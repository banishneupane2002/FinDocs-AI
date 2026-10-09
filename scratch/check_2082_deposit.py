import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
import lancedb
from ask import decode_preeti_text

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')

df = tbl.search().where("source = 'directive_2082.pdf'").to_pandas()
matches = df[df['text'].str.contains('एजेन्ट|नगद|वालेट|जम्मा', case=False, na=False)]
print(f"Total matching chunks in directive_2082.pdf: {len(matches)}")
for _, r in matches.iterrows():
    dec = decode_preeti_text(r['text'])
    if any(w in dec for w in ['२५,०००', '५०,०००', '१,००,०००', 'प्रतिदिन', 'प्रतिमहिना', 'नगद जम्मा']):
        print(f"Page {r['page']}: {dec[:300]}\n" + "-"*40)
