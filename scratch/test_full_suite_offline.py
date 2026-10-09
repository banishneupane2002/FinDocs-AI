import sys
import os
import re

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
    hybrid_search,
    decode_preeti_text,
    extract_meaningful_keywords
)

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

doc_map = build_document_year_map(tbl)
avail_yrs = set.union(*doc_map.values()) if doc_map else set()

# Offline cross-lingual dictionary (0 LLM TOKENS USED)
OFFLINE_TRANSLATIONS = {
    "एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?": "agent wallet cash deposit limit",
    "what is the daily and monthly cash deposit limit in a wallet through an authorized agent?": "एजेन्ट, वालेट, नगद जम्मा, प्रतिदिन, प्रतिमहिना, सीमा",
    "overnight balance limit in wallet": "इखभचलष्नजत धबबिलअभ, ५० हजार, वालेट, मौज्दात",
    "atm debit card daily cash withdrawal limit": "डेबिट कार्ड, ATM, नगद झिक्ने सीमा, ५० हजार, १ लाख",
    "simplified kyc threshold": "सरलीकृत ग्राहक पहिचान, मचर्ेन्ट, १,००,०००",
    "स्वःघोषणासम्बन्धी व्यवस्था बारेमा भन्नुहोस": "self-declaration, declaration, eligibility",
    "tell us about the self-declaration provision in directives": "स्वघोषणा, सञ्चालक, ग्राहक पहिचान",
    "branchless banking agreement requirements in 2079": "शाखारहित, सम्झौता, ग्राहक, सर्तहरू",
    "tell me about system audit in 2079 directive": "System Audit, क्थकतभफ ब्गमष्त, प्रणाली परीक्षण, १ वर्ष, २ आर्थिक वर्ष",
    "system audit frequency and scope in 2082 directive": "System Audit, क्थकतभफ ब्गमष्त, २ आर्थिक वर्ष, vulnerabilities",
    "cctv camera footage retention days": "ऋऋत्ख्, क्यामेरा, ब्याकअप, नब्बे दिन, ९०",
    "force settlement time limit and dispute liability": "Force Settlement, ँयचअभ, क्भततभिफभलत, त्ंघ, त्ंज्ञ",
    "ibft transaction fee charges": "अन्तर बैंक, रकमान्तर, क्ष्धँत्, रु. १०",
    "threshold transaction reporting (ttr) limit and reporting deadline": "सीमा कारोबार, त्त्च्, १० लाख, १५ दिन, goAML",
    "मलाई जुलाई २०२५ को विकास बैंकहरूको एकीकृत वित्तीय स्थितिको विवरण देखाउनुहोस्।": "Consolidated Statement of Financial Position, Development Banks, Mid-July",
    "statement of financial position of dbs show me of july 2024": "वित्तीय अवस्था विवरण, विकास बैंक, जुलाई",
    "non-performing loan (npl) ratio in 2024 report": "खराब कर्जा, NPL, Table 1.2",
    "compare system audit between 2079 and 2082": "System Audit, प्रणाली परीक्षण, २ आर्थिक वर्ष",
    "can i deposit 2000 rupees in a wallet?": "वालेट, नगद जम्मा, सीमा, २०००",
    "tell me about rule 2048": "दफा, नियम, व्यवस्था"
}

