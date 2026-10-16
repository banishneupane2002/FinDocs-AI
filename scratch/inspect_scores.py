import os, sys
sys.path.insert(0, os.getcwd())
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb
from sentence_transformers import SentenceTransformer
from core.lexicon import extract_meaningful_keywords

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

q = "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?"
trans = "Margin Lending, शेयर धितो कर्जा, मार्जिन कर्जा, ७० प्रतिशत, १८० दिन, बजार मूल्य"

k_const = 30
d_pri = {}
search_q = tbl.search(model.encode(q).tolist())
for rank, (_, row) in enumerate(search_q.limit(100).to_pandas().iterrows(), 1):
    k = (row['source'], int(row['page']))
    if k not in d_pri: d_pri[k] = (rank, row)

d_trans = {}
search_t = tbl.search(model.encode(trans).tolist())
for rank, (_, row) in enumerate(search_t.limit(100).to_pandas().iterrows(), 1):
    k = (row['source'], int(row['page']))
    if k not in d_trans: d_trans[k] = (rank, row)

s_pri = {}
kw_pri = extract_meaningful_keywords(q)
clean_pri = " ".join([w for w in kw_pri if len(w) > 1])
search_fts1 = tbl.search(clean_pri)
for rank, (_, row) in enumerate(search_fts1.limit(100).to_pandas().iterrows(), 1):
    k = (row['source'], int(row['page']))
    if k not in s_pri: s_pri[k] = (rank, row)

s_trans = {}
kw_trans = extract_meaningful_keywords(trans)
clean_trans = " ".join([w for w in kw_trans if len(w) > 1])
search_fts2 = tbl.search(clean_trans)
for rank, (_, row) in enumerate(search_fts2.limit(100).to_pandas().iterrows(), 1):
    k = (row['source'], int(row['page']))
    if k not in s_trans: s_trans[k] = (rank, row)

target_pages = [23, 25, 40, 41]
for pg in target_pages:
    k = ('Unified_directive_2082.pdf', pg)
    dp = d_pri.get(k, (None,))[0]
    dt = d_trans.get(k, (None,))[0]
    sp = s_pri.get(k, (None,))[0]
    st = s_trans.get(k, (None,))[0]
    score = 0.0
    if dp: score += 1.0 / (k_const + dp)
    if dt: score += 0.9 / (k_const + dt)
    if sp: score += 1.3 / (k_const + sp)
    if st: score += 1.1 / (k_const + st)
    score *= 1.25 # 2082 recency
    print(f"2082 Page {pg}: score={score:.4f} | d_pri={dp}, d_trans={dt}, s_pri={sp}, s_trans={st}")

