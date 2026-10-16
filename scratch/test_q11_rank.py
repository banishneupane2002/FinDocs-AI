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

q = "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?"
trans = "मार्जिन कर्जा, शेयर धितो कर्जा, ७० प्रतिशत"

results = hybrid_search(q, tbl, model, translated_terms=trans, top_k=20)
print("Hybrid search top 20:")
for idx, r in enumerate(results, 1):
    print(f"{idx}: {r['source']} page {r['page']} score={r.get('_score', 0):.4f}")
    if r['page'] == 23 and '2082' in r['source']:
        print("   >>> FOUND PAGE 23 OF 2082 HERE! <<<")
