import os, sys

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search, expand_query_crosslingual
from core.routing import build_document_year_map, extract_query_years, clean_query_for_search

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db = lancedb.connect('lancedb_data')
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

q = "show me list of finance companies"
print("Query:", q)

doc_year_map = build_document_year_map(table)
available_years = set.union(*doc_year_map.values()) if doc_year_map else set()

matched_years = extract_query_years(q, available_years)
effective_doc = None
if len(matched_years) == 1:
    target_yr = list(matched_years)[0]
    matching_docs = [d for d, yrs in doc_year_map.items() if target_yr in yrs]
    if matching_docs:
        effective_doc = matching_docs if len(matching_docs) > 1 else matching_docs[0]

results = hybrid_search(
    user_query=q,
    table=table,
    model=model,
    translated_terms="", # 0 LLM expansion tokens
    selected_doc=effective_doc,
    top_k=6
)

print(f"\nRetrieved {len(results)} chunks:")
found_annex4 = False
for i, r in enumerate(results, 1):
    src = r['source']
    pg = r['page']
    snip = r['text'][:140].replace('\n', ' ')
    print(f"Rank {i}: {src} p.{pg} | {snip}")
    if "Annual_Report_2025.pdf" in src and pg in (22, 23, 83):
        found_annex4 = True

print("\nVerification: Found Annex 4.1 or Table 2.3 list of FCs in top results?", found_annex4)
assert found_annex4, "Failed to retrieve finance companies list from Annual Report 2025"
print("SUCCESS: Annual Report 2025 Finance Companies list retrieved at top ranks!")
