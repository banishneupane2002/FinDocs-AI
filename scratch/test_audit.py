import lancedb
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

df = t.search().to_pandas()
for _, r in df.iterrows():
    if 'directive' in r['source'] and ('Audit' in r['text'] or 'ब्गमष्त' in r['text'] or 'क्थकतभफ' in r['text'] or 'परीक्षण' in r['text']):
        for line in r['text'].split('\n'):
            if 'Audit' in line or 'ब्गमष्त' in line or ('परीक्षण' in line and '१ वर्ष' in line):
                print(f"{r['source']} p.{r['page']}: {line}")

