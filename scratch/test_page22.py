import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
import lancedb

db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')

df = table.search([0.0]*384).where("source == 'directive_1.pdf' and page == 22").limit(5).to_pandas()
print("Found on page 22 of directive_1:", len(df))
for i, r in df.iterrows():
    print(f"--- Chunk {i+1} ---")
    print(r['text'])

