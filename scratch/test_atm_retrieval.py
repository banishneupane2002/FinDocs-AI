import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from app import extract_meaningful_keywords, hybrid_search
import lancedb
from sentence_transformers import SentenceTransformer

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

q = "what amount at max could be withdrawn from atm"
kw = extract_meaningful_keywords(q)
print("Keywords extracted:", kw)

db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')
model = SentenceTransformer('all-MiniLM-L6-v2')

results = hybrid_search(q, table, model, top_k=6)
print("\nHybrid Search Results for:", q)
for r in results:
    print(f"Score: {r['score']:.4f} | Source: {r['source']} Page: {r['page']}")
    print(f"Snippet: {r['text'][:180].replace(chr(10), ' ')}\n")
