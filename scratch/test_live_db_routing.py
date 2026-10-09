import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
import lancedb
from ask import build_document_year_map, extract_query_years, clean_query_for_search

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')

doc_map = build_document_year_map(tbl)
print("=== LIVE DATABASE DOCUMENT YEAR MAP ===")
for k, v in doc_map.items():
    print(f"  {k} -> {v}")

avail_yrs = set.union(*doc_map.values()) if doc_map else set()

queries = [
    "Can I deposit 2000 rupees in wallet?",
    "What is the fee for Rs. 2500 transfer?",
    "Tell me about rule 2048",
    "tell me about system audit in 2079 directive",
    "Compare system audit between 2079 and 2082",
    "२०८० को परिपत्र अनुसार"
]

print("\n=== LIVE QUERY EVALUATION ===")
for q in queries:
    matched = extract_query_years(q, avail_yrs)
    cleaned = clean_query_for_search(q, matched) if len(matched) == 1 else q
    print(f"Q: '{q}'")
    print(f"   Matched Years: {matched}")
    print(f"   Cleaned Query: '{cleaned}'")
    if len(matched) == 1:
        doc = [d for d, yrs in doc_map.items() if list(matched)[0] in yrs]
        print(f"   🎯 Auto-routed to: {doc[0] if doc else None}")
    elif len(matched) > 1:
        print(f"   📊 Multi-year comparative: Open search across all documents!")
    else:
        print(f"   🛡️ Normal query (amount/rule preserved)")
    print()
