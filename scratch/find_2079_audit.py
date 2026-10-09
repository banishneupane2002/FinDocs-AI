import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
import lancedb
from ask import decode_preeti_text

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')

df = tbl.search().where("source = 'directive_2079.pdf'").to_pandas()
for _, r in df.iterrows():
    dec = decode_preeti_text(r['text'])
    if 'system audit' in dec.lower() or 'परीक्षण' in dec or 'audit' in dec.lower():
        print(f"Page {r['page']}: {dec[:300]}\n---")

