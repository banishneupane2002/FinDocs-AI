import lancedb

db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')

chunks = table.search().where("source = 'Unified_directive_2082.pdf' AND page = 75").to_list()
print('Number of chunks on page 75:', len(chunks))
for c in chunks:
    print('--- CHUNK ---')
    print(c['text'])
