import sys
import os
sys.path.insert(0, os.path.abspath('.'))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb
from ask import hybrid_search, SentenceTransformer, clean_query_for_search, extract_query_years

db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

q = "what was the atm withdrawal limit in 2080"
matched_years = extract_query_years(q)
clean_q = clean_query_for_search(q, matched_years)
print(f"Original: '{q}', Clean: '{clean_q}'")

res = hybrid_search(clean_q, table, model, selected_doc='directive_2080.pdf', top_k=6)
for i, r in enumerate(res, 1):
    print(f"#{i} {r['source']} Page {r['page']} score {r['score']:.4f}")

