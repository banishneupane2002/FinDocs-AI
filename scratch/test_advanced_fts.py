import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
import lancedb, re
from sentence_transformers import SentenceTransformer

db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def advanced_hybrid_search(user_query, translated_terms="", top_k=6):
    candidates_dict = {}

    # 1. Dense Vector Search (user query)
    q_vec = model.encode(user_query).tolist()
    vec_res = table.search(q_vec).limit(35).to_pandas()
    for _, row in vec_res.iterrows():
        k = (row['source'], int(row['page']), row['text'][:60])
        candidates_dict[k] = {
            'source': row['source'],
            'page': int(row['page']),
            'text': row['text'],
            'distance': float(row['_distance']),
            'fts_score': 0.0
        }

    # 2. Dense Vector Search (translated terms if available)
    if translated_terms and translated_terms.strip():
        t_vec = model.encode(translated_terms).tolist()
        t_vec_res = table.search(t_vec).limit(35).to_pandas()
        for _, row in t_vec_res.iterrows():
            k = (row['source'], int(row['page']), row['text'][:60])
            if k not in candidates_dict:
                candidates_dict[k] = {
                    'source': row['source'],
                    'page': int(row['page']),
                    'text': row['text'],
                    'distance': float(row['_distance']),
                    'fts_score': 0.0
                }
            else:
                candidates_dict[k]['distance'] = min(candidates_dict[k]['distance'], float(row['_distance']))

    # 3. Native LanceDB Sparse / FTS Search (Exact keywords on disk)
    # Clean query for FTS to avoid special characters
    fts_q = re.sub(r'[^\w\s\u0900-\u097F]', ' ', user_query).strip()
    if fts_q:
        try:
            fts_res = table.search(fts_q).limit(35).to_pandas()
            for rank, (_, row) in enumerate(fts_res.iterrows()):
                k = (row['source'], int(row['page']), row['text'][:60])
                score = 1.0 / (1.0 + rank)
                if k not in candidates_dict:
                    candidates_dict[k] = {
                        'source': row['source'],
                        'page': int(row['page']),
                        'text': row['text'],
                        'distance': 15.0, # default distance for pure keyword hit
                        'fts_score': score
                    }
                else:
                    candidates_dict[k]['fts_score'] = max(candidates_dict[k]['fts_score'], score)
        except Exception as e:
            pass

    # Also FTS search translated terms
    if translated_terms and translated_terms.strip():
        fts_t = re.sub(r'[^\w\s\u0900-\u097F]', ' ', translated_terms).strip()
        if fts_t:
            try:
                fts_t_res = table.search(fts_t).limit(35).to_pandas()
                for rank, (_, row) in enumerate(fts_t_res.iterrows()):
                    k = (row['source'], int(row['page']), row['text'][:60])
                    score = 1.0 / (1.0 + rank)
                    if k not in candidates_dict:
                        candidates_dict[k] = {
                            'source': row['source'],
                            'page': int(row['page']),
                            'text': row['text'],
                            'distance': 15.0,
                            'fts_score': score
                        }
                    else:
                        candidates_dict[k]['fts_score'] = max(candidates_dict[k]['fts_score'], score)
            except Exception:
                pass

    # 4. Normalized Hybrid Scoring
    candidates = list(candidates_dict.values())
    for c in candidates:
        c['sem_raw'] = 1.0 / (1.0 + c['distance'])
        c['fts_raw'] = c['fts_score']

    min_sem = min(c['sem_raw'] for c in candidates)
    max_sem = max(c['sem_raw'] for c in candidates)
    sem_range = (max_sem - min_sem) if max_sem > min_sem else 1.0

    min_fts = min(c['fts_raw'] for c in candidates)
    max_fts = max(c['fts_raw'] for c in candidates)
    fts_range = (max_fts - min_fts) if max_fts > min_fts else 1.0

    for c in candidates:
        norm_sem = (c['sem_raw'] - min_sem) / sem_range
        norm_fts = (c['fts_raw'] - min_fts) / fts_range if max_fts > 0 else 0.0
        # 60% Semantic Meaning + 40% Exact Full-Text Search
        c['score'] = 0.6 * norm_sem + 0.4 * norm_fts

    candidates.sort(key=lambda x: x['score'], reverse=True)

    # Diversity filter
    diverse = []
    seen = set()
    for c in candidates:
        key = (int(c['page']), c['text'][:60])
        if key not in seen:
            seen.add(key)
            diverse.append(c)
        if len(diverse) >= top_k:
            break

    return diverse

# Test on Q1, Q3, Q5
for q, trans in [
    ("How many debit cards were issued by Development Banks as of Mid-July 2025?", ""),
    ("What was the total number of ATMs across all banks and financial institutions as of Mid-July 2025?", ""),
    ("एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?", "")
]:
    res = advanced_hybrid_search(q, translated_terms=trans, top_k=4)
    print(f"\nQUERY: {q}")
    for i, r in enumerate(res, 1):
        print(f" {i}. [{r['source']} P{r['page']}] Score={r['score']:.3f} | {r['text'][:80].replace(chr(10), ' ')}")

