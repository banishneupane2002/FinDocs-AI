import sys, lancedb
sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')

res = table.search([0.0]*384).where("source == 'Annual_Report_2025.pdf' and page == 33").limit(5).to_pandas()
print(f"Found {len(res)} chunks on page 33 of Annual_Report_2025.pdf:")
for i, r in res.iterrows():
    print(f"--- Chunk {i+1} ---")
    print(r['text'])

