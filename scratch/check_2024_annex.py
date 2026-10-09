import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import lancedb

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')

df = tbl.search().where("source = 'Annual_Report_2024.pdf'").to_pandas()
print(f"Total chunks in Annual_Report_2024.pdf: {len(df)}")
matches = df[df['text'].str.contains("Statement of Financial Position|Annex 3", case=False, na=False)]
for _, r in matches.head(10).iterrows():
    print(f"Page {r['page']}: {r['text'][:250]}\n" + "-"*40)

