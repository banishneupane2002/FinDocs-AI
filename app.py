import os
import sys
import json
import re
import math
import time
import unicodedata
import lancedb
import streamlit as st
from sentence_transformers import SentenceTransformer
from groq import Groq

# 1. Page Configuration
st.set_page_config(
    page_title="NRB Regulatory Intelligence (RAG)",
    page_icon="🏦",
    layout="wide"
)

# Read Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.strip().split("=", 1)[1].strip()

if not GROQ_API_KEY:
    GROQ_API_KEY = ""

MODEL_NAME = "qwen/qwen3.8-27b"

# Stop words for hybrid search
STOP_WORDS = {
    'बारेमा', 'भन्नुहोस्', 'भन्नुहोस', 'व्यवस्था', 'सम्बन्धी', 'सम्बन्धमा', 
    'के', 'कस्तो', 'कति', 'कसरी', 'छ', 'पर्छ', 'हुन', 'तथा', 'र', 'वा', 
    'पनि', 'गर्न', 'सकिन्छ', 'पाइन्छ', 'जानकारी', 'भनेको', 'केहो', 'केही',
    'कसले', 'कसलाई', 'कसको', 'कुन', 'कहाँ', 'किन', 'सक्छ', 'सक्छन्', 'सक्ने',
    'what', 'is', 'the', 'provision', 'regarding', 'tell', 'me', 'about', 
    'rules', 'regulation', 'how', 'much', 'does', 'cost', 'to', 'into', 'and', 'from', 'system',
    'for', 'in', 'on', 'at', 'by', 'with', 'a', 'an', 'who', 'can',
    'was', 'were', 'across', 'all', 'total', 'number', 'of', 'as', 'does', 'did',
    'has', 'have', 'had', 'each', 'between', 'during', 'bank', 'banks', 'banking',
    'financial', 'institution', 'institutions', 'report', 'reports', 'annual', 'per', 'used',
    'their', 'which', 'will', 'would', 'could'
}

def normalize_devanagari(text):
    """Normalize Unicode decomposed vowel combinations, Preeti artifacts, and ligatures."""
    if not text:
        return ""
    t = unicodedata.normalize('NFKC', text)
    # Map Preeti ligature character code \u00cb (Ë) to Devanagari ङ्ग
    t = t.replace('Ë', 'ङ्ग')
    # Recombine decomposed vowel signs: ा + ै -> ौ, ा + े -> ो
    t = t.replace('\u093e\u0948', '\u094c').replace('\u093e\u0947', '\u094b')
    # Fix common Preeti ligature glitched vowels (e.g. व् + halant + ा -> वा)
    t = t.replace('\u094d\u093e', '\u093e')
    # Harmonize common banking spelling variations: बैंकिङ / बैंकिंग / बैङ्किङ -> बैंकिङ्ग
    t = re.sub(r'बैं[किङ्क]+[ङङ्गग]', 'बैंकिङ्ग', t)
    # Harmonize Hindi-style candra transliterations to standard Nepali Devanagari
    t = t.replace('वॉलेट', 'वालेट').replace('वॉ', 'वा')
    return t

def extract_meaningful_keywords(text):
    text_norm = normalize_devanagari(text)
    raw_words = re.findall(r'[\u0900-\u097F\w]+', text_norm)
    keywords = set()
    for w in raw_words:
        w_lower = w.lower()
        if w_lower in STOP_WORDS or len(w) <= 2:
            continue
        keywords.add(w)
        keywords.add(w_lower)
        # English plural stemming (e.g. atms -> atm, banks -> bank, limits -> limit)
        if w_lower.endswith('s') and len(w_lower) > 3:
            base_s = w_lower[:-1]
            if base_s not in STOP_WORDS:
                keywords.add(base_s)
        # Map common legacy font acronyms
        if w_lower in ('ussd', 'यूएसएसडी'):
            keywords.add('ग्क्क्म्')
        # Suffix stripping for inflected Nepali tokens
        for suffix in ['सम्बन्धी', 'सम्बन्धमा', 'मार्फत', 'अनुसार', 'सम्म', 'हरु', 'हरू', 'को', 'का', 'की', 'मा', 'ले', 'लाई', 'बाट']:
            if w.endswith(suffix) and len(w) > len(suffix) + 2:
                base = w[:-len(suffix)]
                if base.lower() not in STOP_WORDS and len(base) > 2:
                    keywords.add(base)
                    keywords.add(base.replace('ः', ''))
                    keywords.add(base.replace(':', ''))
        # Normalize Visarga
        keywords.add(w.replace('ः', ''))
        keywords.add(w.replace(':', ''))

    return {k for k in keywords if k.lower() not in STOP_WORDS and len(k) > 2}

