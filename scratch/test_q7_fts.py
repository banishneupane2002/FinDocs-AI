import lancedb
db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

q7_fts = "Credit Shock C1 15 percent performing loans Substandard 10 DBs CAR"
res = t.search(q7_fts).limit(5).to_pandas()
for _, r in res.iterrows():
    print(r['source'], f"Page {r['page']}", r['text'][:80].replace('\n', ' '))

