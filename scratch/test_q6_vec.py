import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb
from sentence_transformers import SentenceTransformer

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

q = "When calculating the Capital Adequacy Ratio (CAR), what is the risk weight assigned to loans secured by residential properties?"
q_vec = model.encode(q).tolist()
res = tbl.search(q_vec).limit(10).to_pandas()
print("Top 10 dense vector hits for Q6:")
for idx, (_, r) in enumerate(res.iterrows(), 1):
    p225 = " *** TARGET PAGE 225 ***" if r['page'] == 225 and '2082' in r['source'] else ""
    print(f"  {idx}: {r['source']} page {r['page']} dist={r['_distance']:.4f}{p225}")

