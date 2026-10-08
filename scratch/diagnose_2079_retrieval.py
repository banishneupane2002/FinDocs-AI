import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import app

q = "tell me about system audit in 2079 directive"
print("Query:", q)
translated = app.expand_query_crosslingual(q, app.groq_client)
print("Translated:", translated)

results = app.hybrid_search(q, app.table, app.embedding_model, translated_terms=translated, top_k=6)
print("\nRetrieved results:")
for r in results:
    print(f"  Source: {r['source']}, Page: {r['page']}, Score: {r['score']}")

