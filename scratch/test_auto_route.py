import sys, os, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import app

q = "tell me about system audit in 2079 directive"

def extract_query_year(query: str) -> int:
    dev_m = re.search(r'२०([७८][०-९])', query)
    if dev_m:
        nep_to_ar = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
        decade_unit = "".join(nep_to_ar.get(c, c) for c in dev_m.group(1))
        return int(f"20{decade_unit}")
    ar_m = re.search(r'\b(20[5-9][0-9]|20[0-4][0-9])\b', query)
    if ar_m:
        return int(ar_m.group(1))
    return 0

target_year = extract_query_year(q)
print(f"Extracted target year automatically: {target_year}")

# Search with automatic year routing
# Find which source corresponds to this year
df = app.table.to_pandas()
matching_sources = [s for s in df['source'].unique() if str(target_year) in s]
print(f"Matching sources in DB: {matching_sources}")

if matching_sources:
    # Auto-routed search: search specifically within the target year's document!
    auto_doc = matching_sources[0]
    translated = app.expand_query_crosslingual(q, app.groq_client)
    res = app.hybrid_search(q, app.table, app.embedding_model, translated_terms=translated, selected_doc=auto_doc, top_k=4)
    print("\n--- Auto-Routed Search Results ---")
    for r in res:
        print(f"  Source: {r['source']}, Page: {r['page']}, Score: {r['score']}")

