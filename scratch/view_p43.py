import lancedb
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

p43 = t.search().where("source = 'Annual_Report_2025.pdf' AND page = 43").to_pandas()
for _, r in p43.iterrows():
    print(r['text'][:1000])

