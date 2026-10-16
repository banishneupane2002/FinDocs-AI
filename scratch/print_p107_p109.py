import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import lancedb

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')

df = table.search().where("source = 'Unified_directive_2082.pdf' AND page IN (107, 108, 109)").select(['page', 'text']).to_pandas()
for _, r in df.iterrows():
    print(f"=== Page {r['page']} ===")
    print(r['text'])

