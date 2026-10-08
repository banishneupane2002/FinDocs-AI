import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import app

q = "Tell us about the self-declaration system."
print("User question:", q)
translated = app.expand_query_crosslingual(q, app.groq_client)
print("Translated terms:", repr(translated))

res = app.hybrid_search(q, app.table, app.embedding_model, translated_terms=translated, top_k=6)
print("\nRetrieved chunks:")
for r in res:
    print(f"  Source: {r['source']}, Page: {r['page']}, Score: {r['score']}")
    print("  Snippet:", r['text'][:150].strip())
