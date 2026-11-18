import sys, os, time, re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search, detect_query_disambiguation, is_specific_query
from core.routing import build_document_year_map, extract_query_years, clean_query_for_search, get_unified_directive_for_page
from core.preeti import decode_preeti_text

print("Connecting to LanceDB...", flush=True)
db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')

print("Loading local SentenceTransformer model (0 API tokens)...", flush=True)
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

doc_year_map = build_document_year_map(table)
available_years = set.union(*doc_year_map.values()) if doc_year_map else set()

# Comprehensive test suite of diverse questions bank staff might ask:
# Formal, casual, layman, English, Nepali, short, long
TEST_QUERIES = [
    # --- Category 1: Loan Classification, NPL & Provisions ---
    {
        "query": "categories of bad loan",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 2,
        "key_phrases": ["खराब", "कमसल", "शंकास्पद"]
    },
    {
        "query": "what are the categories of non performing loans?",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 2,
        "key_phrases": ["कमसल", "शंकास्पद", "खराब"]
    },
    {
        "query": "substandard loan criteria and provision",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 2,
        "key_phrases": ["कमसल", "२५ प्रतिशत", "भाखा नाघेको"]
    },
    {
        "query": "सूक्ष्म निगरानी कर्जाको समयसीमा र नोक्सानी व्यवस्था कति हो?",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 2,
        "key_phrases": ["सूक्ष्म निगरानी", "५ प्रतिशत"]
    },
    {
        "query": "loss loan provisioning percentage",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 2,
        "key_phrases": ["१०० प्रतिशत", "खराब"]
    },

    # --- Category 2: Governance, Allowances & HR ---
    {
        "query": "Directors' Meeting Allowance",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 6,
        "key_phrases": ["बैठक भत्ता", "नियमावली"]
    },
    {
        "query": "allowance of board directors in finance companies",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 6,
        "key_phrases": ["बैठक भत्ता", "सञ्चालक"]
    },
    {
        "query": "सञ्चालक समितिको बैठक भत्ता कति लिन पाइन्छ?",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 6,
        "key_phrases": ["बैठक भत्ता", "नियमावली"]
    },
    {
        "query": "qualification of compliance officer",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 19,
        "key_phrases": ["कार्यान्वयन अधिकारी", "अधिकृत"]
    },
    {
        "query": "कम्प्लायन्स अफिसरको योग्यता के हुनुपर्छ?",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 19,
        "key_phrases": ["कार्यान्वयन अधिकारी", "अधिकृत"]
    },
    {
        "query": "what is the maximum age limit for bank CEO?",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 6,
        "key_phrases": ["६५ वर्ष", "६९ वर्ष", "कार्यकारी प्रमुख"]
    },
    {
        "query": "promoter share lock-in period for finance companies",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 8,
        "key_phrases": ["लकइन", "संस्थापक", "५ वर्ष"]
    },
    {
        "query": "independent director tenure limit",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 6,
        "key_phrases": ["स्वतन्त्र सञ्चालक", "कार्यकाल"]
    },

    # --- Category 3: Digital Banking, Payments & Limits ---
    {
        "query": "mobile banking limit",
        "expected_action": "direct_rag",
        "expected_doc": "directive_2082.pdf",
        "expected_page": [21, 22],
        "key_phrases": ["३ लाख", "प्रतिदिन"]
    },
    {
        "query": "daily fund transfer limit from digital wallet to bank account",
        "expected_action": "direct_rag",
        "expected_doc": "directive_2082.pdf",
        "expected_page": [21, 22],
        "key_phrases": ["२ लाख", "१० लाख"]
    },
    {
        "query": "ATM debit card cash withdrawal daily limit",
        "expected_action": "direct_rag",
        "expected_doc": "directive_2082.pdf",
        "expected_page": [20, 21],
        "key_phrases": ["२५ हजार", "१ लाख"]
    },
    {
        "query": "contactless payment limit without pin",
        "expected_action": "direct_rag",
        "expected_doc": "directive_2082.pdf",
        "expected_page": [21, 22],
        "key_phrases": ["५ हजार", "५,०००"]
    },
    {
        "query": "how much cash can agent deposit in a wallet per day?",
        "expected_action": "direct_rag",
        "expected_doc": "directive_2082.pdf",
        "expected_page": [21, 22],
        "key_phrases": ["२५ हजार", "१ लाख"]
    },
    {
        "query": "USSD payment per transaction and daily cap",
        "expected_action": "direct_rag",
        "expected_doc": "directive_2082.pdf",
        "expected_page": [21, 22],
        "key_phrases": ["५,०००", "१०,०००"]
    },
    {
        "query": "failed transaction claim settlement reversal timeframe",
        "expected_action": "direct_rag",
        "expected_doc": "directive_2082.pdf",
        "expected_page": [30, 31, 32],
        "key_phrases": ["T+1", "T+3", "फर्छ्यौट"]
    },

    # --- Category 4: Regulatory Ratios & Caps ---
    {
        "query": "minimum CRR and SLR requirement for class C finance companies",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 13,
        "key_phrases": ["४ प्रतिशत", "१० प्रतिशत"]
    },
    {
        "query": "credit to deposit CD ratio maximum limit and penalty",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 15,
        "key_phrases": ["९० प्रतिशत", "हर्जाना"]
    },
    {
        "query": "single obligor limit for fund based loan",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 3,
        "key_phrases": ["२५ प्रतिशत", "प्राथमिक पुँजी"]
    },
    {
        "query": "personal residential home loan maximum ceiling and LTV",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 3,
        "key_phrases": ["३ करोड", "७० प्रतिशत", "८० प्रतिशत"]
    },

    # --- Category 5: Operations, Prohibitions & Trade ---
    {
        "query": "can finance companies issue international import letter of credit LC?",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 2,
        "key_phrases": ["वाणिज्य बैंक", "प्रतितपत्र"]
    },
    {
        "query": "are directors allowed to take loan from their own finance company?",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 3,
        "key_phrases": ["सञ्चालक", "लिन पाउने छैन"]
    },
    {
        "query": "non banking assets NBA holding period before mandatory sale",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 10,
        "key_phrases": ["गैर-बैंकिङ सम्पत्ति", "बिक्री"]
    },

    # --- Category 6: AML/CFT & Reporting ---
    {
        "query": "threshold transaction reporting TTR amount limit and days",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 19,
        "key_phrases": ["१० लाख", "१५ दिन"]
    },
    {
        "query": "suspicious transaction reporting STR timeframe in days",
        "expected_action": "direct_rag",
        "expected_doc": "Unified_directive_2082.pdf",
        "expected_dir": 19,
        "key_phrases": ["३ दिन", "वित्तीय जानकारी इकाई"]
    },
    {
        "query": "cctv footage backup storage days for cash counters and ATMs",
        "expected_action": "direct_rag",
        "expected_doc": "directive_2082.pdf",
        "expected_page": [24, 25, 26],
        "key_phrases": ["९० दिन", "क्यामेरा"]
    },

    # --- Category 7: Intentional Broad Ambiguous Queries (MUST show clarification card) ---
    {
        "query": "loan",
        "expected_action": "disambiguation_card",
        "expected_type": "broad_topic"
    },
    {
        "query": "kyc",
        "expected_action": "disambiguation_card",
        "expected_type": "broad_topic"
    },
    {
        "query": "fee",
        "expected_action": "disambiguation_card",
        "expected_type": "cross_category"
    },
    {
        "query": "ब्याजदर",
        "expected_action": "disambiguation_card",
        "expected_type": "cross_category"
    },
    {
        "query": "कालोसूची",
        "expected_action": "disambiguation_card",
        "expected_type": "cross_category"
    }
]

