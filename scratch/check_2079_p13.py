import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
import lancedb
from ask import decode_preeti_text

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')

p13 = tbl.search().where("source = 'directive_2079.pdf' AND page = 13").to_pandas()
for _, r in p13.iterrows():
    print(decode_preeti_text(r['text']))

