import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')

print("=== Page 118 Chunks ===")
df118 = tbl.search().where("source = 'Unified_directive_2082.pdf' AND page = 118").select(['page', 'text']).to_pandas()
for i, r in df118.iterrows():
    print(f"\n--- Page 118 Chunk {i} ---")
    print(r['text'])

print("\n=== Page 23 Chunks ===")
df23 = tbl.search().where("source = 'Unified_directive_2082.pdf' AND page = 23").select(['page', 'text']).to_pandas()
for i, r in df23.iterrows():
    print(f"\n--- Page 23 Chunk {i} ---")
    print(r['text'])
