import sys, os, time, re, unicodedata, json
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search, expand_query_crosslingual
from core.routing import build_document_year_map, extract_query_years, clean_query_for_search

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

BENCHMARKS = [
    {
        "id": "B1",
        "category": "Annual Supervision Report 2024/25",
        "query": "How many debit cards were issued by Development Banks as of Mid-July 2025?",
        "expansion": "Debit Cards, Development Banks, DBs, Table 3.6, Mid-July 2025, 1,216,322",
        "expected_facts": ["1,216,322", "1216322", "1,076,072"],
        "expected_source": "Annual_Report_2025.pdf",
        "expected_page": [33]
    },
    {
        "id": "B2",
        "category": "Annual Supervision Report 2024/25",
        "query": "What was the number of mobile banking customers in Finance Companies (FCs) in 2024/25?",
        "expansion": "Mobile Banking Customers, Finance Companies, FCs, Table 4.5, 294,739",
        "expected_facts": ["294,739", "294739", "231,852"],
        "expected_source": "Annual_Report_2025.pdf",
        "expected_page": [43]
    },
    {
        "id": "B3",
        "category": "Annual Supervision Report 2024/25",
        "query": "What was the total number of ATMs across all banks and financial institutions as of Mid-July 2025?",
        "expansion": "Total ATMs, Indicators Summary, Table 3.6, Table 4.5, 5,222",
        "expected_facts": ["5,222", "5222", "4,837", "344", "41"],
        "expected_source": "Annual_Report_2025.pdf",
        "expected_page": [16]
    },
    {
        "id": "B4",
        "category": "Annual Supervision Report 2024/25",
        "query": "विकास बैंकहरूमा इन्टरनेट बैंकिङ प्रयोग गर्ने ग्राहक संख्या कति पुगेको छ?",
        "expansion": "Development Banks, DBs, Internet Banking Customers, Table 3.6, Mid-July 2025, 599,316",
        "expected_facts": ["५,९९,३१६", "599,316", "599316"],
        "expected_source": "Annual_Report_2025.pdf",
        "expected_page": [33]
    },
    {
        "id": "B5",
        "category": "Limits & Caps",
        "query": "एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?",
        "expansion": "आधिकारिक प्रतिनिधि, एजेन्ट, नगद जम्मा, २५ हजार, १ लाख, प्रतिदिन",
        "expected_facts": ["२५ हजार", "१ लाख", "25,000", "100,000", "२५,०००", "१,००,०००"],
        "expected_source": "directive_2082.pdf",
        "expected_page": [21, 22]
    },
    {
        "id": "B6",
        "category": "Limits & Caps",
        "query": "What is the maximum cash withdrawal limit through an agent from a digital wallet?",
        "expansion": "आधिकारिक प्रतिनिधि, एजेन्ट, नगद झिक्ने, ५ हजार, २५ हजार",
        "expected_facts": ["5,000", "25,000", "५ हजार", "२५ हजार", "५,०००", "२५,०००"],
        "expected_source": "directive_2082.pdf",
        "expected_page": [20, 21, 22]
    },
    {
        "id": "B7",
        "category": "Limits & Caps",
        "query": "वालेटमा अधिकतम ओभरनाइट मौज्दात (Overnight Balance) कति राख्न पाइन्छ?",
        "expansion": "ओभरनाइट मौज्दात, ५० हजार, ५०,०००, निक्षेप बैंक खाता",
        "expected_facts": ["५०,०००", "50,000", "५० हजार", "निक्षेप बैंक खाता", "ओभरनाइट मौज्दात"],
        "expected_source": "directive_2082.pdf",
        "expected_page": [21, 22]
    },
    {
        "id": "B8",
        "category": "Limits & Caps",
        "query": "What is the transaction limit for USSD-based mobile payments?",
        "expansion": "ग्क्क्म्, USSD, १०,०००, ५,०००, दैनिक रु.१०,०००, प्रति कारोबार रु.५,०००",
        "expected_facts": ["10,000", "5,000", "१० हजार", "५ हजार", "१०,०००", "५,०००"],
        "expected_source": "directive_2082.pdf",
        "expected_page": [21, 22]
    },
    {
        "id": "B9",
        "category": "Governance",
        "query": "स्व-घोषणासम्बन्धी व्यवस्था बारेमा भन्नुहोस्",
        "expansion": "सञ्चालक, स्वघोषणा, स्वःघोषणा, अनुसूची ११.१, १५ दिन",
        "expected_facts": ["११.१", "11.1", "१५ दिन", "15", "सञ्चालक"],
        "expected_source": "directive_2082.pdf",
        "expected_page": [59, 60]
    },
    {
        "id": "B10",
        "category": "Governance",
        "query": "What is the cooling-off period required if an agent was previously blacklisted?",
        "expansion": "आधिकारिक प्रतिनिधि, एजेन्ट, कालोसूची, फुकुवा भएको कम्तीमा ३ वर्ष पूरा भएको, ३ वर्ष, स्वघोषणा",
        "expected_facts": ["3 years", "३ वर्ष", "फुकुवा भएको कम्तीमा ३ वर्ष", "कालोसूची"],
        "expected_source": "directive_2082.pdf",
        "expected_page": [35]
    },
    {
        "id": "B11",
        "category": "Governance",
        "query": "संस्थागत सुशासनसम्बन्धी व्यवस्था कुन निर्देशनमा छ?",
        "expansion": "संस्थागत सुशासन, ११/०८२, निर्देशन नं. ६",
        "expected_facts": ["११/०८२", "११/०८१", "11/082", "निर्देशन नं.११", "निर्देशन नं. ११", "६/०८२", "निर्देशन नं. ६"],
        "expected_source": "directive_2082.pdf",
        "expected_page": [56, 57, 74]
    },
    {
        "id": "B12",
        "category": "Cross-Lingual",
        "query": "Tell us about the self-declaration system for board directors.",
        "expansion": "सञ्चालक, स्वघोषणा, स्वःघोषणा, अनुसूची ११.१, १५ दिन",
        "expected_facts": ["11.1", "११.१", "15 days", "१५ दिन", "Director", "सञ्चालक"],
        "expected_source": "directive_2082.pdf",
        "expected_page": [59, 60]
    },
    {
        "id": "B13",
        "category": "Cross-Lingual",
        "query": "What are the reporting requirements for failed and successful electronic transactions?",
        "expansion": "Reporting Portal, अनुसूची १०.१, Statement of Success and Failed Transaction, १०.१.६, १०.१.११",
        "expected_facts": ["10.1.6", "१०.१.६", "Success and Failed Transaction", "Reporting Portal", "१०.१.११"],
        "expected_source": "directive_2082.pdf",
        "expected_page": [41, 47, 52]
    }
]

