import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')

q_tokens = ["Margin", "Lending", "मार्जिन", "शेयर", "धितो", "७०", "प्रतिशत"]

q_space = " ".join(q_tokens)
q_or = " OR ".join(q_tokens)

print("--- SPACE QUERY ---")
try:
    res_space = tbl.search(q_space).limit(5).to_pandas()
    for _, r in res_space.iterrows():
        print(f"  {r['source']} P{r['page']} score={r['_score']:.2f}")
except Exception as e:
    print("Space err:", e)

print("\n--- OR QUERY ---")
try:
    res_or = tbl.search(q_or).limit(5).to_pandas()
    for _, r in res_or.iterrows():
        print(f"  {r['source']} P{r['page']} score={r['_score']:.2f}")
except Exception as e:
    print("OR err:", e)

