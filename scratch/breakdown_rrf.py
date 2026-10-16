import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lancedb
from sentence_transformers import SentenceTransformer
from core.search import extract_meaningful_keywords

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

q = "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?"
trans = "मार्जिन कर्जा, शेयर धितो कर्जा, ७० प्रतिशत"

k_const = 30
q_vec = model.encode(q).tolist()
t_vec = model.encode(trans).tolist()

kw_pri = extract_meaningful_keywords(q)
clean_pri_fts = " ".join([w for w in kw_pri if len(w) > 1 or w in '०१२३४५६७८९0123456789'])

kw_trans = extract_meaningful_keywords(trans)
clean_trans_fts = " ".join([w for w in kw_trans if len(w) > 1 or w in '०१२३४५६७८९0123456789'])

d_pri = { (r['source'], int(r['page'])): rank for rank, (_, r) in enumerate(tbl.search(q_vec).limit(100).to_pandas().iterrows(), 1) }
d_trans = { (r['source'], int(r['page'])): rank for rank, (_, r) in enumerate(tbl.search(t_vec).limit(100).to_pandas().iterrows(), 1) }
s_pri = { (r['source'], int(r['page'])): rank for rank, (_, r) in enumerate(tbl.search(clean_pri_fts).limit(100).to_pandas().iterrows(), 1) }
s_trans = { (r['source'], int(r['page'])): rank for rank, (_, r) in enumerate(tbl.search(clean_trans_fts).limit(100).to_pandas().iterrows(), 1) }

target_pages = [23, 25, 26, 33, 40, 53]
print(f"{'Page':<6} | {'d_pri':<8} | {'d_trans':<8} | {'s_pri':<8} | {'s_trans':<8} | {'RRF Score':<10}")
print("-" * 60)
for pg in target_pages:
    k = ('Unified_directive_2082.pdf', pg)
    dp = d_pri.get(k, 999)
    dt = d_trans.get(k, 999)
    sp = s_pri.get(k, 999)
    st = s_trans.get(k, 999)
    score = 0.0
    if k in d_pri: score += 1.0 / (k_const + dp)
    if k in d_trans: score += 0.9 / (k_const + dt)
    if k in s_pri: score += 1.3 / (k_const + sp)
    if k in s_trans: score += 1.1 / (k_const + st)
    score *= 1.5 # 2082 recency
    print(f"{pg:<6} | {dp:<8} | {dt:<8} | {sp:<8} | {st:<8} | {score:<10.5f}")

