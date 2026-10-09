import lancedb
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

print("=== ALL CHUNKS OF DIRECTIVE 2080 PAGE 18 ===")
d2080 = t.search().where("source = 'directive_2080.pdf' AND page = 18").to_pandas()
for _, r in d2080.iterrows():
    print(r['text'])

