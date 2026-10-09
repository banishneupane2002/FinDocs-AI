import lancedb
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

df = t.search().where("source = 'directive_2082.pdf' AND (page = 20 OR page = 21)").to_pandas()
for _, r in df.iterrows():
    print(f"\n================ PAGE {r['page']} (chunk {r.get('chunk_id')}) ================")
    print(r['text'])

