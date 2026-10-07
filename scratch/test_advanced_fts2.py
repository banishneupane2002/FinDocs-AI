import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
import lancedb, re
from sentence_transformers import SentenceTransformer
import ask

db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')

q = "एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?"
kw = ask.extract_meaningful_keywords(q)
print("Extracted keywords:", kw)
fts_kw_str = " ".join(kw)
print("FTS query string:", fts_kw_str)

res = table.search(fts_kw_str).limit(5).to_pandas()
for i, r in enumerate(res.iterrows(), 1):
    row = r[1]
    print(f" {i}. [{row['source']} P{row['page']}] | {row['text'][:90].replace(chr(10), ' ')}")

