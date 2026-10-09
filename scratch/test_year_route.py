import sys
import os
import re
import unicodedata
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
import lancedb
from sentence_transformers import SentenceTransformer

from test_improved_atm import hybrid_search_test

db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')
model = SentenceTransformer('all-MiniLM-L6-v2')

q2080 = "what was the atm withdrawal limit in 2080"
# Filter to directive_2080.pdf as app.py does
d2080_results = hybrid_search_test(q2080, table, model, top_k=4)
# Also test with where clause on directive_2080.pdf
s_pri = {}
from test_improved_atm import extract_meaningful_keywords
kw_pri = extract_meaningful_keywords(q2080)
clean_pri_fts = " ".join([w for w in kw_pri if len(w) > 1])
search_fts = table.search(clean_pri_fts).where("source = 'directive_2080.pdf'")
print("\n--- Directed search on directive_2080.pdf for 2080 query ---")
for rank, (_, row) in enumerate(search_fts.limit(4).to_pandas().iterrows(), 1):
    print(f"#{rank} {row['source']} Page {row['page']}")

