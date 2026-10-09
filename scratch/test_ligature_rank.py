import sys
import os
sys.path.insert(0, os.path.abspath('.'))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb
from ask import SentenceTransformer

db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')

fts_query = "डेबिट कार्ड भुक्तानी भुत्तफानी नगद झिक्ने भिफक्ने अधिकतम सीमा प्रतिकारोबार प्रतिदिन"
res = table.search(fts_query).where("source = 'directive_2080.pdf'").limit(5).to_pandas()

print("--- FTS RESULTS WITH LIGATURE TOKENS ---")
for i, (_, r) in enumerate(res.iterrows(), 1):
    print(f"#{i} {r['source']} Page {r['page']}")