def hybrid_search(user_query, table, model, translated_terms="", selected_doc="All Documents", top_k=6):
    k_const = 30  # Standard RRF constant

    # 1. Primary Dense Search (Direct Query Intent)
    d_pri = {}
    q_vec = model.encode(user_query).tolist()
    search_q = table.search(q_vec)
    if selected_doc and selected_doc != "All Documents":
        search_q = search_q.where(f"source = '{selected_doc}'")
    for rank, (_, row) in enumerate(search_q.limit(80).to_pandas().iterrows(), 1):
        k = (row['source'], int(row['page']), row['text'][:60])
        d_pri[k] = (rank, row)

    # 2. Translated Dense Search (Cross-Lingual Bridge)
    d_trans = {}
    if translated_terms and translated_terms.strip():
        t_vec = model.encode(translated_terms).tolist()
        search_t = table.search(t_vec)
        if selected_doc and selected_doc != "All Documents":
            search_t = search_t.where(f"source = '{selected_doc}'")
        for rank, (_, row) in enumerate(search_t.limit(80).to_pandas().iterrows(), 1):
            k = (row['source'], int(row['page']), row['text'][:60])
            d_trans[k] = (rank, row)

    # 3. Primary Sparse Inverted Index Search (Exact Native Term Matching)
    s_pri = {}
    kw_pri = extract_meaningful_keywords(user_query)
    clean_pri_fts = " ".join([re.sub(r'[^\w\u0900-\u097F]', '', w) for w in kw_pri if len(w) > 1])
    if clean_pri_fts.strip():
        try:
            search_fts1 = table.search(clean_pri_fts)
            if selected_doc and selected_doc != "All Documents":
                search_fts1 = search_fts1.where(f"source = '{selected_doc}'")
            for rank, (_, row) in enumerate(search_fts1.limit(80).to_pandas().iterrows(), 1):
                k = (row['source'], int(row['page']), row['text'][:60])
                s_pri[k] = (rank, row)
        except Exception:
            pass

    # 4. Translated Sparse Inverted Index Search (Exact Target Term Matching)
    s_trans = {}
    if translated_terms and translated_terms.strip():
        kw_trans = extract_meaningful_keywords(translated_terms)
        clean_trans_fts = " ".join([re.sub(r'[^\w\u0900-\u097F]', '', w) for w in kw_trans if len(w) > 1])
        if clean_trans_fts.strip():
            try:
                search_fts2 = table.search(clean_trans_fts)
                if selected_doc and selected_doc != "All Documents":
                    search_fts2 = search_fts2.where(f"source = '{selected_doc}'")
                for rank, (_, row) in enumerate(search_fts2.limit(80).to_pandas().iterrows(), 1):
                    k = (row['source'], int(row['page']), row['text'][:60])
                    s_trans[k] = (rank, row)
            except Exception:
                pass

    # 5. Multi-Channel Weighted Reciprocal Rank Fusion (RRF)
    all_keys = set(d_pri.keys()) | set(d_trans.keys()) | set(s_pri.keys()) | set(s_trans.keys())
    if not all_keys:
        return []

    fused_results = []
    for k in all_keys:
        dp = d_pri[k][0] if k in d_pri else 999
        dt = d_trans[k][0] if k in d_trans else 999
        sp = s_pri[k][0] if k in s_pri else 999
        st = s_trans[k][0] if k in s_trans else 999

        row = (d_pri.get(k) or s_pri.get(k) or d_trans.get(k) or s_trans.get(k))[1]

        # Multi-Channel Weighted RRF:
        # Primary dense (1.0), Primary sparse exact tokens (1.2), Cross-lingual auxiliary (0.6 each)
        rrf_score = (1.0 / (k_const + dp)) + (1.2 / (k_const + sp)) + (0.6 / (k_const + dt)) + (0.6 / (k_const + st))
        fused_results.append({
            'source': row['source'],
            'page': int(row['page']),
            'text': row['text'],
            'score': rrf_score
        })

    fused_results.sort(key=lambda x: x['score'], reverse=True)

    # 6. Diversity re-ranking: prevent duplicate pages across directive editions
    diverse_results = []
    seen_word_sets = []
    for item in fused_results:
        wset = set(re.findall(r'[\u0900-\u097F\w]+', item['text'].lower()))
        is_dup = False
        for st in seen_word_sets:
            overlap = len(wset & st) / max(len(wset), 1)
            if overlap > 0.75:
                is_dup = True
                break
        if not is_dup:
            diverse_results.append(item)
            seen_word_sets.append(wset)
            if len(diverse_results) >= top_k:
                break

    return diverse_results

