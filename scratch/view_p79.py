import lancedb
db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

p79 = t.search().where("source = 'Annual_Report_2025.pdf' AND page = 79").to_pandas()
for _, r in p79.iterrows():
    print(r['text'])

