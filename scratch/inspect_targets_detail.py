import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import lancedb
from sentence_transformers import SentenceTransformer
from scratch.test_clean_fixes import clean_extract_keywords

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

print("=== Q5 DETAILED INSPECTION ===")
q5 = "What is the minimum Statutory Liquidity Ratio (SLR) and Cash Reserve Ratio (CRR) required for a 'C' class finance company?"
t5 = "वैधानिक तरलता अनुपात, अनिवार्य नगद मौज्दात, १० प्रतिशत, ४ प्रतिशत"

q5_vec = model.encode(q5).tolist()
t5_vec = model.encode(t5).tolist()

d_pri_5 = { (r['source'], int(r['page'])): rank for rank, (_, r) in enumerate(table.search(q5_vec).limit(100).to_pandas().iterrows(), 1) }
d_trans_5 = { (r['source'], int(r['page'])): rank for rank, (_, r) in enumerate(table.search(t5_vec).limit(100).to_pandas().iterrows(), 1) }

kw_pri_5 = clean_extract_keywords(q5)
s_pri_5 = { (r['source'], int(r['page'])): rank for rank, (_, r) in enumerate(table.search(" ".join(kw_pri_5)).limit(100).to_pandas().iterrows(), 1) }

kw_trans_5 = clean_extract_keywords(t5)
s_trans_5 = { (r['source'], int(r['page'])): rank for rank, (_, r) in enumerate(table.search(" ".join(kw_trans_5)).limit(100).to_pandas().iterrows(), 1) }

for src in ['Unified_directive_2082.pdf', 'Unified_directive_2081.pdf']:
    for pg in [118, 120]:
        k = (src, pg)
        print(f"k={k} -> d_pri={d_pri_5.get(k, 999)} d_trans={d_trans_5.get(k, 999)} s_pri={s_pri_5.get(k, 999)} s_trans={s_trans_5.get(k, 999)}")

print("\n=== Q11 DETAILED INSPECTION ===")
q11 = "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?"
t11 = "मार्जिन कर्जा, शेयर धितो कर्जा, ७० प्रतिशत, १८० दिन"

q11_vec = model.encode(q11).tolist()
t11_vec = model.encode(t11).tolist()

d_pri_11 = { (r['source'], int(r['page'])): rank for rank, (_, r) in enumerate(table.search(q11_vec).limit(100).to_pandas().iterrows(), 1) }
d_trans_11 = { (r['source'], int(r['page'])): rank for rank, (_, r) in enumerate(table.search(t11_vec).limit(100).to_pandas().iterrows(), 1) }

kw_pri_11 = clean_extract_keywords(q11)
s_pri_11 = { (r['source'], int(r['page'])): rank for rank, (_, r) in enumerate(table.search(" ".join(kw_pri_11)).limit(100).to_pandas().iterrows(), 1) }

kw_trans_11 = clean_extract_keywords(t11)
s_trans_11 = { (r['source'], int(r['page'])): rank for rank, (_, r) in enumerate(table.search(" ".join(kw_trans_11)).limit(100).to_pandas().iterrows(), 1) }

for pg in [23, 25, 26, 33, 40]:
    k = ('Unified_directive_2082.pdf', pg)
    print(f"k={k} -> d_pri={d_pri_11.get(k, 999)} d_trans={d_trans_11.get(k, 999)} s_pri={s_pri_11.get(k, 999)} s_trans={s_trans_11.get(k, 999)}")
