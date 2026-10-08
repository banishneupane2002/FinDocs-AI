import lancedb
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

print("--- DIRECTIVE 1 PAGE 20 ---")
d1 = t.search().where("source = 'directive_1.pdf' AND page = 20").to_pandas()
for _, r in d1.iterrows():
    print(r['text'])

print("\n--- DIRECTIVE 3 PAGE 18 ---")
d3 = t.search().where("source = 'directive_3.pdf' AND page = 18").to_pandas()
for _, r in d3.iterrows():
    print(r['text'])

