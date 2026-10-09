import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import lancedb

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')

df = tbl.search("Statement of Financial Position Development Banks").where("source = 'Annual_Report_2024.pdf'").limit(5).to_pandas()
print(f"Found {len(df)} chunks in Annual_Report_2024.pdf:")
for _, r in df.iterrows():
    print(f"Page {r['page']}: {r['text'][:150]}...\n")

