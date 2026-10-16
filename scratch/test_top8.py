import os, sys
sys.path.insert(0, os.getcwd())
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb
from sentence_transformers import SentenceTransformer
from core.lexicon import extract_meaningful_keywords
import re

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

all_keys = set(d_pri.keys()) | set(d_trans.keys()) | set(s_pri.keys()) | set(s_trans.keys())

def get_doc_year(src: str) -> int:
    ym = re.search(r'(20[78][0-9]|20[12][0-9])', src)
    return int(ym.group(1)) if ym else 0

all_sources = [k[0] for k in all_keys]
bs_years = [get_doc_year(s) for s in all_sources if get_doc_year(s) >= 2050]
ad_years = [get_doc_year(s) for s in all_sources if 2000 <= get_doc_year(s) < 2050]
max_bs_year = max(bs_years, default=0)
max_ad_year = max(ad_years, default=0)

rrf_scores = {}
for k in all_keys:
    score = 0.0
    row_obj = None
    if k in d_pri:
        score += 1.0 / (k_const + d_pri[k][0])
        row_obj = d_pri[k][1]
    if k in d_trans:
        score += 0.9 / (k_const + d_trans[k][0])
        if row_obj is None: row_obj = d_trans[k][1]
    if k in s_pri:
        score += 1.3 / (k_const + s_pri[k][0])
        if row_obj is None: row_obj = s_pri[k][1]
    if k in s_trans:
        score += 1.1 / (k_const + s_trans[k][0])
        if row_obj is None: row_obj = s_trans[k][1]

    doc_yr = get_doc_year(k[0])
    target_max = max_bs_year if doc_yr >= 2050 else max_ad_year
    if target_max > 0 and doc_yr == target_max:
        score *= 1.60
    elif target_max > 0 and doc_yr == target_max - 1:
        score *= 0.90
    elif target_max > 0 and doc_yr < target_max - 1:
        score *= 0.75

    rrf_scores[k] = (score, row_obj)

sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1][0], reverse=True)
print("=== TOP 25 CANDIDATES BEFORE DIVERSITY CAPPING ===")
for i, (k, (score, row)) in enumerate(sorted_items[:25], 1):
    print(f"{i:2d}: {k[0]:28s} page {k[1]:3d} | score={score:.4f}")
