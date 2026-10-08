import lancedb
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

df = t.search().to_pandas()
print(f"Total chunks: {len(df)}")

# Find chunks with 'नब्बे' or '९०' in directives
for _, r in df.iterrows():
    if 'directive' in r['source'] and ('नब्बे' in r['text'] or '९०' in r['text']):
        for line in r['text'].split('\n'):
            if 'नब्बे' in line or '९०' in line:
                print(f"{r['source']} p.{r['page']}: {line}")
