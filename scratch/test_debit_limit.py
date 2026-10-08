import lancedb
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

df = t.search().to_pandas()
for _, r in df.iterrows():
    if 'directive' in r['source'] and ('डेबिट' in r['text'] or 'Debit' in r['text']) and ('एटीएम' in r['text'] or 'ATM' in r['text'] or 'ब्त्ः' in r['text']):
        for line in r['text'].split('\n'):
            if 'प्रतिदिन' in line or 'दैनिक' in line or 'झिक्न' in line or '५०' in line or '१ लाख' in line:
                print(f"{r['source']} p.{r['page']}: {line}")

