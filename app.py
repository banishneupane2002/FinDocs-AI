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
    'for', 'in', 'on', 'at', 'by', 'with', 'a', 'an', 'who', 'can'
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
            keywords.add(w_lower[:-1])
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
        keywords.add(w.replace('ः', ''))
        keywords.add(w.replace(':', ''))

    return {k for k in keywords if k.lower() not in STOP_WORDS and len(k) > 2}

def hybrid_search(user_query, table, model, selected_doc="All Documents", top_k=4):
    df_all = table.to_pandas()
    if selected_doc and selected_doc != "All Documents":
        df_all = df_all[df_all['source'] == selected_doc].copy()

    N = len(df_all)
    if N == 0:
        return []

    df_all['norm_text'] = df_all['text'].apply(normalize_devanagari)

    # 1. Broad Vector Search (Top 60)
    query_vector = model.encode(user_query).tolist()
    search_q = table.search(query_vector)
    if selected_doc and selected_doc != "All Documents":
        search_q = search_q.where(f"source = '{selected_doc}'")
    vec_candidates = search_q.limit(min(60, N)).to_pandas()

    # 2. Extract Meaningful Keywords
    keywords = extract_meaningful_keywords(user_query)

    # 3. Direct Keyword Matching across full corpus
    def make_key(row):
        return (row['source'], int(row['page']), row['text'][:60])

    candidates_dict = {}
    for _, row in vec_candidates.iterrows():
        k = make_key(row)
        candidates_dict[k] = {
            'row': row,
            'distance': row.get('_distance', 1.0)
        }

    if keywords:
        for _, row in df_all.iterrows():
            text = row['norm_text']
            if any(kw in text for kw in keywords):
                k = make_key(row)
                if k not in candidates_dict:
                    candidates_dict[k] = {
                        'row': row,
                        'distance': None
                    }

    # 4. Hybrid Scoring
    scored = []
    for k, item in candidates_dict.items():
        row = item['row']
        dist = item['distance']
        sem_score = (1.0 / (1.0 + dist)) if dist is not None else 0.35

        kw_score = 0.0
        text = normalize_devanagari(row['text'])
        for kw in keywords:
            kw_re = re.compile(re.escape(kw), re.IGNORECASE)
            count = len(kw_re.findall(text))
            if count > 0:
                doc_freq = sum(1 for t in df_all['norm_text'] if kw.lower() in t.lower())
                idf = math.log((N + 1) / (doc_freq + 1))
                kw_score += (min(count, 3) * 0.5 + 1.0) * idf

        total_score = sem_score + kw_score
        scored.append({
            'source': row['source'],
            'page': int(row['page']),
            'text': row['text'],
            'score': total_score
        })

    scored.sort(key=lambda x: x['score'], reverse=True)

    # Diversity re-ranking: prevent identical cross-edition duplicate tables from monopolizing top slots
    diverse_results = []
    seen_word_sets = []
    for item in scored:
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
        return f"{q} {st.session_state.translation_cache[clean_q]}"

    # If the user query is already written in Nepali Devanagari, preserve pure Devanagari search
    # to avoid polluting sparse keyword ranking with broad English buzzwords (e.g. from Annual Reports).
    is_nepali = sum(1 for c in q if '\u0900' <= c <= '\u097f') >= max(len(q.replace(' ', '')), 1) * 0.3
    if is_nepali:
        return q

    try:
        res = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a specialized bilingual terminology engine for Nepal Rastra Bank (NRB) regulations, directives, and reports. "
                        "Translate key banking/regulatory concepts into their official NRB terminology: "
                        "- Corporate governance -> संस्थागत सुशासन "
                        "- Cash withdrawal / cash out via agent -> एजेन्टमार्फत नगद प्राप्त, नगद झिक्ने, आधिकारिक प्रतिनिधि "
                        "- Digital wallet -> वालेट "
                        "- Branchless banking -> शाखारहित बैंकिङ्ग सेवा, व्यावसायिक आधिकारिक प्रतिनिधि "
                        "- USSD -> यूएसएसडी, ग्क्क्म् "
                        "- Cooling-off period -> फुकुवा, कालोसूची "
                        "- Self-declaration -> स्वघोषणा "
                        "Output 3-5 official Nepali regulatory terms. "
                        "Return ONLY the comma-separated terms, nothing else."
                    )
                },
                {"role": "user", "content": q}
            ],
            temperature=0.0,
            max_tokens=60
        )
        terms = res.choices[0].message.content.strip()
        st.session_state.translation_cache[clean_q] = terms
        return f"{q} {terms}"
    except Exception:
        return q

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
    search_query = expand_query_crosslingual(active_query, groq_client)
    live_table = get_live_table()
    results = hybrid_search(search_query, live_table, embedding_model, selected_doc=selected_doc, top_k=5)

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
                max_tokens=450,
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
