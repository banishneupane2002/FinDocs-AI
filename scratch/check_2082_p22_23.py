import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
import lancedb
from ask import decode_preeti_text

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')

p22 = tbl.search().where("source = 'directive_2082.pdf' AND (page = 22 OR page = 23)").to_pandas()
for _, r in p22.iterrows():
    print(f"Page {r['page']}:")
    print(decode_preeti_text(r['text']))
    print("="*50)