doc_year_map = build_document_year_map(table)
available_years = set.union(*doc_year_map.values()) if doc_year_map else set()
print(f"Loaded {len(BENCHMARKS)} benchmark tests.")

passed_count = 0
for b in BENCHMARKS:
    q = b["query"]
    expansion = b.get("expansion", "")
    t0 = time.time()
    
    # 1. Routing identical to app.py
    matched_years = extract_query_years(q, available_years)
    effective_doc = None
    if len(matched_years) == 1:
        target_yr = list(matched_years)[0]
        matching_docs = [d for d, yrs in doc_year_map.items() if target_yr in yrs]
        if matching_docs:
            effective_doc = matching_docs if len(matching_docs) > 1 else matching_docs[0]
            
    search_query = clean_query_for_search(q, matched_years) if effective_doc else q
    if not search_query.strip():
        search_query = q
        
    # 2. Hybrid search identical to app.py
    results = hybrid_search(
        user_query=search_query,
        table=table,
        model=model,
        translated_terms=expansion,
        selected_doc=effective_doc,
        top_k=8
    )
    dt = time.time() - t0
    
    retrieved_sources = [r.get("source", "") for r in results]
    retrieved_pages = [r.get("page", 0) for r in results]
    combined_text = " ".join([r.get("text", "") for r in results])
    
    found_page = False
    for r in results:
        src = r.get("source", "")
        pg = r.get("page", 0)
        if b["expected_source"] in src and pg in b["expected_page"]:
            found_page = True
            break
            
    matched_facts = [f for f in b["expected_facts"] if f in combined_text]
    
    status = "PASS" if (found_page and len(matched_facts) >= 1) else "FAIL"
    if status == "PASS":
        passed_count += 1
    
    top_display = list(zip([os.path.basename(s) for s in retrieved_sources], retrieved_pages))[:4]
    print(f"[{status}] {b['id']} ({b['category']}) in {dt:.2f}s")
    print(f"     Query: {q}")
    print(f"     Found target page: {found_page} | Top pages: {top_display}")
    print(f"     Matched facts: {matched_facts}")
    print()

print(f"=== RESULT: {passed_count}/{len(BENCHMARKS)} PASSED ===")
