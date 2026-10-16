import os
import sys
import json
import re
import math
import time
import subprocess
import urllib.parse
import lancedb
import streamlit as st
from sentence_transformers import SentenceTransformer
from groq import Groq

# 1. Modular Imports from styles and core package
from styles import CUSTOM_CSS
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
    delete_document,
    extract_sample_text_from_file,
    categorize_file,
    get_file_metadata,
    MODELS_TO_TRY
)

# 2. Page Configuration
st.set_page_config(
    page_title="NRB Regulatory Intelligence (RAG)",
    page_icon="🏦",
    layout="wide"
)

# Inject Institutional Theme Stylesheet
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

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
    """Renders the verified ground truth sources with 1-click PDF page launcher and text viewer."""
    if not cited_sources and not other_sources:
        return

    if cited_sources:
        st.markdown("##### 🔍 Verified Source Document(s):")
        for idx, c in enumerate(cited_sources):
            if isinstance(c, dict):
                src_name = c['source']
                pg_num = c['page']
                snippet_text = c.get('text', '').strip()
            else:
                src_name = str(c).replace("**", "")
                pg_num = 1
                snippet_text = ""

            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"📄 **{src_name}** — **Page {pg_num}**")
            with col_btn:
                safe_filename = urllib.parse.quote(src_name)
                st.link_button(
                    f"📖 Open Page {pg_num}", 
                    f"/app/static/{safe_filename}#page={pg_num}"
                )

            if snippet_text:
                with st.expander(f"👁️ View Extracted Text from {src_name} (Page {pg_num})"):
                    st.text_area(
                        "Extracted Context",
                        value=snippet_text,
                        height=160,
                        disabled=True,
                        key=f"{key_prefix}_txt_{idx}_{src_name}_{pg_num}",
                        label_visibility="collapsed"
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

            with st.expander(f"📚 Other Retrieved Reference Pages ({len(remaining)})"):
                for idx, c in enumerate(remaining):
                    src_name = c['source']
                    pg_num = c['page']
                    snippet_text = c.get('text', '').strip()

                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"📄 **{src_name}** — **Page {pg_num}**")
                    with col_btn:
                        safe_filename = urllib.parse.quote(src_name)
                        st.link_button(
                            f"📖 Open Page {pg_num}", 
                            f"/app/static/{safe_filename}#page={pg_num}"
                        )

                    if snippet_text:
                        with st.expander(f"👁️ View Text from {src_name} (Page {pg_num})"):
                            st.text_area(
                                "Reference Context",
                                value=snippet_text,
                                height=130,
                                disabled=True,
                                key=f"{key_prefix}_oth_txt_{idx}_{src_name}_{pg_num}",
                                label_visibility="collapsed"
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

# 6. Clean Executive Sidebar
with st.sidebar:
    st.markdown("### 🏦Institutional Regulatory Intelligence Engine")
    st.divider()

    # Document Scope Filter
    st.subheader(" Filter Search")
    selected_doc = st.selectbox(
        "Search Scope:",
        options=doc_options,
        index=0,
        help="Leave on 'All Documents' so AI auto-selects the right directive and fiscal year based on your question."
    )
    st.caption("💡 *'All Documents' automatically selects the right directive and year based on your question.*")
    st.divider()

    # Chat Actions
    st.subheader("🧹 Actions")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "नमस्ते! म यस संस्था सम्बन्धी कागजातहरूको आधिकारिक सहायक हुँ। तपाईं परिपत्र, निर्देशन, कारोबार सीमा वा शुल्कबारे कुनै पनि प्रश्न सोध्न सक्नुहुन्छ।",
                "sources": [],
                "latency": None
            }
        ]
        st.rerun()

# 7. Top-Level Workspace Navigation (ChatGPT & Gemini Style View Switcher - Sticky Navbar)
active_tab = st.segmented_control(
    "Workspace View",
    options=["💬 Regulatory Assistant", "📁 Document Management & Admin"],
    default="💬 Regulatory Assistant",
    key="main_workspace_view",
    label_visibility="collapsed"
)
if not active_tab:
    active_tab = "💬 Regulatory Assistant"

