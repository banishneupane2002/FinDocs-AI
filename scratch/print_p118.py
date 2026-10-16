import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')

df = tbl.search().where("source = 'Unified_directive_2082.pdf' AND page = 118").select(['page', 'text']).to_pandas()
for _, r in df.iterrows():
    print(r['text'])

