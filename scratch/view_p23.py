import lancedb
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

df = t.search().where("source = 'directive_1.pdf' AND page = 23").to_pandas()
for _, r in df.iterrows():
    print(r['text'])
    print("="*40)