# ==========================================
# VIEW 1: CLEAN REGULATORY CHATBOT
# ==========================================
if active_tab == "💬 Regulatory Assistant":
    # Clean Header
    st.markdown("""
    <div style="margin-bottom: 1.1rem; padding-bottom: 0.5rem;">
        <h2 style="margin: 0; font-size: 1.45rem; font-weight: 700; color: #0A2540; letter-spacing: -0.01em;">
            💬 Document Assistant
        </h2>
    </div>
    """, unsafe_allow_html=True)

    # Chat History in Session State
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "नमस्ते! म यस संस्था सम्बन्धी कागजातहरूको आधिकारिक सहायक हुँ। तपाईं परिपत्र, निर्देशन, कारोबार सीमा वा शुल्कबारे कुनै पनि प्रश्न सोध्न सक्नुहुन्छ।",
                "sources": [],
                "other_sources": [],
                "target_years": [],
                "target_doc": None,
                "latency": None
            }
        ]

    # Display Previous Messages
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
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
        with st.chat_message("user"):
            st.markdown(active_query)

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

        # Stream Groq Response to UI
        with st.chat_message("assistant"):
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
                    max_tokens=1100,
                    stream=True
                )

                for chunk in stream:
                    token = chunk.choices[0].delta.content or ""
                    full_response += token
                    response_placeholder.markdown(full_response + "▌")
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
# VIEW 2: ORGANIZED DOCUMENT MANAGEMENT & ADMIN
# ==========================================
else:
    st.markdown("""
    <div style="margin-bottom: 1.2rem; padding-bottom: 0.8rem; border-bottom: 1px solid #E2E8F0;">
        <h2 style="margin: 0; font-size: 1.6rem; font-weight: 700; color: #0A2540; letter-spacing: -0.01em;">
            📁 Document Management & Admin Panel
        </h2>
        <p style="margin: 4px 0 0 0; font-size: 0.92rem; color: #64748B;">
            Organize, upload, inspect, and synchronize regulatory documents with the LanceDB vector store.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Lazy Dataframe Loading (Only in Admin view)
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

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("📚 Total Documents", f"{total_docs} Files")
    with col_m2:
        st.metric("🧩 Indexed Chunks", f"{total_chunks:,}")

    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

    # 2. Upload and Ingestion Container
    with st.expander("📤 Add New Documents (Upload & Index)", expanded=True):
        st.markdown("<p style='font-size: 0.9rem; color: #475569; margin-bottom: 8px;'>Drag and drop institutional PDF, DOCX, or TXT documents. Once uploaded, click <b>Index Documents Now</b> to process Preeti text, chunk, and generate embeddings.</p>", unsafe_allow_html=True)
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
                st.success(f"✅ Successfully saved {len(new_saved)} new file(s) to File_System: {', '.join(new_saved)}")

        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            if st.button("⚡ Ingest & Index Documents Now", use_container_width=True, type="primary"):
                with st.spinner("Extracting text, resolving Preeti fonts, generating embeddings, and updating LanceDB..."):
                    res = run_ingestion()
                    if res.returncode == 0:
                        st.success("✅ Successfully indexed all documents into database!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Error during ingestion: {res.stderr[:300]}")
        with col_act2:
            if st.button("🔄 Full Database Re-Sync", use_container_width=True):
                with st.spinner("Re-syncing files with vector store..."):
                    res = run_ingestion()
                    if res.returncode == 0:
                        st.success("✅ Database synchronized with filesystem!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Error: {res.stderr[:300]}")

    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

    # 3. Interactive Chunk Inspector
    with st.expander("🔍 Interactive Chunk Inspector (Browse Extracted Database Chunks)", expanded=False):
        st.markdown("<p style='font-size: 0.9rem; color: #475569; margin-bottom: 8px;'>Directly view, search, and verify raw chunks stored in the LanceDB vector store for any document.</p>", unsafe_allow_html=True)
        if df is not None and not df.empty:
            doc_list = sorted(list(df["source"].unique()))
            col_sel1, col_sel2 = st.columns([2, 1])
            with col_sel1:
                sel_doc = st.selectbox("Select Document", doc_list, key="chunk_insp_doc")
            
            doc_df = df[df["source"] == sel_doc]
            all_pages = sorted(list(doc_df["page"].unique()))
            page_options = ["All Pages"] + [f"Page {p}" for p in all_pages]
            
            with col_sel2:
                sel_page_str = st.selectbox("Select Page", page_options, key="chunk_insp_page")
            
            chunk_search = st.text_input("Filter chunks by keyword (optional):", key="chunk_insp_search", placeholder="Type keyword to filter chunks...").strip()
            
            filtered_chunks = doc_df
            if sel_page_str != "All Pages":
                page_num = int(sel_page_str.replace("Page ", ""))
                filtered_chunks = filtered_chunks[filtered_chunks["page"] == page_num]
            
            if chunk_search:
                filtered_chunks = filtered_chunks[filtered_chunks["text"].str.contains(chunk_search, case=False, na=False)]
            
            st.caption(f"Found **{len(filtered_chunks)}** chunk(s) for **{sel_doc}** ({sel_page_str}):")
            
            for idx, (_, ch_row) in enumerate(filtered_chunks.head(15).iterrows(), 1):
                clean_t = decode_preeti_text(ch_row['text'])
                with st.expander(f"🧩 Chunk #{idx} — Page {ch_row['page']} ({len(clean_t)} characters)", expanded=(idx == 1)):
                    st.text_area(f"Chunk Content (Page {ch_row['page']})", clean_t, height=130, key=f"chunk_txt_{sel_doc}_{ch_row['page']}_{idx}", disabled=True)
            
            if len(filtered_chunks) > 15:
                st.info(f"Showing first 15 of {len(filtered_chunks)} matching chunks. Select a specific page or filter by keyword above to see others.")
        else:
            st.info("No documents indexed in database yet.")

    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

    # 4. Organized Document Catalog
    st.subheader("📑 Document Catalog (Organized by Category)")
    
    admin_filter = st.text_input(
        "🔍 Filter documents:",
        placeholder="Filter by filename, year (e.g. 2082), or keyword...",
        key="admin_search_input"
    ).strip().lower()

    # Build metadata for all files in File_System
    all_metadata = [get_file_metadata(f, sources_summary, df=df) for f in all_disk_files]

    # Category definitions with human-friendly Nepali & English titles
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

    for cat in CATEGORY_SECTIONS:
        # Filter docs belonging to this category
        cat_docs = [m for m in all_metadata if m["category"] == cat["id"]]
        if admin_filter:
            cat_docs = [m for m in cat_docs if admin_filter in m["filename"].lower() or admin_filter in m["years_str"].lower()]

        # Sort docs by detected year descending, then by filename
        cat_docs.sort(key=lambda m: (m["years_str"], m["filename"]), reverse=True)

        exp_label = f"{cat['title']} — {len(cat_docs)} Document(s)"
        with st.expander(exp_label, expanded=False):
            st.caption(cat["description"])
            
            if not cat_docs:
                st.info("No documents currently in this category.")
                continue

            # Table Header
            col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([3.6, 1.2, 1.3, 1.5, 1.0])
            with col_h1: st.caption("📄 **Document Name**")
            with col_h2: st.caption("💾 **File Size**")
            with col_h3: st.caption("🧩 **Chunks**")
            with col_h4: st.caption("📖 **View PDF**")
            with col_h5: st.caption("⚙️ **Action**")

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
                        st.markdown(f"✅ {doc['chunk_count']:,}")
                    else:
                        st.markdown("⚠️ *Not indexed*")
                with c4:
                    st.link_button("📖 View PDF", f"/app/static/{safe_name}", use_container_width=True)
                with c5:
                    if st.button("🗑️", key=f"del_btn_{fname}", help=f"Delete '{fname}' from system and database", type="secondary"):
                        success = delete_document(fname, live_table=live_table_for_delete)
                        if success:
                            st.toast(f"Removed '{fname}' from system and database!")
                            time.sleep(0.6)
                            st.rerun()
