import os
import sys
import io
import re
import math
import time
import unicodedata
from functools import lru_cache
import lancedb
from sentence_transformers import SentenceTransformer
from groq import Groq

# Force UTF-8 on Windows terminal
if sys.platform == "win32":
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# Load GROQ API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.strip().split("=", 1)[1].strip()

if not GROQ_API_KEY:
    print("❌ Error: GROQ_API_KEY not found. Please set it in .env or as an environment variable.")
    sys.exit(1)

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "qwen/qwen3.8-27b"

# Connect to LanceDB and the Multilingual Model
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

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
        # Normalize Visarga
        keywords.add(w.replace('ः', ''))
        keywords.add(w.replace(':', ''))

    return {k for k in keywords if k.lower() not in STOP_WORDS and len(k) > 2}

def hybrid_search(user_query, table, model, top_k=4):
    df_all = table.to_pandas()
    N = len(df_all)
    if N == 0:
        return []

    # Pre-normalize text for accurate ligature matching
    df_all['norm_text'] = df_all['text'].apply(normalize_devanagari)

    # 1. Broad Vector Search (Top 60)
    query_vector = model.encode(user_query).tolist()
    vec_candidates = table.search(query_vector).limit(min(60, N)).to_pandas()

    # 2. Extract Keywords
    keywords = extract_meaningful_keywords(user_query)

    # 3. Direct Keyword Matching across full corpus to avoid dense vector pruning
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

# Cache translation queries to eliminate redundant API calls
_translation_cache = {}

def expand_query_crosslingual(q, groq_client):
    """Bidirectional cross-lingual query expansion for English & Nepali banking documents."""
    clean_q = q.strip().lower()
    if clean_q in _translation_cache:
        return f"{q} {_translation_cache[clean_q]}"

    # If the user query is already written in Nepali Devanagari, preserve pure Devanagari search
    # to avoid polluting sparse keyword ranking with broad English buzzwords (e.g. from Annual Reports).
    is_nepali = sum(1 for c in q if '\u0900' <= c <= '\u097f') >= max(len(q.replace(' ', '')), 1) * 0.3
    if is_nepali:
        return q

    try:
        res = groq_client.chat.completions.create(
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
        _translation_cache[clean_q] = terms
        return f"{q} {terms}"
    except Exception:
        return q

def call_groq_with_retry(groq_client, messages, max_retries=2):
    """Execute completion call with automatic backoff on rate limits."""
    for attempt in range(max_retries + 1):
        try:
            return groq_client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.1,
                max_tokens=400,
                stream=True
            )
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                if attempt < max_retries:
                    time.sleep(3.0 * (attempt + 1))
                    continue
            raise e

def main():
    print("\n" + "=" * 65)
    print("BANK DOCUMENT INTELLIGENCE ACTIVE ")
    print("Supports both English & Official Nepali. Type 'exit' to quit.")
    print("=" * 65 + "\n")

    while True:
        try:
            user_question = input("User: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_question:
            continue
        if user_question.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break

        print("   Searching documents (Cross-Lingual Dual-Pass Hybrid Retrieval)...")

        search_query = expand_query_crosslingual(user_question, client)
        results = hybrid_search(search_query, table, embedding_model, top_k=4)

        context_text = ""
        sources = []
        for item in results:
            context_text += f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}]:\n{item['text']}\n"
            sources.append(f"{item['source']} (Page {item['page']})")

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

        print("   AI is generating answer...\n")
        try:
            print("Assistant:\n", end="", flush=True)
            stream = call_groq_with_retry(
                client,
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ]
            )

            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)

            print("\n\nSources Cited:")
            for src in set(sources):
                print(f"   * {src}")
            print("-" * 65 + "\n")

        except Exception as e:
            print(f"\n⚠️ Error connecting to Groq API: {e}\n")

if __name__ == "__main__":
    main()