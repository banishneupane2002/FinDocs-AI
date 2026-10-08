import lancedb
db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')
df = t.search('C1 DBs').limit(3).to_pandas()
for _, r in df.iterrows():
    print(r['source'], r['page'], r['text'][:100].replace('\n', ' '))

