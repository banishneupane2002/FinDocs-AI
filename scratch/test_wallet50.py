import lancedb
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

df = t.search().to_pandas()
for _, r in df.iterrows():
    if 'directive' in r['source'] and 'वालेट' in r['text'] and ('५०' in r['text'] or 'बैंक खाता' in r['text']):
        for line in r['text'].split('\n'):
            if '५०' in line or 'बैंक खाता' in line:
                print(f"{r['source']} p.{r['page']}: {line}")

