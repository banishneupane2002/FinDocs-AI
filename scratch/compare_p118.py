import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import lancedb

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')

p118_81 = table.search().where("source = 'Unified_directive_2081.pdf' AND page = 118").select(['text']).to_pandas()
p118_82 = table.search().where("source = 'Unified_directive_2082.pdf' AND page = 118").select(['text']).to_pandas()

print("--- 2081 P118 ---")
for _, r in p118_81.iterrows():
    print(r['text'][:300])

print("\n--- 2082 P118 ---")
for _, r in p118_82.iterrows():
    print(r['text'][:300])