print(f"\n=======================================================")
print(f"RUNNING ENTERPRISE EVALUATION ON {len(TEST_QUERIES)} BANK QUERIES")
print(f"STRICT MODE: 0 GROQ TOKENS CONSUMED (LOCAL RETRIEVAL ONLY)")
print(f"=======================================================\n")

passed = 0
failed = 0

for idx, item in enumerate(TEST_QUERIES, 1):
    q = item["query"]
    exp_act = item["expected_action"]
    t0 = time.time()

    # Step 1: Disambiguation evaluation (0 tokens)
    is_ambig, card = detect_query_disambiguation(q, [])

    # If disambiguation expected:
    if exp_act == "disambiguation_card":
        if is_ambig:
            passed += 1
            print(f"[{idx:02d}] PASS: Ambiguous Query Intercepted Correctly -> '{q}'")
            print(f"     Title: {card.get('title')} | Options: {len(card.get('options', []))}")
        else:
            failed += 1
            print(f"[{idx:02d}] FAIL: Ambiguous Query Falsely Fast-Tracked -> '{q}'")
        continue

    # If Direct RAG expected:
    if is_ambig:
        failed += 1
        print(f"[{idx:02d}] FAIL: Specific Query Falsely Blocked by Card -> '{q}'")
        print(f"     Card Title: {card.get('title')}")
        continue

    # Step 2: Routing evaluation (0 tokens)
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

    # Step 3: Local Hybrid Search (0 tokens)
    results = hybrid_search(
        user_query=search_query,
        table=table,
        model=model,
        translated_terms="", # 0 LLM expansion tokens
        selected_doc=effective_doc,
        top_k=6
    )
    search_time = time.time() - t0

    # Step 4: Assemble Context with Targeted Clause Windowing (identical to app.py)
    full_page_context = []
    seen_pages = set()
    total_chars = 0

    for res in results:
        sp = (res['source'], int(res['page']))
        if sp not in seen_pages:
            seen_pages.add(sp)
            ptxt = res['text']
            if len(ptxt) > 2400:
                chunk_txt = decode_preeti_text(res.get('text', ''))
                pos = ptxt.find(chunk_txt[:80]) if len(chunk_txt) >= 80 else -1
                if pos != -1:
                    start = max(0, pos - 400)
                    end = min(len(ptxt), pos + len(chunk_txt) + 600)
                    excerpt = ptxt[start:end]
                else:
                    excerpt = ptxt[:2400]
            else:
                excerpt = ptxt

            dir_info = get_unified_directive_for_page(res['page'], res['source']) if 'unified' in res['source'].lower() else None
            dir_tag = f" | {dir_info[1]}" if dir_info else ""
            full_page_context.append(f"[कागजात: {res['source']} | पृष्ठ: {res['page']}{dir_tag}]:\n{excerpt}")
            total_chars += len(excerpt)
            if len(seen_pages) >= 5 or total_chars >= 8000:
                break

    assembled_context = "\n\n".join(full_page_context)
    est_tokens = int(total_chars / 3.5)

    # Verification checks:
    # 1. Target doc or directive represented
    top_sources = [r['source'] for r in results[:4]]
    top_pages = [r['page'] for r in results[:4]]

    doc_matched = any(item.get("expected_doc", "") in s for s in top_sources) if "expected_doc" in item else True

    # Check key phrases in assembled context
    key_phrases = item.get("key_phrases", [])
    found_phrases = [kp for kp in key_phrases if kp in assembled_context]
    has_key_facts = len(found_phrases) >= 1 if key_phrases else True

    # Check token budget compliance
    token_ok = (est_tokens <= 2500)

    if doc_matched and has_key_facts and token_ok:
        passed += 1
        print(f"[{idx:02d}] PASS: '{q}' in {search_time:.3f}s")
        print(f"     Top Hits: {list(zip(top_sources, top_pages))[:3]}")
        print(f"     Matched Facts: {found_phrases} | Context: {total_chars} chars (~{est_tokens} tokens)")
    else:
        failed += 1
        print(f"[{idx:02d}] FAIL: '{q}' in {search_time:.3f}s")
        print(f"     Doc Matched: {doc_matched} | Facts Matched: {found_phrases}/{key_phrases}")
        print(f"     Top Hits: {list(zip(top_sources, top_pages))[:3]}")
        print(f"     Context Size: {total_chars} chars (~{est_tokens} tokens, Token Budget OK: {token_ok})")

print(f"\n=======================================================")
print(f"FINAL RESULT: {passed}/{len(TEST_QUERIES)} PASSED | {failed} FAILED")
print(f"GROQ LLM TOKENS USED: 0 TOKENS (100% LOCAL & FREE)")
print(f"=======================================================\n")
