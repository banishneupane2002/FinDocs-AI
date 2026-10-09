import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
import os
import lancedb
from sentence_transformers import SentenceTransformer
from groq import Groq
from ask import (
    build_document_year_map,
    extract_query_years,
    prioritize_matching_document,
    clean_query_for_search,
    expand_query_crosslingual,
    hybrid_search,
    decode_preeti_text
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.strip().split("=", 1)[1].strip()

client = Groq(api_key=GROQ_API_KEY)
db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

doc_map = build_document_year_map(tbl)
avail_yrs = set.union(*doc_map.values()) if doc_map else set()

test_queries = [
    "मलाई जुलाई २०२५ को विकास बैंकहरूको एकीकृत वित्तीय स्थितिको विवरण देखाउनुहोस्।",
    "Statement of Financial Position of DBs show me of july 2024"
]

for q in test_queries:
    print("\n" + "="*60)
    print("USER QUERY:", q)
    matched = extract_query_years(q, avail_yrs)
    print("MATCHED YEARS:", matched)
    
    effective_doc = None
    if len(matched) == 1:
        target_yr = list(matched)[0]
        matching_docs = [d for d, yrs in doc_map.items() if target_yr in yrs]
        if matching_docs:
            effective_doc = prioritize_matching_document(target_yr, matching_docs)
            print(f"🎯 Auto-routed to: {effective_doc} (Target Year: {target_yr})")
            
    search_q = clean_query_for_search(q, matched) if effective_doc else q
    print("CLEANED SEARCH QUERY:", search_q)
    
    translated_terms = expand_query_crosslingual(search_q, client)
    print("TRANSLATED TERMS:", translated_terms)
    
    results = hybrid_search(search_q, tbl, model, translated_terms=translated_terms, selected_doc=effective_doc, top_k=4)
    print("TOP RETRIEVED PAGES:")
    for r in results[:3]:
        print(f"  * {r['source']} Page {r['page']} (Score: {r['score']:.4f})")

