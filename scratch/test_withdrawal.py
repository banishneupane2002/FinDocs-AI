import lancedb
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

df = t.search().to_pandas()
for _, r in df.iterrows():
    if 'directive' in r['source'] and ('झिक्ने' in r['text'] or 'झिक्न' in r['text']):
        for line in r['text'].split('\n'):
            if 'प्रतिदिन' in line or 'दैनिक' in line or 'सीमा' in line:
                print(f"{r['source']} p.{r['page']}: {line}")

