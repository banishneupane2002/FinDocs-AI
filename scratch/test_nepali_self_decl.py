import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import app

q_nepali = "स्वःघोषणासम्बन्धी व्यवस्था बारेमा भन्नुहोस"
res_nepali = app.hybrid_search(q_nepali, app.table, app.embedding_model, top_k=4)
print("=== Nepali Query Results ===")
for r in res_nepali:
    print(f"  Source: {r['source']}, Page: {r['page']}, Score: {r['score']}")

