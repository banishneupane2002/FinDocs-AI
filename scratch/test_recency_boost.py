import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
import lancedb
from sentence_transformers import SentenceTransformer
from ask import (
    build_document_year_map,
    extract_query_years,
    prioritize_matching_document,
    clean_query_for_search,
    hybrid_search
)

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

doc_map = build_document_year_map(tbl)

q = "एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?"
translated = "agent wallet cash deposit limit"

# Test standard search
res = hybrid_search(q, tbl, model, translated_terms=translated, top_k=6)
print("Standard Search (No Recency Boost):")
for r in res[:4]:
    print(f"  {r['source']} P{r['page']} (Score: {r['score']:.4f})")

# Now test with recency boost for directives
print("\nWith Directive Recency Preference:")
k_const = 30
# Re-rank with recency
boosted = []
for r in res:
    src = r['source']
    yrs = doc_map.get(src, {2000})
    max_yr = max(yrs) if yrs else 2000
    # Add recency boost for directives if between 2078 and 2082
    recency_bonus = 0.0
    if 'directive' in src and 2078 <= max_yr <= 2085:
        recency_bonus = (max_yr - 2078) * 0.003
    elif 'Annual_Report' in src and 2020 <= max_yr <= 2030:
        recency_bonus = (max_yr - 2020) * 0.003
    boosted.append({
        'source': r['source'],
        'page': r['page'],
        'score': r['score'] + recency_bonus
    })

boosted.sort(key=lambda x: x['score'], reverse=True)
for r in boosted[:4]:
    print(f"  {r['source']} P{r['page']} (Score: {r['score']:.4f})")

