import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lancedb
from sentence_transformers import SentenceTransformer
from core.search import extract_meaningful_keywords, hybrid_search

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

q = "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?"
trans = "मार्जिन कर्जा, शेयर धितो कर्जा, ७० प्रतिशत"

kw_pri = extract_meaningful_keywords(q)
clean_pri_fts = " ".join([w for w in kw_pri if len(w) > 1 or w in '०१२३४५६७८९0123456789'])
print("clean_pri_fts:", repr(clean_pri_fts))

kw_trans = extract_meaningful_keywords(trans)
clean_trans_fts = " ".join([w for w in kw_trans if len(w) > 1 or w in '०१२३४५६७८९0123456789'])
print("clean_trans_fts:", repr(clean_trans_fts))

# Check s_trans hits:
res2 = tbl.search(clean_trans_fts).limit(10).to_pandas()
print("\ns_trans top 10:")
for rank, (_, row) in enumerate(res2.iterrows(), 1):
    print(f"  {rank}: {row['source']} page {row['page']} score={row['_score']:.2f}")

# Check s_pri hits:
res1 = tbl.search(clean_pri_fts).limit(10).to_pandas()
print("\ns_pri top 10:")
for rank, (_, row) in enumerate(res1.iterrows(), 1):
    print(f"  {rank}: {row['source']} page {row['page']} score={row['_score']:.2f}")

