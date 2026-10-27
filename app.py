import os
import sys
import json
import re
import math
import time
import html
import base64
import subprocess
import urllib.parse
import lancedb
import streamlit as st
from sentence_transformers import SentenceTransformer
from groq import Groq

# 1. Modular Imports from styles and core package
from styles import CUSTOM_CSS, inject_sidebar_backdrop
from core import (
    decode_preeti_text,
    extract_query_years,
    clean_query_for_search,
    build_document_year_map,
    expand_query_crosslingual,
    hybrid_search,
    call_groq_with_retry,
    extract_cited_sources,
    build_rag_prompt,
    run_ingestion,
    check_filesystem_out_of_sync,
    delete_document,
    get_file_metadata,
    categorize_file,
    MODELS_TO_TRY
)

# 2. Page Configuration
st.set_page_config(
    page_title="Best Finance Regulatory Intelligence",
    page_icon="https://bestfinance.com.np/image/catalog/logo/favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject Institutional Theme Stylesheet & Sidebar Backdrop Controller
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
inject_sidebar_backdrop()

@st.cache_data
def get_brand_logo_b64():
    p = os.path.join(os.path.dirname(__file__), "best_finance_logo.png")
    if os.path.exists(p):
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

brand_logo_b64 = get_brand_logo_b64()

# 3. Read Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.strip().split("=", 1)[1].strip()

if not GROQ_API_KEY:
    GROQ_API_KEY = ""

MODEL_NAME = MODELS_TO_TRY[0]

# Session State Initializations
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = GROQ_API_KEY
if "translation_cache" not in st.session_state:
    st.session_state.translation_cache = {}
if "model_usage" not in st.session_state:
    st.session_state.model_usage = {}
if "model_status" not in st.session_state:
    st.session_state.model_status = {}

# 4. Cached ML Resources
@st.cache_resource(show_spinner=False)
def load_models():
    embed = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    groq_c = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    return embed, groq_c

embedding_model, groq_client = load_models()

def get_live_table():
    db = lancedb.connect("./lancedb_data")
    return db.open_table("bank_documents")

try:
    table = get_live_table()
except Exception:
    table = None

def open_pdf_at_page(pdf_name: str, page: int):
    """Opens the local PDF on Windows directly scrolled to the specified page in Chrome or Edge."""
    pdf_path = os.path.join("File_System", pdf_name)
    if not os.path.exists(pdf_path):
        pdf_path = pdf_name
    if not os.path.exists(pdf_path):
        st.warning(f"File '{pdf_name}' not found on disk.")
        return

    abs_path = os.path.abspath(pdf_path).replace("\\", "/")
    target_url = f"file:///{abs_path}#page={page}"

    browsers = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    for b_path in browsers:
        if os.path.exists(b_path):
            try:
                subprocess.Popen([b_path, target_url])
                st.toast(f"Opening {pdf_name} at Page {page}...")
                return
            except Exception:
                continue

    try:
        os.startfile(os.path.abspath(pdf_path))
    except Exception as e:
        st.error(f"Error opening document: {e}")

def render_verified_sources(cited_sources, other_sources=None, key_prefix="src", target_years=None, target_doc=None):
    """Renders the verified ground truth sources with 1-click PDF page launcher and high-contrast text viewer."""
    if not cited_sources and not other_sources:
        return

    if cited_sources:
        for idx, c in enumerate(cited_sources):
            if isinstance(c, dict):
                src_name = c['source']
                pg_num = c['page']
                snippet_text = c.get('text', '').strip()
            else:
                src_name = str(c).replace("**", "")
                pg_num = 1
                snippet_text = ""

            safe_filename = urllib.parse.quote(src_name)
            
            # Lovable-style clean source card with minimal monochrome outline icon
            col_info, col_btn = st.columns([3.6, 1.2])
            with col_info:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; margin-top: 4px;">
                    <div style="background: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 8px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width: 18px; height: 18px;">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                            <line x1="10" y1="9" x2="8" y2="9"></line>
                        </svg>
                    </div>
                    <div>
                        <div style="font-weight: 600; color: #0F172A; font-size: 0.90rem;">{src_name} · Page {pg_num}</div>
                        <div style="color: #64748B; font-size: 0.78rem;">Verified official regulatory source document</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                st.link_button(
                    f"Open page {pg_num} ↗", 
                    f"/app/static/{safe_filename}#page={pg_num}",
                    use_container_width=True
                )

            if snippet_text:
                with st.expander("View extracted text"):
                    escaped_text = html.escape(snippet_text)
                    st.markdown(
                        f'<div class="extracted-text-box">{escaped_text}</div>',
                        unsafe_allow_html=True
                    )

    # Render all other retrieved candidate reference pages
    if other_sources:
        cited_keys = {(c['source'], c['page']) for c in cited_sources if isinstance(c, dict)}
        remaining = [c for c in other_sources if (c['source'], c['page']) not in cited_keys]
        if remaining:
            def other_sort_key(c):
                src = c['source']
                ym = re.search(r'(20[78][0-9]|20[12][0-9])', src)
                yr = int(ym.group(1)) if ym else 0
                target_match = 0
                if target_doc:
                    if isinstance(target_doc, (list, set, tuple)) and src in target_doc:
                        target_match = 0
                    elif isinstance(target_doc, str) and src == target_doc:
                        target_match = 0
                elif target_years and yr in target_years:
                    target_match = 0
                else:
                    target_match = 1
                return (target_match, -yr if not target_years else 0, c.get('page', 0))

            remaining.sort(key=other_sort_key)

            with st.expander(f"Other reference pages ({len(remaining)})"):
                for idx, c in enumerate(remaining):
                    src_name = c['source']
                    pg_num = c['page']
                    snippet_text = c.get('text', '').strip()
                    safe_filename = urllib.parse.quote(src_name)

                    col_info, col_btn = st.columns([3.6, 1.2])
                    with col_info:
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width: 15px; height: 15px; flex-shrink: 0;">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                                <line x1="16" y1="13" x2="8" y2="13"></line>
                                <line x1="16" y1="17" x2="8" y2="17"></line>
                            </svg>
                            <span style="font-weight: 600; color: #0F172A; font-size: 0.88rem;">{src_name}</span>
                            <span style="color: #64748B; font-size: 0.82rem;">· Page {pg_num}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_btn:
                        st.link_button(
                            f"Open page {pg_num} ↗", 
                            f"/app/static/{safe_filename}#page={pg_num}",
                            use_container_width=True
                        )

                    if snippet_text:
                        with st.expander("View extracted text"):
                            escaped_text = html.escape(snippet_text)
                            st.markdown(
                                f'<div class="extracted-text-box">{escaped_text}</div>',
                                unsafe_allow_html=True
                            )

# 5. Live Repository State (Fast cached source metadata without heavy vector loading)
@st.cache_data(ttl=60, show_spinner=False)
def get_cached_sources():
    try:
        t = get_live_table()
        df_src = t.search().select(["source"]).to_pandas()
        return df_src["source"].value_counts().to_dict()
    except Exception:
        return {}

sources_summary = get_cached_sources()
doc_options = ["All Documents"] + list(sources_summary.keys())
all_disk_files = [f for f in os.listdir("File_System") if f.lower().endswith((".pdf", ".docx", ".txt"))] if os.path.exists("File_System") else []


# ==========================================
# PAGE 1: REGULATORY ASSISTANT (/)
# ==========================================
def render_assistant_page():
    # Top Unified Institutional Navbar (Logo Left, Title Centered, Badge Right)
    st.markdown(f"""
    <div class="institutional-navbar">
        <div class="navbar-left">
            <a href="https://bestfinance.com.np" target="_blank" class="navbar-brand-link">
                <img src="data:image/png;base64,{brand_logo_b64}" 
                     alt="Best Finance Company Ltd." 
                     class="navbar-brand-logo">
            </a>
        </div>
        <div class="navbar-center">
            <div class="navbar-title-container">
                <div class="navbar-title-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" style="width: 20px; height: 20px;">
                        <path fill-rule="evenodd" d="M12.516 2.17a.75.75 0 0 0-1.032 0 11.209 11.209 0 0 1-7.877 3.08.75.75 0 0 0-.722.515A12.74 12.74 0 0 0 2.25 9.75c0 5.942 4.064 10.933 9.563 12.348a.749.749 0 0 0 .374 0c5.499-1.415 9.563-6.406 9.563-12.348 0-1.39-.223-2.73-.635-3.985a.75.75 0 0 0-.722-.516l-.143.001c-2.996 0-5.717-1.17-7.734-3.08Zm3.094 8.016a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z" clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="navbar-title-content">
                    <h1 class="navbar-title-heading">Regulatory & Directive Assistant</h1>
                    </div>
            </div>
        </div>
        <div class="navbar-right">
            <div class="navbar-status-badge">
                <span class="status-pulse-dot"></span>
                <span class="status-badge-text">Verified sources only</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar Filters & Chat Controls (Positioned Below Best Finance Logo)
    with st.sidebar:
        # Page Navigation Links (Directly Below Logo!)
        st.page_link(assistant_page, label="Regulatory Assistant", icon=":material/chat:")
        st.page_link(admin_page, label="Document Management", icon=":material/folder:")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size: 0.76rem; font-weight: 800; letter-spacing: 0.08em; color: #6EE7B7; text-transform: uppercase; margin-bottom: 10px; display: flex; align-items: center; gap: 7px;">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="#6EE7B7" style="width: 14px; height: 14px;">
                <path fill-rule="evenodd" d="M2.628 1.601C5.028 1.206 7.49 1 10 1s4.973.206 7.372.601a.75.75 0 0 1 .628.74v2.288a2.25 2.25 0 0 1-.659 1.59l-4.682 4.683a2.25 2.25 0 0 0-.659 1.59v3.037c0 .684-.31 1.33-.844 1.757l-1.937 1.55A.75.75 0 0 1 8 18.25v-5.757a2.25 2.25 0 0 0-.659-1.591L2.659 6.22A2.25 2.25 0 0 1 2 4.629V2.34a.75.75 0 0 1 .628-.74Z" clip-rule="evenodd" />
            </svg>
            Scope & Filter
        </div>
        """, unsafe_allow_html=True)

        CATEGORY_OPTIONS = {
            "all": "All categories (Auto)",
            "unified": "Unified Directives (एकीकृत निर्देशन)",
            "payment": "Payment Directives (भुक्तानी निर्देशन)",
            "report": "Supervision Reports (सुपरीवेक्षण प्रतिवेदन)",
            "other": "Circulars & Other (अन्य परिपत्र)"
        }

        selected_cat = st.selectbox(
            "Category scope",
            options=list(CATEGORY_OPTIONS.keys()),
            format_func=lambda k: CATEGORY_OPTIONS[k],
            index=0,
            label_visibility="visible"
        )

        all_available_docs = list(sources_summary.keys())
        if selected_cat == "all":
            category_docs = all_available_docs
            doc_dropdown_options = ["All documents (Global)"] + all_available_docs
        else:
            category_docs = [f for f in all_available_docs if categorize_file(f) == selected_cat]
            if category_docs:
                doc_dropdown_options = [f"All Documents in this Category ({len(category_docs)})"] + category_docs
            else:
                doc_dropdown_options = ["No documents found in this category"]

        selected_doc_choice = st.selectbox(
            "Document",
            options=doc_dropdown_options,
            index=0,
            label_visibility="visible"
        )

        st.caption("AI auto-detects the right directive and fiscal year from your question.")

        if selected_cat == "all" and selected_doc_choice.startswith("All documents"):
            selected_doc = "All Documents"
        elif selected_doc_choice.startswith("All Documents in this Category"):
            selected_doc = category_docs
        elif selected_doc_choice.startswith("No documents"):
            selected_doc = "All Documents"
        else:
            selected_doc = selected_doc_choice

        st.divider()

        # Chat Actions
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "नमस्ते! म बेष्ट फाइनान्स कम्पनी लि. (Best Finance Company Ltd.) को आधिकारिक नियामक सहायक हुँ। तपाईं नेपाल राष्ट्र बैंकका परिपत्र, निर्देशन, कारोबार सीमा वा शुल्कबारे कुनै पनि प्रश्न सोध्न सक्नुहुन्छ।",
                    "sources": [],
                    "latency": None
                }
            ]
            st.rerun()

    # Chat History in Session State
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "नमस्ते! म बेष्ट फाइनान्स कम्पनी लि. (Best Finance Company Ltd.) को आधिकारिक नियामक सहायक हुँ। तपाईं नेपाल राष्ट्र बैंकका परिपत्र, निर्देशन, कारोबार सीमा वा शुल्कबारे कुनै पनि प्रश्न सोध्न सक्नुहुन्छ।",
                "sources": [],
                "other_sources": [],
                "target_years": [],
                "target_doc": None,
                "latency": None
            }
        ]

    # Display Previous Messages (Lovable Layout: Clean Pill on Right, Shield Avatar on Left)
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin: 12px 0 16px 0;">
                <div style="background-color: #083820; color: #FFFFFF; border-radius: 24px; padding: 10px 22px; font-weight: 500; font-size: 0.94rem; max-width: 80%; box-shadow: 0 2px 8px rgba(8, 56, 32, 0.16);">
                    {msg["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            col_av, col_body = st.columns([0.045, 0.955])
            with col_av:
                st.markdown("""
                <div style="width: 34px; height: 34px; border-radius: 50%; background: #064E3B; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(6, 78, 59, 0.25); margin-top: 4px;">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" style="width: 18px; height: 18px;">
                        <path fill-rule="evenodd" d="M12.516 2.17a.75.75 0 0 0-1.032 0 11.209 11.209 0 0 1-7.877 3.08.75.75 0 0 0-.722.515A12.74 12.74 0 0 0 2.25 9.75c0 5.942 4.064 10.933 9.563 12.348a.749.749 0 0 0 .374 0c5.499-1.415 9.563-6.406 9.563-12.348 0-1.39-.223-2.73-.635-3.985a.75.75 0 0 0-.722-.516l-.143.001c-2.996 0-5.717-1.17-7.734-3.08Zm3.094 8.016a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z" clip-rule="evenodd" />
                    </svg>
                </div>
                """, unsafe_allow_html=True)
            with col_body:
                st.markdown(msg["content"])
                if msg.get("latency"):
                    st.caption(f"⚡ {msg['latency']}")
                if msg.get("sources") or msg.get("other_sources"):
                    render_verified_sources(
                        msg.get("sources", []), 
                        other_sources=msg.get("other_sources", []), 
                        key_prefix=f"hist_{i}",
                        target_years=set(msg.get("target_years", [])) if msg.get("target_years") else None,
                        target_doc=msg.get("target_doc")
                    )

    # Input Box ALWAYS AT BOTTOM OF SCREEN
    active_query = st.chat_input("Ask a question about NRB directives, rules, or limits (उदा: स्वःघोषणासम्बन्धी व्यवस्था)...")

    if active_query:
        start_time = time.time()
        st.session_state.messages.append({"role": "user", "content": active_query})
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin: 12px 0 16px 0;">
            <div style="background-color: #083820; color: #FFFFFF; border-radius: 24px; padding: 10px 22px; font-weight: 500; font-size: 0.94rem; max-width: 80%; box-shadow: 0 2px 8px rgba(8, 56, 32, 0.16);">
                {active_query}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Automatic Query Year Routing & Document Selection
        live_table = table if table is not None else get_live_table()
        with st.spinner("🔍 Retrieving regulatory clauses & analyzing directives..."):
            doc_year_map = build_document_year_map(live_table)
            available_years = set.union(*doc_year_map.values()) if doc_year_map else set()
            matched_years = extract_query_years(active_query, available_years)

            effective_doc = None if selected_doc in ["Auto (AI-Detected Document)", "All Documents"] else selected_doc
            routed_badge = None

            if effective_doc is None:
                if len(matched_years) == 1:
                    target_yr = list(matched_years)[0]
                    matching_docs = [d for d, yrs in doc_year_map.items() if target_yr in yrs]
                    if matching_docs:
                        effective_doc = matching_docs if len(matching_docs) > 1 else matching_docs[0]
                        doc_names_str = ", ".join(f"`{d}`" for d in matching_docs)
                        routed_badge = f"🎯 Auto-routed to {target_yr} Directives / Reports ({doc_names_str})"
                elif len(matched_years) > 1:
                    yrs_str = ", ".join(str(y) for y in sorted(matched_years))
                    routed_badge = f"📊 Comparative Multi-Year Query (analyzing across years: {yrs_str})"
            elif isinstance(effective_doc, (list, set, tuple)):
                if len(matched_years) == 1:
                    target_yr = list(matched_years)[0]
                    matching_in_scope = [d for d in effective_doc if target_yr in doc_year_map.get(d, set())]
                    if matching_in_scope:
                        effective_doc = matching_in_scope if len(matching_in_scope) > 1 else matching_in_scope[0]
                        doc_names_str = ", ".join(f"`{d}`" for d in (matching_in_scope if isinstance(matching_in_scope, list) else [matching_in_scope]))
                        routed_badge = f"🎯 Auto-routed within category to {target_yr} ({doc_names_str})"

            search_query = clean_query_for_search(active_query, matched_years) if effective_doc else active_query
            if not search_query.strip():
                search_query = active_query

            # Cross-Lingual Dual-Pass Hybrid Retrieval
            translated_terms = expand_query_crosslingual(search_query, groq_client, cache=st.session_state.translation_cache)
            results = hybrid_search(search_query, live_table, embedding_model, translated_terms=translated_terms, selected_doc=effective_doc, top_k=8)

            # For comparative multi-year queries, interleave results across matched documents
            if len(matched_years) > 1:
                target_docs = set()
                for yr in matched_years:
                    for d, yrs in doc_year_map.items():
                        if yr in yrs:
                            target_docs.add(d)
                if target_docs:
                    by_doc = {d: [] for d in target_docs}
                    for item in results:
                        if item['source'] in by_doc:
                            by_doc[item['source']].append(item)
                    interleaved = []
                    for i in range(3):
                        for d in sorted(by_doc.keys()):
                            if i < len(by_doc[d]):
                                interleaved.append(by_doc[d][i])
                    if interleaved:
                        results = interleaved

            # Parent Document Context Windowing with Preeti decoding
            seen_pages = set()
            full_page_context = []
            full_page_map = {}
            total_chars = 0

            for item in results:
                sp = (item['source'], item['page'])
                if sp not in seen_pages:
                    seen_pages.add(sp)
                    try:
                        page_records = live_table.search().where(f"source = '{item['source']}' AND page = {item['page']}").select(["text"]).to_pandas()
                        full_page_text = "\n".join(page_records['text'].tolist())
                    except Exception:
                        full_page_text = item['text']

                    full_page_text = decode_preeti_text(full_page_text)
                    full_page_map[sp] = full_page_text

                    full_page_context.append(f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}]:\n{full_page_text}\n")
                    total_chars += len(full_page_text)
                    if len(seen_pages) >= 5 or total_chars > 12000:
                        break

            context_text = "\n".join(full_page_context)
            system_prompt = build_rag_prompt(context_text)

        # Stream Groq Response to UI (Lovable Shield Avatar Layout)
        col_av, col_body = st.columns([0.045, 0.955])
        with col_av:
            st.markdown("""
            <div style="width: 34px; height: 34px; border-radius: 50%; background: #064E3B; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(6, 78, 59, 0.25); margin-top: 4px;">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" style="width: 18px; height: 18px;">
                    <path fill-rule="evenodd" d="M12.516 2.17a.75.75 0 0 0-1.032 0 11.209 11.209 0 0 1-7.877 3.08.75.75 0 0 0-.722.515A12.74 12.74 0 0 0 2.25 9.75c0 5.942 4.064 10.933 9.563 12.348a.749.749 0 0 0 .374 0c5.499-1.415 9.563-6.406 9.563-12.348 0-1.39-.223-2.73-.635-3.985a.75.75 0 0 0-.722-.516l-.143.001c-2.996 0-5.717-1.17-7.734-3.08Zm3.094 8.016a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z" clip-rule="evenodd" />
                </svg>
            </div>
            """, unsafe_allow_html=True)
        with col_body:
            response_placeholder = st.empty()
            full_response = ""
            active_model_used = None

            try:
                stream, active_model_used = call_groq_with_retry(
                    groq_client,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": active_query}
                    ],
                    temperature=0.1,
                    max_tokens=2500,
                    stream=True
                )

                for chunk in stream:
                    choice = chunk.choices[0]
                    token = choice.delta.content or ""
                    if token:
                        full_response += token
                        response_placeholder.markdown(full_response + "▌")
                    elif not full_response:
                        response_placeholder.markdown("🧠 *Analyzing regulatory directives...* ▌")

                if full_response.strip():
                    response_placeholder.markdown(full_response)
                else:
                    full_response = "उपलब्ध कागजातमा यो जानकारी फेला परेन / Information not found in the documents."
                    response_placeholder.markdown(full_response)

                # Track tokens used in session
                approx_tokens = (len(system_prompt) + len(active_query) + len(full_response)) // 4
                if active_model_used:
                    st.session_state.model_usage[active_model_used] = st.session_state.model_usage.get(active_model_used, 0) + approx_tokens

                elapsed_sec = time.time() - start_time
                latency_str = f"Answered in {elapsed_sec:.2f}s via {active_model_used} on Groq LPU"
                st.caption(f"⚡ {latency_str}")

                # Extract and display verified sources cited strictly based on answer and target
                cited_sources = extract_cited_sources(
                    full_response, 
                    results, 
                    full_page_map, 
                    live_table=live_table,
                    target_years=matched_years,
                    target_doc=effective_doc
                )

                # Collect other retrieved candidates so all citations & related pages are accessible
                other_candidates = []
                seen_cand = set()
                for r in results:
                    k = (r['source'], r['page'])
                    if k not in seen_cand:
                        seen_cand.add(k)
                        other_candidates.append({
                            'source': r['source'],
                            'page': r['page'],
                            'text': full_page_map.get(k, r.get('text', ''))
                        })

                render_verified_sources(
                    cited_sources, 
                    other_sources=other_candidates, 
                    key_prefix=f"curr_{len(st.session_state.messages)}",
                    target_years=matched_years,
                    target_doc=effective_doc
                )

                # Save to Session State
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "sources": cited_sources,
                    "other_sources": other_candidates,
                    "target_years": list(matched_years) if matched_years else [],
                    "target_doc": effective_doc if isinstance(effective_doc, (str, list)) else None,
                    "latency": latency_str
                })

            except Exception as e:
                st.error(f"⚠️ Error querying Groq: {e}")

    # Bottom spacer so the final message and citations are never obscured by the docked input bar
    st.markdown("<div style='height: 110px;'></div>", unsafe_allow_html=True)


