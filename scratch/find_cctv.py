import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import lancedb

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')

df = tbl.search().to_pandas()
cctv_matches = df[df['text'].str.contains('सीसीटीभी|ऋऋत्ख्|क्यामेरा|CCTV', case=False, na=False)]
print('Found CCTV chunks:', len(cctv_matches))
for _, r in cctv_matches.iterrows():
    if any(w in r['text'] for w in ['९०', '90', 'नब्बे', 'दिन', 'महिना', 'back', 'backup']):
        print(f"{r['source']} P{r['page']}: {r['text'][:200]}\n" + "-"*40)