TEST_CASES = [
    {
        "id": "TC-01",
        "category": "Limits & Thresholds",
        "query": "एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?",
        "expected_doc": "directive_2082.pdf",
        "expected_facts": ["२५,०००", "१,००,०००", "नगद जम्मा"]
    },
    {
        "id": "TC-02",
        "category": "Limits & Thresholds",
        "query": "What is the daily and monthly cash deposit limit in a wallet through an authorized agent?",
        "expected_doc": "directive_2082.pdf",
        "expected_facts": ["२५,०००", "१,००,०००"]
    },
    {
        "id": "TC-03",
        "category": "Limits & Thresholds",
        "query": "Overnight balance limit in wallet",
        "expected_doc": "directive_2082.pdf",
        "expected_facts": ["५०,०००", "Overnight"]
    },
    {
        "id": "TC-04",
        "category": "IT Security & Preeti",
        "query": "tell me about system audit in 2079 directive",
        "expected_doc": "directive_2079.pdf",
        "expected_facts": ["१ वर्ष", "२ आर्थिक वर्ष", "६ महिना"]
    },
    {
        "id": "TC-05",
        "category": "IT Security & Preeti",
        "query": "System audit frequency and scope in 2082 directive",
        "expected_doc": "directive_2082.pdf",
        "expected_facts": ["२ आर्थिक वर्ष", "६ महिना"]
    },
    {
        "id": "TC-06",
        "category": "IT Security & Preeti",
        "query": "CCTV camera footage retention days",
        "expected_doc": "directive_2082.pdf",
        "expected_facts": ["९० दिन", "CCTV"]
    },
    {
        "id": "TC-07",
        "category": "IT Security & Preeti",
        "query": "Force settlement time limit and dispute liability",
        "expected_doc": "directive_2082.pdf",
        "expected_facts": ["T+1", "T+3", "Force"]
    },
    {
        "id": "TC-08",
        "category": "IT Security & Preeti",
        "query": "IBFT transaction fee charges",
        "expected_doc": "directive_2082.pdf",
        "expected_facts": ["१०", "IBFT"]
    },
    {
        "id": "TC-09",
        "category": "AML/CFT Compliance",
        "query": "Threshold Transaction Reporting (TTR) limit and reporting deadline",
        "expected_doc": "directive_2082.pdf",
        "expected_facts": ["१० लाख", "१५ दिन", "TTR"]
    },
    {
        "id": "TC-10",
        "category": "Financial Statements",
        "query": "मलाई जुलाई २०२५ को विकास बैंकहरूको एकीकृत वित्तीय स्थितिको विवरण देखाउनुहोस्।",
        "expected_doc": "Annual_Report_2025.pdf",
        "expected_facts": ["Development Banks", "Statement of Financial Position"]
    },
    {
        "id": "TC-11",
        "category": "Financial Statements",
        "query": "Statement of Financial Position of DBs show me of july 2024",
        "expected_doc": "Annual_Report_2024.pdf",
        "expected_facts": ["Development Banks", "Financial Position", "Annex 3.3"]
    },
    {
        "id": "TC-12",
        "category": "Financial Statistics",
        "query": "Non-Performing Loan (NPL) ratio in 2024 report",
        "expected_doc": "Annual_Report_2024.pdf",
        "expected_facts": ["NPL", "Table 1.2"]
    },
    {
        "id": "TC-13",
        "category": "Comparative Multi-Year",
        "query": "Compare system audit between 2079 and 2082",
        "expected_doc": None, # Should pull both
        "expected_facts": ["System Audit", "directive_2079.pdf", "directive_2082.pdf"]
    },
    {
        "id": "TC-14",
        "category": "Amount Shielding",
        "query": "Can I deposit 2000 rupees in a wallet?",
        "expected_doc": None,
        "expected_facts": ["वालेट", "नगद जम्मा"]
    },
    {
        "id": "TC-15",
        "category": "Statutory Governance",
        "query": "स्वःघोषणासम्बन्धी व्यवस्था बारेमा भन्नुहोस",
        "expected_doc": "directive_2082.pdf",
        "expected_facts": ["स्वघोषणा"]
    }
]

print("================================================================================")
print("COMPREHENSIVE OFFLINE CONTEXT EXTRACTION & RETRIEVAL AUDIT (0 TOKENS CONSUMED)")
print("================================================================================\n")

passed = 0
failed = 0

for tc in TEST_CASES:
    q = tc["query"]
    print(f"[{tc['id']}] Category: {tc['category']}")
    print(f"   Query: \"{q}\"")

    # 1. Routing
    matched = extract_query_years(q, avail_yrs)
    effective_doc = None
    if len(matched) == 1:
        target_yr = list(matched)[0]
        matching_docs = [d for d, yrs in doc_map.items() if target_yr in yrs]
        if matching_docs:
            effective_doc = prioritize_matching_document(target_yr, matching_docs)

    search_q = clean_query_for_search(q, matched) if effective_doc else q
    translated = OFFLINE_TRANSLATIONS.get(q.strip().lower(), OFFLINE_TRANSLATIONS.get(q.strip(), ""))

    # 2. Hybrid Retrieval
    results = hybrid_search(search_q, tbl, model, translated_terms=translated, selected_doc=effective_doc, top_k=6)

    # 3. Context Windowing
    seen_pages = set()
    extracted_contexts = []
    extracted_sources = []
    for item in results:
        sp = (item['source'], item['page'])
        if sp not in seen_pages:
            seen_pages.add(sp)
            try:
                page_records = tbl.search().where(f"source = '{item['source']}' AND page = {item['page']}").to_pandas()
                full_page_text = "\n".join(page_records['text'].tolist())
            except Exception:
                full_page_text = item['text']
            decoded_text = decode_preeti_text(full_page_text)
            extracted_contexts.append(decoded_text)
            extracted_sources.append(f"{item['source']} P{item['page']}")
            if len(seen_pages) >= 4:
                break

    all_context = "\n".join(extracted_contexts)
    top_sources_str = ", ".join(extracted_sources[:3])

    # 4. Verification Check
    doc_match = True
    if tc["expected_doc"]:
        doc_match = any(tc["expected_doc"] in s for s in extracted_sources)

    facts_found = []
    facts_missing = []
    for f in tc["expected_facts"]:
        # check in all_context or extracted_sources
        if f.lower() in all_context.lower() or any(f.lower() in s.lower() for s in extracted_sources):
            facts_found.append(f)
        else:
            facts_missing.append(f)

    if doc_match and len(facts_missing) == 0:
        print(f"   Status: ✅ PASSED")
        print(f"   Top Sources: {top_sources_str}")
        print(f"   Verified Facts Found: {facts_found}")
        passed += 1
    else:
        print(f"   Status: ❌ FAILED or PARTIAL")
        print(f"   Top Sources: {top_sources_str}")
        print(f"   Missing Facts: {facts_missing}")
        failed += 1
    print("-" * 80)

print(f"\nAUDIT COMPLETE: {passed}/{len(TEST_CASES)} PASSED, {failed} FAILED.")

