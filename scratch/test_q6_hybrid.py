import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

q = "When calculating the Capital Adequacy Ratio (CAR), what is the risk weight assigned to loans secured by residential properties?"
res = hybrid_search(q, tbl, model, translated_terms="", top_k=10)
print("Hybrid search top 10 for Q6:")
for idx, r in enumerate(res, 1):
    p225 = " *** TARGET PAGE 225 ***" if r['page'] == 225 and '2082' in r['source'] else ""
    print(f"  {idx}: {r['source']} page {r['page']} score={r.get('_score', 0):.4f}{p225}")

