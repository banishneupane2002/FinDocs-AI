import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
import lancedb
from sentence_transformers import SentenceTransformer
from ask import (
    build_document_year_map,
    extract_query_years,
    hybrid_search
)

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
doc_map = build_document_year_map(tbl)

q = 'Compare system audit between 2079 and 2082'
avail_yrs = set.union(*doc_map.values()) if doc_map else set()
matched_years = extract_query_years(q, avail_yrs)
print('Matched Years:', matched_years)

results = hybrid_search(q, tbl, model, translated_terms='System Audit, प्रणाली परीक्षण', selected_doc=None, top_k=6)

target_docs = set()
for yr in matched_years:
    for d, yrs in doc_map.items():
        if yr in yrs:
            target_docs.add(d)
by_doc = {d: [] for d in target_docs}
for item in results:
    if item['source'] in by_doc:
        by_doc[item['source']].append(item)
interleaved = []
for i in range(3):
    for d in sorted(by_doc.keys()):
        if i < len(by_doc[d]):
            interleaved.append(by_doc[d][i])

print('Interleaved Pages in Context:')
seen = set()
for item in interleaved:
    sp = (item['source'], item['page'])
    if sp not in seen:
        seen.add(sp)
        print(f"  * {item['source']} Page {item['page']}")

