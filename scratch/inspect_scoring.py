import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lancedb
from sentence_transformers import SentenceTransformer
import numpy as np

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

q = "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?"
trans = "मार्जिन कर्जा, शेयर धितो कर्जा, ७० प्रतिशत"

# 1. Check Tantivy FTS search
query_clean = ' OR '.join(["मार्जिन", "कर्जा", "शेयर", "धितो", "७०", "प्रतिशत", "Margin", "Lending", "LTV"])
print("FTS search query:", query_clean)
fts_res = tbl.search(query_clean, query_type="fts").limit(30).to_pandas()
print("\nFTS Top hits:")
for idx, r in fts_res.head(15).iterrows():
    p23_flag = " *** TARGET ***" if r['page'] == 23 and '2082' in r['source'] else ""
    print(f"  {r['source']} Page {r['page']} score={r.get('_score', 0):.2f}{p23_flag}")

# 2. Check Vector search
q_emb = model.encode(q + " " + trans).tolist()
vec_res = tbl.search(q_emb).limit(30).to_pandas()
print("\nVector Top hits:")
for idx, r in vec_res.head(15).iterrows():
    p23_flag = " *** TARGET ***" if r['page'] == 23 and '2082' in r['source'] else ""
    print(f"  {r['source']} Page {r['page']} dist={r.get('_distance', 0):.4f}{p23_flag}")

