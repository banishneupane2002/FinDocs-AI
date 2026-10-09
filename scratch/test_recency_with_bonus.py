import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
import lancedb
from sentence_transformers import SentenceTransformer
from ask import (
    build_document_year_map,
    extract_meaningful_keywords
)

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
doc_map = build_document_year_map(tbl)

q = "एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?"
translated = "agent wallet cash deposit limit"

k_const = 30
d_pri = {}
q_vec = model.encode(q).tolist()
for rank, (_, row) in enumerate(tbl.search(q_vec).limit(100).to_pandas().iterrows(), 1):
    k = (row['source'], int(row['page']))
    if k not in d_pri:
        d_pri[k] = (rank, row)

t_vec = model.encode(translated).tolist()
d_trans = {}
for rank, (_, row) in enumerate(tbl.search(t_vec).limit(100).to_pandas().iterrows(), 1):
    k = (row['source'], int(row['page']))
    if k not in d_trans:
        d_trans[k] = (rank, row)

s_pri = {}
kw_pri = extract_meaningful_keywords(q)
clean_pri_fts = " ".join([w for w in kw_pri if len(w) > 1])
for rank, (_, row) in enumerate(tbl.search(clean_pri_fts).limit(100).to_pandas().iterrows(), 1):
    k = (row['source'], int(row['page']))
    if k not in s_pri:
        s_pri[k] = (rank, row)

all_keys = set(d_pri.keys()) | set(d_trans.keys()) | set(s_pri.keys())
fused = []
for k in all_keys:
    dp = d_pri[k][0] if k in d_pri else 999
    dt = d_trans[k][0] if k in d_trans else 999
    sp = s_pri[k][0] if k in s_pri else 999
    row = (d_pri.get(k) or s_pri.get(k) or d_trans.get(k))[1]
    
    rrf = (1.0 / (k_const + dp)) + (1.2 / (k_const + sp)) + (0.6 / (k_const + dt))
    
    # Recency weighting
    max_yr = max(doc_map.get(row['source'], {2000}))
    if 'directive' in row['source']:
        rrf += (max_yr - 2078) * 0.004
    elif 'Annual_Report' in row['source']:
        rrf += (max_yr - 2023) * 0.004
        
    fused.append({'source': row['source'], 'page': int(row['page']), 'score': rrf})

fused.sort(key=lambda x: x['score'], reverse=True)
print("Top Pages with Recency Weighting:")
seen = set()
for f in fused:
    sp = (f['source'], f['page'])
    if sp not in seen:
        seen.add(sp)
        print(f"  {f['source']} Page {f['page']} (Score: {f['score']:.4f})")
        if len(seen) >= 4:
            break

