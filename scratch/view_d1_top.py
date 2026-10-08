import lancedb
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

d1 = t.search().where("source = 'directive_1.pdf' AND page = 20").to_pandas()
print(d1.iloc[0]['text'][:800])

