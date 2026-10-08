import lancedb
db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')
df = t.search().where("source = 'Annual_Report_2025.pdf' AND page = 33").to_pandas()
for i, r in df.iterrows():
    print(f"Chunk {i}: length {len(r['text'])}")
    print(r['text'][:200].replace('\n', ' '))