# ==========================================
# PAGE 2: DOCUMENT MANAGEMENT & ADMIN (/admin)
# ==========================================
def render_admin_page():
    # 0. Automatic Full Database Synchronization on Any File System Changes
    if check_filesystem_out_of_sync():
        with st.spinner("🔄 File system changes detected. Automatically synchronizing database..."):
            res = run_ingestion()
            if res.returncode == 0:
                st.toast("✅ Database automatically synchronized with files on disk!")
                time.sleep(0.6)
                st.rerun()

    @st.cache_data(ttl=60, show_spinner=False)
    def load_admin_data():
        try:
            t = get_live_table()
            return t.to_pandas()
        except Exception:
            return None

    df = load_admin_data()
    total_docs = len(all_disk_files)
    total_chunks = len(df) if df is not None else 0

    # Top Unified Institutional Navbar (Responsive: Logo Left, Admin Header Centered, Status Right)
    st.markdown(f"""
    <div class="institutional-navbar">
        <div class="navbar-left">
            <a href="https://bestfinance.com.np" target="_blank" class="navbar-brand-link">
                <img src="data:image/png;base64,{brand_logo_b64}" 
                     alt="Best Finance Company Ltd." 
                     class="navbar-brand-logo">
            </a>
        </div>
        <div class="navbar-center">
            <div class="navbar-title-container">
                <div class="navbar-title-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" style="width: 20px; height: 20px;">
                        <path d="M19.5 21a3 3 0 0 0 3-3v-4.5a3 3 0 0 0-3-3h-15a3 3 0 0 0-3 3V18a3 3 0 0 0 3 3h15ZM1.5 10.146V6a3 3 0 0 1 3-3h5.379a2.25 2.25 0 0 1 1.59.659l2.122 2.121c.14.141.331.22.53.22H19.5a3 3 0 0 1 3 3v1.146A4.483 4.483 0 0 0 19.5 9h-15a4.483 4.483 0 0 0-3 1.146Z" />
                    </svg>
                </div>
                <div class="navbar-title-content">
                    <h1 class="navbar-title-heading">Document Management & Admin</h1>
                    <p class="navbar-title-sub">Upload, organize, inspect, and synchronize institutional regulatory documents</p>
                </div>
            </div>
        </div>
        <div class="navbar-right">
            <div class="navbar-status-badge">
                <span class="status-pulse-dot"></span>
                <span class="status-badge-text">Auto-Sync Active</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar Status (Positioned Below Best Finance Logo)
    with st.sidebar:
        st.page_link(assistant_page, label="Regulatory Assistant", icon=":material/chat:")
        st.page_link(admin_page, label="Document Management", icon=":material/folder:")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.88rem; font-weight: 700; color: #FFFFFF; margin-top: 10px;'>Database Synchronization</div>", unsafe_allow_html=True)
        st.markdown("<div style='color: #6EE7B7; font-size: 0.80rem; font-weight: 600; margin-top: 4px;'>● Auto-Sync Active</div>", unsafe_allow_html=True)
        st.caption("The database automatically stays synchronized whenever documents are added, modified, or deleted in `File_System/`.")

    st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

    # 1. Summary Metrics
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1.5px solid #D1FAE5; border-radius: 10px; padding: 14px 18px; box-shadow: 0 1px 3px rgba(0, 169, 79, 0.04);">
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.88rem; font-weight: 600; color: #475569; margin-bottom: 4px;">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 20px; height: 20px; color: #00A94F; display: inline-block; vertical-align: -3px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
        </svg>
        <span>Total Documents</span>
            </div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #008C42;">
                {total_docs} Files
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_m2:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1.5px solid #D1FAE5; border-radius: 10px; padding: 14px 18px; box-shadow: 0 1px 3px rgba(0, 169, 79, 0.04);">
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.88rem; font-weight: 600; color: #475569; margin-bottom: 4px;">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor" style="width: 20px; height: 20px; color: #00A94F; display: inline-block; vertical-align: -3px;">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3" />
                </svg>
                <span>Indexed Chunks</span>
            </div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #008C42;">
                {total_chunks:,}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

    # 2. Upload and Ingestion Container
    with st.expander("🗎 Add New Documents (Upload & Index)", expanded=True):
        st.markdown("<p style='font-size: 0.9rem; color: #475569; margin-bottom: 8px;'>Drag and drop institutional PDF, DOCX, or TXT documents. New documents are automatically ingested and indexed into the database upon upload.</p>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Select files",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            key="admin_doc_uploader",
            label_visibility="collapsed"
        )
        if uploaded_files:
            new_saved = []
            for up_file in uploaded_files:
                save_path = os.path.join("File_System", up_file.name)
                if not os.path.exists(save_path):
                    with open(save_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    new_saved.append(up_file.name)
            if new_saved:
                with st.spinner(f"⚡ Ingesting and indexing {len(new_saved)} new document(s) into database..."):
                    res = run_ingestion()
                    if res.returncode == 0:
                        st.toast(f"✅ Successfully saved and indexed {len(new_saved)} document(s)!")
                        time.sleep(0.6)
                        st.rerun()
                    else:
                        st.error(f"Error during ingestion: {res.stderr[:300]}")

        if st.button("⚡ Ingest & Index Documents Now", use_container_width=True, type="primary"):
            with st.spinner("Extracting text, resolving Preeti fonts, generating embeddings, and updating LanceDB..."):
                res = run_ingestion()
                if res.returncode == 0:
                    st.success("✅ Successfully indexed all documents into database!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Error during ingestion: {res.stderr[:300]}")

    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

    # 3. Interactive Chunk Inspector
    

    # 4. Organized Document Catalog
    st.subheader("📑 Document Catalog (Organized by Category)")

    admin_filter = st.text_input(
        "🔍 Filter documents:",
        placeholder="Filter by filename, year (e.g. 2082), or keyword...",
        key="admin_search_input"
    ).strip().lower()

    filter_words = admin_filter.split() if admin_filter else []

    # Build metadata for all files in File_System
    all_metadata = [get_file_metadata(f, sources_summary, df=df) for f in all_disk_files]

    # Category definitions with human-friendly titles
    CATEGORY_SECTIONS = [
        {
            "id": "unified",
            "title": "🏦 Unified Directives (बैंक तथा वित्तीय संस्था सम्बन्धी एकीकृत निर्देशन)",
            "description": "Comprehensive prudential regulations, capital adequacy, credit classification, and governance directives."
        },
        {
            "id": "payment",
            "title": "💳 Payment System Directives (भुक्तानी प्रणाली सम्बन्धी एकीकृत निर्देशन)",
            "description": "Digital payments, wallet limits, interchange fees, settlement, and PSP/PSO regulations."
        },
        {
            "id": "report",
            "title": "📊 Annual Supervision Reports (वार्षिक सुपरीवेक्षण तथा निरीक्षण प्रतिवेदन)",
            "description": "Official annual banking supervision reports, balance sheets, and sector reviews."
        },
        {
            "id": "other",
            "title": "📑 Circulars & Other Documents (अन्य परिपत्र तथा सूचनाहरू)",
            "description": "General circulars, press releases, AML/CFT guidelines, and custom uploaded manuals."
        }
    ]

    live_table_for_delete = get_live_table()

    def doc_matches_filter(doc, words, cat_title=""):
        if not words:
            return True
        name_clean = doc["filename"].replace("_", " ").replace("-", " ")
        searchable = f"{doc['filename']} {name_clean} {doc['years_str']} {doc['category']} {cat_title}".lower()
        return all(w in searchable for w in words)

    total_matched_docs = 0
    if filter_words:
        for m in all_metadata:
            c_title = next((c["title"] for c in CATEGORY_SECTIONS if c["id"] == m["category"]), "")
            if doc_matches_filter(m, filter_words, c_title):
                total_matched_docs += 1
        if total_matched_docs == 0:
            st.info(f"🔍 No documents found matching '{admin_filter}'. Try searching by year (e.g. 2082), category, or keyword.")
        else:
            st.caption(f"Found **{total_matched_docs}** matching document(s) for '**{admin_filter}**':")

    for cat in CATEGORY_SECTIONS:
        cat_docs = [m for m in all_metadata if m["category"] == cat["id"]]
        if filter_words:
            cat_docs = [m for m in cat_docs if doc_matches_filter(m, filter_words, cat["title"])]

        cat_docs.sort(key=lambda m: (m["years_str"], m["filename"]), reverse=True)

        is_expanded = bool(filter_words and len(cat_docs) > 0)
        exp_label = f"{cat['title']} — {len(cat_docs)} Document(s)"
        with st.expander(exp_label, expanded=is_expanded):
            st.caption(cat["description"])
            
            if not cat_docs:
                st.info("No documents currently in this category.")
                continue

            # Table Header
            col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([3.6, 1.2, 1.3, 1.5, 1.0])
            with col_h1: st.caption("**Document Name**")
            with col_h2: st.caption("**File Size**")
            with col_h3: st.caption("**Chunks**")
            with col_h4: st.caption("**View PDF**")
            with col_h5: st.caption("**Action**")

            for doc in cat_docs:
                fname = doc["filename"]
                safe_name = urllib.parse.quote(fname)
                c1, c2, c3, c4, c5 = st.columns([3.6, 1.2, 1.3, 1.5, 1.0])
                
                with c1:
                    st.markdown(f"**{fname}**")
                with c2:
                    st.markdown(f"{doc['size_mb']:.2f} MB")
                with c3:
                    if doc['chunk_count'] > 0:
                        st.markdown(f"{doc['chunk_count']:,} chunks")
                    else:
                        st.markdown("*Not indexed*")
                with c4:
                    st.link_button("View PDF ↗", f"/app/static/{safe_name}", use_container_width=True)
                with c5:
                    if st.button("Delete", key=f"del_btn_{fname}", help=f"Delete '{fname}' from system and database", type="secondary"):
                        success = delete_document(fname, live_table=live_table_for_delete)
                        if success:
                            st.toast(f"Removed '{fname}' from system and database!")
                            time.sleep(0.6)
                            st.rerun()


# ==========================================
# 6. STREAMLIT MULTI-PAGE NAVIGATION ROUTER
# ==========================================
assistant_page = st.Page(
    render_assistant_page,
    title="Regulatory Assistant",
    icon=":material/chat:",
    default=True
)

admin_page = st.Page(
    render_admin_page,
    title="Document Management",
    icon=":material/folder:",
    url_path="admin"
)

pg = st.navigation([assistant_page, admin_page], position="hidden")
pg.run()

