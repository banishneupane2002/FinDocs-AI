import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import app

q = "system audit"
print("Query:", q)
translated = app.expand_query_crosslingual(q, app.groq_client)
print("Translated:", translated)

results = app.hybrid_search(q, app.table, app.embedding_model, translated_terms=translated, selected_doc="directive_2079.pdf", top_k=6)
print("\nRetrieved results with selected_doc='directive_2079.pdf':")
for r in results:
    print(f"  Source: {r['source']}, Page: {r['page']}, Score: {r['score']}")

