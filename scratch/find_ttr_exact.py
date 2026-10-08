import lancedb, sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

# Find exact page where '१० लाख' and '१५ दिन' occur together
df = t.search().where("text LIKE '%१० लाख%' AND text LIKE '%१५ दिन%'").to_pandas()
for _, r in df.iterrows():
    print(r['source'], f"Page {r['page']}")
    for l in r['text'].split('\n'):
        if '१० लाख' in l or '१५ दिन' in l or 'goAML' in l or 'नयब्ःी' in l:
            print("  ", l)