# Cached translation lookup to avoid repeated API calls
if "translation_cache" not in st.session_state:
    st.session_state.translation_cache = {}

def expand_query_crosslingual(q, client):
    """Bidirectional cross-lingual query expansion for English & Nepali banking documents."""
    clean_q = q.strip().lower()
    if clean_q in st.session_state.translation_cache:
        return st.session_state.translation_cache[clean_q]

    is_nepali = sum(1 for c in q if '\u0900' <= c <= '\u097f') >= max(len(q.replace(' ', '')), 1) * 0.3

    if is_nepali:
        sys_instruction = (
            "You are a specialized bilingual terminology engine for Nepal Rastra Bank reports and directives.\n"
            "The user question is in Nepali. Translate the core banking entities and financial metrics into their official English terminology (for finding tables in English Annual Reports):\n"
            "- विकास बैंक -> Development Banks, DBs\n"
            "- वित्त कम्पनी -> Finance Companies, FCs\n"
            "- इन्टरनेट बैंकिङ -> Internet Banking\n"
            "- मोबाइल बैंकिङ -> Mobile Banking\n"
            "- वञ्चित क्षेत्र कर्जा -> Deprived Sector Lending\n"
            "- आधार दर -> Base Rate\n"
            "- तनाव परीक्षण -> Stress Testing, Liquidity Shock\n"
            "- शीघ्र सुधारात्मक कारबाही -> Prompt Corrective Action, PCA\n"
            "- निष्कृय कर्जा -> Non-Performing Loans, NPL\n"
            "Output 3-5 comma-separated English terms, nothing else."
        )
    else:
        sys_instruction = (
            "Translate all key banking subjects, services, and regulatory concepts from the question into official Nepal Rastra Bank (NRB) Nepali terms.\n"
            "Always use official Nepali Devanagari terms:\n"
            "- wallet -> वालेट (NOT वॉलेट)\n"
            "- banking -> बैंकिङ्ग (NOT बैंकिंग)\n"
            "- payment -> भुक्तानी (NOT पेमेन्ट)\n"
            "- agent -> आधिकारिक प्रतिनिधि, एजेन्ट\n"
            "- cash deposit -> नगद जम्मा\n"
            "- cash withdrawal -> नगद झिक्ने, नगद प्राप्त\n"
            "- blacklisting -> कालोसूची, फुकुवा\n"
            "- self-declaration -> स्वघोषणा\n"
            "- USSD -> ग्क्क्म्, USSD\n"
            "Return 3-6 comma-separated Nepali terms in Devanagari script only, nothing else."
        )

    try:
        res = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": sys_instruction},
                {"role": "user", "content": q}
            ],
            temperature=0.0,
            max_tokens=60
        )
        terms = res.choices[0].message.content.strip()
        st.session_state.translation_cache[clean_q] = terms
        return terms
    except Exception:
        return ""

# 2. Cached Resources (Loads heavy ML models once into RAM)
@st.cache_resource
def load_models():
    embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    groq_client = Groq(api_key=GROQ_API_KEY)
    return embedding_model, groq_client

def get_live_table():
    """Always connects to the live database so newly added files are immediately visible."""
    db = lancedb.connect("./lancedb_data")
    return db.open_table("bank_documents")

try:
    embedding_model, groq_client = load_models()
    table = get_live_table()
except Exception as e:
    st.error(f"⚠️ Failed to connect to database or Groq. Error: {e}")
    st.stop()

# 3. Sidebar: System Status & Document Management
with st.sidebar:
    st.title("🏦 Bank Document System")
    st.caption("Powered by **Qwen 27B** (Groq LPU) • Multilingual (नेपाली / EN)")
    st.divider()

    # Active Documents in Database
    st.subheader("📚 Indexed Documents")
    try:
        df = table.to_pandas()
        sources_summary = df["source"].value_counts()
        for doc_name, count in sources_summary.items():
            st.write(f"• **{doc_name}** ({count} chunks)")
        doc_options = ["All Documents"] + list(sources_summary.index)
    except Exception:
        doc_options = ["All Documents"]

    st.divider()

    # Optional Document Filter
    st.subheader("🎯 Search Filter")
    selected_doc = st.selectbox(
        "Focus search on a specific file:",
        options=doc_options,
        index=0
    )

    st.divider()

    # File Uploader
    st.subheader("📤 Add New Document")
    uploaded_file = st.file_uploader(
        "Drop a PDF, DOCX, or TXT file here",
        type=["pdf", "docx", "txt"]
    )
    if uploaded_file is not None:
        save_path = os.path.join("./", uploaded_file.name)
        if not os.path.exists(save_path):
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Saved '{uploaded_file.name}' to folder!")
            st.info("File saved. Ingest script or watcher will process it automatically.")

