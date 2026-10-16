import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')

q = "residential properties risk weight Capital Adequacy"
res = tbl.search(q).limit(10).to_pandas()
print("Top 10 hits for:", q)
for rank, (_, r) in enumerate(res.iterrows(), 1):
    p225_flag = " *** FOUND PAGE 225! ***" if r['page'] == 225 and '2082' in r['source'] else ""
    print(f"  {rank}: {r['source']} page {r['page']} score={r['_score']:.2f}{p225_flag}")

