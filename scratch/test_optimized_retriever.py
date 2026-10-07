import sys, time, re, math
import lancedb
from sentence_transformers import SentenceTransformer

sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def normalize_devanagari(text: str) -> str:
    if not text:
        return ""
    import unicodedata
    text = unicodedata.normalize("NFKC", text)
    # Common Preeti converter glitches
    glitches = {
        'बैंकिË': 'बैंकिङ्ग',
        'बैंिकङ्ग': 'बैंकिङ्ग',
        'बैिकङ्ग': 'बैंकिङ्ग',
        'िनदर्ेशन': 'निर्देशन',
        'निदर्ेशन': 'निर्देशन',
        'अ.प्रा.': 'एकीकृत',
        'द्धठ': '२७',
        'द्दद्द': '२२',
    }
    for k, v in glitches.items():
        text = text.replace(k, v)
    return text

def test_search(query: str, nepali_translation: str = "", top_k: int = 4):
    print(f"\n==================================================")
    print(f"QUERY: '{query}'")
    if nepali_translation:
        print(f"TRANSLATED: '{nepali_translation}'")
    
    t0 = time.time()
    # 1. Vector search using LanceDB native index (Top 30)
    q_vec = model.encode(query).tolist()
    vec_results = table.search(q_vec).limit(30).to_pandas()
    
    candidates = {}
    for _, row in vec_results.iterrows():
        key = (row['source'], int(row['page']), row['text'][:50])
        candidates[key] = {
            'source': row['source'],
            'page': int(row['page']),
            'text': row['text'],
            'distance': float(row['_distance'])
        }
        
    # If translation is provided, also get top 30 from translated vector
    if nepali_translation:
        t_vec = model.encode(nepali_translation).tolist()
        t_results = table.search(t_vec).limit(30).to_pandas()
        for _, row in t_results.iterrows():
            key = (row['source'], int(row['page']), row['text'][:50])
            if key not in candidates:
                candidates[key] = {
                    'source': row['source'],
                    'page': int(row['page']),
                    'text': row['text'],
                    'distance': float(row['_distance'])
                }
            else:
                # Keep the better distance
                candidates[key]['distance'] = min(candidates[key]['distance'], float(row['_distance']))

    print(f"Total candidate chunks retrieved on disk: {len(candidates)}")
    
    # 2. Extract keywords from both query and translation
    all_text_for_kw = f"{query} {nepali_translation}".lower()
    raw_words = re.findall(r'[\u0900-\u097F\w]+', all_text_for_kw)
    stop_words = {'what', 'is', 'the', 'a', 'an', 'in', 'on', 'of', 'for', 'to', 'can', 'be', 'must', 'with', 'and', 'or', 'by', 'as', 'कस्तो', 'के', 'हो', 'छ', 'र', 'वा', 'मा', 'को', 'का'}
    keywords = [w for w in raw_words if w not in stop_words and len(w) > 2]

    # 3. Score the candidates using Min-Max Normalized Hybrid Scoring
    candidate_list = list(candidates.values())
    
    # Compute raw semantic scores (1 / (1 + distance))
    for c in candidate_list:
        c['sem_raw'] = 1.0 / (1.0 + c['distance'])
        # Compute keyword match count
        c_text_norm = normalize_devanagari(c['text']).lower()
        match_count = sum(1 for kw in keywords if kw in c_text_norm)
        c['kw_raw'] = match_count

    # Min-Max Normalization
    min_sem = min(c['sem_raw'] for c in candidate_list)
    max_sem = max(c['sem_raw'] for c in candidate_list)
    sem_range = max_sem - min_sem if max_sem > min_sem else 1.0

    min_kw = min(c['kw_raw'] for c in candidate_list)
    max_kw = max(c['kw_raw'] for c in candidate_list)
    kw_range = max_kw - min_kw if max_kw > min_kw else 1.0

    for c in candidate_list:
        norm_sem = (c['sem_raw'] - min_sem) / sem_range
        norm_kw = (c['kw_raw'] - min_kw) / kw_range if max_kw > 0 else 0.0
        # 70% semantic meaning, 30% keyword match
        c['final_score'] = 0.7 * norm_sem + 0.3 * norm_kw

    candidate_list.sort(key=lambda x: x['final_score'], reverse=True)

    # Diversity filter: avoid duplicate pages across directive_1 and directive_2
    diverse = []
    seen = set()
    for c in candidate_list:
        key = (int(c['page']), c['text'][:60])
        if key not in seen:
            seen.add(key)
            diverse.append(c)
        if len(diverse) >= top_k:
            break

    elapsed = (time.time() - t0) * 1000
    print(f"Search completed in {elapsed:.1f}ms")
    for i, res in enumerate(diverse, 1):
        clean_snip = res['text'].replace('\n', ' ')[:110]
        print(f" {i}. [{res['source']} - Page {res['page']}] Score: {res['final_score']:.3f} | {clean_snip}...")

test_search(
    "What agreement must a bank make with a customer for branchless banking?",
    nepali_translation="शाखारहित बैंकिङ्ग सेवा ग्राहक सम्झौता"
)

test_search(
    "Can a blacklisted person be appointed as branchless banking agent?",
    nepali_translation="कालोसूचीमा परेको व्यक्ति शाखारहित बैंकिङ्ग एजेन्ट नियुक्त हुन सक्छ?"
)

test_search(
    "what was number of atms on mid july 2025"
)