# 4. Main Chat Interface
st.title("💬 Confidential Banking Document Intelligence")
st.write("Ask regulatory, circular, fee, or policy questions in **नेपाली** or **English**.")

# Quick Demo Prompt Buttons (Executive Showcase)
st.markdown("##### ⚡ Quick Showcase Questions (Click to test):")
col1, col2 = st.columns(2)
with col1:
    btn1 = st.button("📋 स्वःघोषणासम्बन्धी व्यवस्था (Self-Declaration)")
    btn2 = st.button("💰 एजेन्टमार्फत नगद जम्मा गर्ने सीमा (Agent Limits)")
with col2:
    btn3 = st.button("🌐 Tell us about the self-declaration system")
    btn4 = st.button("💳 Daily & monthly cash deposit limits (English)")

# Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "नमस्ते! म नेपाल राष्ट्र बैंक सम्बन्धी कागजातहरूको आधिकारिक सहायक हुँ। तपाईं परिपत्र, निर्देशन, कारोबार सीमा वा शुल्कबारे कुनै पनि प्रश्न सोध्न सक्नुहुन्छ।",
            "sources": [],
            "latency": None
        }
    ]

# Display Previous Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("latency"):
            st.caption(f"⚡ {msg['latency']}")
        if msg.get("sources"):
            with st.expander("📄 Sources Cited"):
                for src in msg["sources"]:
                    st.write(f"- {src}")

# Determine Active User Input (from typing or click)
preset_query = None
if btn1:
    preset_query = "स्वःघोषणासम्बन्धी व्यवस्था बारेमा भन्नुहोस"
elif btn2:
    preset_query = "एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?"
elif btn3:
    preset_query = "Tell us about the self-declaration system."
elif btn4:
    preset_query = "What is the daily and monthly cash deposit limit in a wallet through an authorized agent?"

chat_input_val = st.chat_input("Type your question here (उदा: स्वःघोषणासम्बन्धी व्यवस्था बारेमा भन्नुहोस)...")
active_query = preset_query or chat_input_val

if active_query:
    start_time = time.time()
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": active_query})
    with st.chat_message("user"):
        st.markdown(active_query)

    # 2. Cross-Lingual Dual-Pass Hybrid Retrieval
    translated_terms = expand_query_crosslingual(active_query, groq_client)
    live_table = get_live_table()
    results = hybrid_search(active_query, live_table, embedding_model, translated_terms=translated_terms, selected_doc=selected_doc, top_k=6)

    context_text = ""
    sources_list = []
    for item in results:
        context_text += f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}]:\n{item['text']}\n"
        sources_list.append(f"**{item['source']}** (Page {item['page']})")

    # 3. Professional Banking System Prompt
    system_prompt = f"""You are an official banking document intelligence assistant for Nepal Rastra Bank.
Your job is to extract exact figures, limits, fee tiers, and regulatory clauses from the provided context.

RULES:
1. If the question is in Nepali, answer in formal, professional Nepali (zero Hindi words).
2. If the question is in English, answer in clear, professional English.
3. Present the exact numbers, fee tier ranges, and limits clearly.
4. Quote the exact clause from the document whenever applicable.
5. Always cite the document name and page number.
6. Interpret statutory conditions and exclusionary scopes logically:
   - For example, if a directive states that a service is permitted in "X बाहेकका क्षेत्रमा" (areas except/excluding X), state definitively that it cannot be operated / is not permitted in X. Do not claim information is missing when the regulatory scope is explicitly defined.
7. Only state "उपलब्ध कागजातमा यो जानकारी फेला परेन / Information not found in the documents" if the subject matter is genuinely absent from the provided context.

Context from files:
{context_text}"""

    # 4. Stream Groq Response to UI
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            stream = groq_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": active_query}
                ],
                temperature=0.1,
                max_tokens=900,
                stream=True
            )

            for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                full_response += token
                response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)
            elapsed_sec = time.time() - start_time
            latency_str = f"Answered in {elapsed_sec:.2f}s via Qwen 27B on Groq LPU"
            st.caption(f"⚡ {latency_str}")

            # Show Sources Expander
            unique_sources = list(set(sources_list))
            if unique_sources:
                with st.expander("📄 Sources Cited & Reference Snippets"):
                    for item in results:
                        st.markdown(f"**{item['source']}** — Page {item['page']}")
                        st.code(item['text'][:250].strip() + "...", language="text")

            # Save to Session State
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": unique_sources,
                "latency": latency_str
            })

        except Exception as e:
            st.error(f"⚠️ Error querying Groq: {e}")
