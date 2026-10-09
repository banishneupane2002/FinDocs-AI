import sys
import os
sys.path.insert(0, os.path.abspath('.'))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb
from sentence_transformers import SentenceTransformer
from ask import (
    hybrid_search, 
    extract_meaningful_keywords, 
    detect_document_years, 
    build_document_year_map, 
    extract_query_years, 
    prioritize_matching_document,
    clean_query_for_search,
    decode_preeti_text
)

db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

doc_year_map = build_document_year_map(table)
available_years = set.union(*doc_year_map.values()) if doc_year_map else set()

test_queries = [
    "what amount at max could be withdrawn from atm",
    "एटीएमबाट अधिकतम कति रकम झिक्न सकिन्छ?",
    "what was the atm withdrawal limit in 2080",
    "what are parameters to categorize bad loans",
    "What is the daily and monthly cash deposit limit in a wallet through an authorized agent?"
]

print("=" * 70)
print("OFFLINE RETRIEVAL VERIFICATION (0 LLM TOKENS)")
print("=" * 70)

for q in test_queries:
    matched_years = extract_query_years(q, available_years)
    effective_doc = None
    if len(matched_years) == 1:
        target_yr = list(matched_years)[0]
        matching_docs = [d for d, yrs in doc_year_map.items() if target_yr in yrs]
        if matching_docs:
            effective_doc = prioritize_matching_document(target_yr, matching_docs)

    search_query = clean_query_for_search(q, matched_years) if effective_doc else q
    results = hybrid_search(search_query, table, model, selected_doc=effective_doc, top_k=3)

    print(f"\nQuery: '{q}'")
    if effective_doc:
        print(f"  -> Routed to: {effective_doc} (Target Year: {list(matched_years)[0]})")
    else:
        print("  -> Unanchored (Searching All Documents with prevailing recency boost)")

    for rank, item in enumerate(results, 1):
        print(f"  #{rank} [{item['source']} Page {item['page']}] Score: {item['score']:.4f}")
        clean_text = decode_preeti_text(item['text'][:140]).replace('\n', ' ')
        print(f"      {clean_text}...")

print("\n" + "=" * 70)
print("ALL RETRIEVAL TESTS COMPLETED SUCCESSFULLY!")
print("=" * 70)
