import sys, os, time, re, json
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search, expand_query_crosslingual
from core.routing import build_document_year_map, extract_query_years, clean_query_for_search
from core.preeti import decode_preeti_text

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

TEST_CASES = [
    {
        "id": "NEW_Q1_NPL",
        "query": "overall Non-Performing Loan (NPL) ratio of Finance Companies (Class 'C') compared to Commercial Banks in the 2024/25 supervision report?",
        "expansion": "NPL ratio, Gross NPL, Table 1.2, Non-Performing Loans, Financial Soundness Indicators",
        "expected_doc": "Annual_Report_2025.pdf",
        "expected_keywords": ["11.34%", "5.04%", "NPL", "Finance"]
    },
    {
        "id": "NEW_Q2_BRANCHES",
        "query": "वाणिज्य बैंकहरू र विकास बैंकहरूको कुल शाखा संख्या (Total Branches) कति पुगेको छ?",
        "expansion": "Total branches, number of branches, Table 1.1, Structure of Financial Sector",
        "expected_doc": "Annual_Report_2025.pdf",
        "expected_keywords": ["branches", "1132", "1423", "Table 1.1"]
    },
    {
        "id": "NEW_Q3_COOLING",
        "query": "cooling-off period required for blacklisted agent",
        "expansion": "आधिकारिक प्रतिनिधि, एजेन्ट, कालोसूची, फुकुवा भएको कम्तीमा ३ वर्ष पूरा भएको, ३ वर्ष, स्वघोषणा",
        "expected_doc": "directive_2082.pdf",
        "expected_page": 35,
        "expected_keywords": ["कालोसूची", "३ वर्ष", "फुकुवा"]
    },
    {
        "id": "NEW_Q4_STR_TTR",
        "query": "What is the deadline and threshold for filing a (STR) and a (TTR) to the (FIU)?",
        "expansion": "सीमा कारोबार, त्त्च्, १० लाख, १५ दिन, शंकास्पद कारोबार, क्त्च्, ३ दिन, goAML",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_keywords": ["१० लाख", "१५ दिन", "३ दिन"]
    }
]

print("=" * 80)
print("  VERIFYING TARGET RETRIEVAL & CONTEXT ACCURACY FOR NEW BENCHMARKS")
print("=" * 80)

doc_year_map = build_document_year_map(table)
available_years = set.union(*doc_year_map.values()) if doc_year_map else set()

for item in TEST_CASES:
    qid = item["id"]
    query = item["query"]
    expansion = item["expansion"]
    
    # 1. Routing check
    matched_years = extract_query_years(query, available_years)
    effective_doc = "All Documents"
    if matched_years:
        candidate_docs = set()
        for yr in matched_years:
            for d, yrs in doc_year_map.items():
                if yr in yrs:
                    candidate_docs.add(d)
        if len(candidate_docs) == 1:
            effective_doc = list(candidate_docs)[0]
    
    clean_q = clean_query_for_search(query, matched_years) if effective_doc != "All Documents" else query
    
    # 2. Hybrid search
    results = hybrid_search(clean_q, table, model, translated_terms=expansion, selected_doc=effective_doc, top_k=8)
    
    # 3. Context building (production compact)
    seen_pages = set()
    full_page_context = []
    total_chars = 0
    pages_included = []

    for r in results:
        sp = (r['source'], r['page'])
        if sp not in seen_pages:
            seen_pages.add(sp)
            try:
                page_recs = table.search().where(f"source = '{r['source']}' AND page = {r['page']}").select(["text"]).to_pandas()
                page_text = "\n".join(page_recs['text'].tolist())
            except Exception:
                page_text = r.get('text', '')

            page_text = decode_preeti_text(page_text)
            full_page_context.append(f"\n[कागजात: {r['source']} | पृष्ठ: {r['page']}]:\n{page_text}\n")
            pages_included.append(f"{r['source']} P{r['page']}")
            total_chars += len(page_text)
            if len(seen_pages) >= 5 or total_chars > 12000:
                break

    context_str = "\n".join(full_page_context)
    normalized_context = re.sub(r'\s+', ' ', context_str)
    
    # Check expected doc and keywords
    has_expected_doc = any(item.get("expected_doc", "") in p for p in pages_included)
    found_keywords = [kw for kw in item["expected_keywords"] if kw.lower() in normalized_context.lower()]
    missing_keywords = [kw for kw in item["expected_keywords"] if kw.lower() not in normalized_context.lower()]
    
    pass_status = "PASS" if has_expected_doc and len(found_keywords) >= 2 else "FAIL"
    
    print(f"\n[{pass_status}] {qid}")
    print(f"  Query: {query}")
    print(f"  Clean Query: {clean_q}")
    print(f"  Effective Doc: {effective_doc} | Matched Years: {matched_years}")
    print(f"  Retrieved Pages: {', '.join(pages_included[:5])}")
    print(f"  Total Chars: {total_chars} (~{total_chars//5} tokens)")
    print(f"  Keywords Found: {found_keywords}")
    if missing_keywords:
        print(f"  Keywords Missing: {missing_keywords}")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)

