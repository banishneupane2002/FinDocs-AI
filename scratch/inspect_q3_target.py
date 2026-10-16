import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')

df = tbl.search().where("source = 'Unified_directive_2082.pdf' AND page <= 20").select(['page', 'text']).to_pandas()
for _, r in df.iterrows():
    txt = r['text']
    if 'कालोसूची' in txt and ('खराब' in txt or '१००' in txt or 'वर्गीकरण' in txt or 'नोक्सानी' in txt):
        print(f"--- Page {r['page']} ---")
        for line in txt.split('\n'):
            if 'कालोसूची' in line or 'खराब' in line or '१००' in line:
                print(f"  {line.strip()}")

