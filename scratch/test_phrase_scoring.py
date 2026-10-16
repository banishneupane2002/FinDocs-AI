import os, sys, lancedb
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = r'C:\Users\Banish\RAG_FILESYSTEM'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')
from core.preeti import decode_preeti_text

df = table.search().where("source = 'Unified_directive_2082.pdf' AND page = 172").select(['text']).to_pandas()
raw_txt = '\n'.join(df['text'].tolist())
txt = decode_preeti_text(raw_txt)

lines = txt.split('\n')
for i, l in enumerate(lines):
    if "दिनभित्र" in l:
        for j in range(max(0, i-3), min(len(lines), i+4)):
            print(f"{j}: {lines[j]}")

