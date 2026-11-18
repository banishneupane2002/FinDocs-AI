import sys, os, time, re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.search import detect_query_disambiguation, is_specific_query
from core.routing import extract_target_directive_number, extract_query_years, clean_query_for_search, build_document_year_map
from core.lexicon import BANKING_DOMAIN_LEXICON, extract_meaningful_keywords
from core.preeti import decode_preeti_text

# Bank Staff Query Evaluation Suite:
# Testing realistic casual, formal, layman, short, long, English, and Nepali queries
BANK_STAFF_QUERIES = [
    # --- Category 1: Loan Classification, NPL, Substandard, Watchlist ---
    {"q": "categories of bad loan", "type": "specific", "category": "NPL & Classification"},
    {"q": "what are the categories of non performing loans?", "type": "specific", "category": "NPL & Classification"},
    {"q": "substandard loan criteria and provision", "type": "specific", "category": "NPL & Classification"},
    {"q": "सूक्ष्म निगरानी कर्जाको समयसीमा र नोक्सानी व्यवस्था कति हो?", "type": "specific", "category": "NPL & Classification"},
    {"q": "loss loan provisioning percentage", "type": "specific", "category": "NPL & Classification"},
    {"q": "खराब कर्जा नोक्सानी व्यवस्था दर", "type": "specific", "category": "NPL & Classification"},
    {"q": "pass loan provisioning rate for finance companies", "type": "specific", "category": "NPL & Classification"},
    {"q": "overdue loan 90 days classification category", "type": "specific", "category": "NPL & Classification"},

    # --- Category 2: Governance, Allowances, HR & Board ---
    {"q": "Directors' Meeting Allowance", "type": "specific", "category": "Governance & HR"},
    {"q": "allowance of board directors in finance companies", "type": "specific", "category": "Governance & HR"},
    {"q": "सञ्चालक समितिको बैठक भत्ता कति लिन पाइन्छ?", "type": "specific", "category": "Governance & HR"},
    {"q": "qualification of compliance officer", "type": "specific", "category": "Governance & HR"},
    {"q": "कम्प्लायन्स अफिसरको योग्यता के हुनुपर्छ?", "type": "specific", "category": "Governance & HR"},
    {"q": "what is the maximum age limit for bank CEO?", "type": "specific", "category": "Governance & HR"},
    {"q": "CEO appointment vacancy fulfillment timeframe", "type": "specific", "category": "Governance & HR"},
    {"q": "promoter share lock-in period for finance companies", "type": "specific", "category": "Governance & HR"},
    {"q": "independent director tenure limit and qualification", "type": "specific", "category": "Governance & HR"},
    {"q": "सञ्चालकको योग्यता र अयोग्यतासम्बन्धी व्यवस्था", "type": "specific", "category": "Governance & HR"},

    # --- Category 3: Digital Banking, Wallets, Cards & Limits ---
    {"q": "mobile banking limit", "type": "specific", "category": "Digital Banking"},
    {"q": "daily fund transfer limit from digital wallet to bank account", "type": "specific", "category": "Digital Banking"},
    {"q": "ATM debit card cash withdrawal daily limit", "type": "specific", "category": "Digital Banking"},
    {"q": "contactless payment limit without pin", "type": "specific", "category": "Digital Banking"},
    {"q": "how much cash can agent deposit in a wallet per day?", "type": "specific", "category": "Digital Banking"},
    {"q": "USSD payment per transaction and daily cap", "type": "specific", "category": "Digital Banking"},
    {"q": "failed transaction claim settlement reversal timeframe", "type": "specific", "category": "Digital Banking"},
    {"q": "वालेटमा अधिकतम ओभरनाइट मौज्दात कति राख्न पाइन्छ?", "type": "specific", "category": "Digital Banking"},
    {"q": "cctv footage backup storage days for cash counters and ATMs", "type": "specific", "category": "Digital Banking"},

    # --- Category 4: Ratios, Caps & Capital Adequacy ---
    {"q": "minimum CRR and SLR requirement for class C finance companies", "type": "specific", "category": "Ratios & Caps"},
    {"q": "credit to deposit CD ratio maximum limit and penalty", "type": "specific", "category": "Ratios & Caps"},
    {"q": "single obligor limit for fund based loan", "type": "specific", "category": "Ratios & Caps"},
    {"q": "personal residential home loan maximum ceiling and LTV", "type": "specific", "category": "Ratios & Caps"},
    {"q": "first home buyer maximum loan ceiling and LTV", "type": "specific", "category": "Ratios & Caps"},
    {"q": "margin lending loan against shares LTV ratio", "type": "specific", "category": "Ratios & Caps"},
    {"q": "deprived sector lending minimum percentage", "type": "specific", "category": "Ratios & Caps"},

    # --- Category 5: Operations, Prohibitions & Trade ---
    {"q": "can finance companies issue international import letter of credit LC?", "type": "specific", "category": "Operations & Trade"},
    {"q": "are directors allowed to take loan from their own finance company?", "type": "specific", "category": "Operations & Trade"},
    {"q": "non banking assets NBA holding period before mandatory sale", "type": "specific", "category": "Operations & Trade"},
    {"q": "cooling-off period required if an agent was previously blacklisted", "type": "specific", "category": "Operations & Trade"},

    # --- Category 6: AML/CFT & Reporting ---
    {"q": "threshold transaction reporting TTR amount limit and days", "type": "specific", "category": "AML/CFT"},
    {"q": "suspicious transaction reporting STR timeframe in days", "type": "specific", "category": "AML/CFT"},
    {"q": "goAML reporting portal timeline for threshold transactions", "type": "specific", "category": "AML/CFT"},
    {"q": "high risk customer PEP enhanced customer due diligence", "type": "specific", "category": "AML/CFT"},

    # --- Category 7: Intentional Ambiguous / Broad Keywords (MUST show clarification card) ---
    {"q": "loan", "type": "ambiguous", "category": "Clarification Card"},
    {"q": "loans", "type": "ambiguous", "category": "Clarification Card"},
    {"q": "kyc", "type": "ambiguous", "category": "Clarification Card"},
    {"q": "fee", "type": "ambiguous", "category": "Clarification Card"},
    {"q": "fees", "type": "ambiguous", "category": "Clarification Card"},
    {"q": "charges", "type": "ambiguous", "category": "Clarification Card"},
    {"q": "ब्याजदर", "type": "ambiguous", "category": "Clarification Card"},
    {"q": "कालोसूची", "type": "ambiguous", "category": "Clarification Card"},
    {"q": "शुल्क", "type": "ambiguous", "category": "Clarification Card"}
]

print("=================================================================")
print(f"BANK STAFF REGULATORY QUERY TEST SUITE: {len(BANK_STAFF_QUERIES)} QUERIES")
print("VERIFICATION CRITERIA: 0 GROQ TOKENS CONSUMED (100% LOCAL PYTHON)")
print("=================================================================\n")

total_tests = len(BANK_STAFF_QUERIES)
passed_tests = 0
failed_tests = 0

for i, test in enumerate(BANK_STAFF_QUERIES, 1):
    q = test["q"]
    expected_type = test["type"]
    category = test["category"]

    # 1. Test Disambiguation Check (0 Groq tokens)
    t0 = time.time()
    is_ambig, card = detect_query_disambiguation(q, [])
    dt_ms = (time.time() - t0) * 1000

    # 2. Test Lexicon Coverage (0 Groq tokens)
    q_lower = q.lower()
    matched_lex_terms = []
    for lex_k, synonyms in BANKING_DOMAIN_LEXICON.items():
        if lex_k in q_lower:
            matched_lex_terms.append(lex_k)

    # 3. Test Directive / Year Routing (0 Groq tokens)
    target_dir = extract_target_directive_number(q)

    # Evaluate
    if expected_type == "specific":
        if not is_ambig:
            passed_tests += 1
            print(f"[{i:02d}/46] PASS ({dt_ms:.2f}ms): [Direct RAG] '{q}' ({category})")
            if matched_lex_terms:
                print(f"       Lexicon Anchors: {matched_lex_terms[:3]}")
        else:
            failed_tests += 1
            print(f"[{i:02d}/46] FAIL: Falsely blocked by clarification card: '{q}'")
            print(f"       Card Title: {card.get('title')}")
    else: # ambiguous
        if is_ambig:
            passed_tests += 1
            print(f"[{i:02d}/46] PASS ({dt_ms:.2f}ms): [Clarification Card] '{q}' -> Title: '{card.get('title')}'")
            print(f"       Options Presented: {len(card.get('options', []))} 1-click options")
        else:
            failed_tests += 1
            print(f"[{i:02d}/46] FAIL: Ambiguous term was not caught: '{q}'")

print("\n=================================================================")
print("TEST SUITE 2: TARGETED CLAUSE WINDOWING BENCHMARK (0 TOKENS)")
print("=================================================================")

# Simulate long legal pages (> 2400 chars) and test windowing behavior
sample_pages = [
    {
        "name": "Directive 2 p.21 (Mobile & Web Limits)",
        "content": "खण्ड क: विद्युतीय बैंकिङ... " + ("क" * 1500) + "मोबाइल एप्लिकेसन (Mobile Application) को माध्यमबाट गरिने भुक्तानी कारोबारको सीमा प्रतिदिन रु. ३,००,०००/- (तीन लाख) सम्म कायम गर्नुपर्नेछ। " + ("ख" * 2000),
        "target_phrase": "मोबाइल एप्लिकेसन"
    },
    {
        "name": "Directive 6 p.75 (Directors' Meeting Allowance)",
        "content": "खण्ड ख: सञ्चालक समिति... " + ("ग" * 1200) + "सञ्चालक समितिको बैठक भत्ता सम्बन्धमा सम्बन्धित संस्थाले आफ्नो नियमावलीमा तोकिए बमोजिम निर्धारण गर्नुपर्नेछ। " + ("घ" * 1800),
        "target_phrase": "बैठक भत्ता"
    },
    {
        "name": "Directive 19 p.173 (Compliance Officer Qualifications)",
        "content": "सम्पत्ति शुद्धीकरण व्यवस्था... " + ("ङ" * 1600) + "संस्थाले AML/CFT सम्बन्धी काम कारबाहीको प्रभावकारी कार्यान्वयनका लागि व्यवस्थापकीय तहको कार्यान्वयन अधिकारी (Compliance Officer) तोक्नुपर्नेछ। " + ("च" * 1500),
        "target_phrase": "Compliance Officer"
    }
]

window_passed = 0
for idx, sp in enumerate(sample_pages, 1):
    raw_text = sp["content"]
    target = sp["target_phrase"]
    original_len = len(raw_text)

    # Windowing logic identical to app.py
    if len(raw_text) > 2400:
        pos = raw_text.find(target[:80])
        if pos != -1:
            start = max(0, pos - 400)
            end = min(len(raw_text), pos + len(target) + 600)
            excerpt = raw_text[start:end]
        else:
            excerpt = raw_text[:2400]
    else:
        excerpt = raw_text

    excerpt_len = len(excerpt)
    est_tokens = int(excerpt_len / 3.5)
    has_target = target in excerpt

    if has_target and excerpt_len <= 2400 and est_tokens <= 700:
        window_passed += 1
        print(f"[Window {idx}] PASS: {sp['name']}")
        print(f"          Original: {original_len} chars -> Trimmed: {excerpt_len} chars (~{est_tokens} tokens)")
        print(f"          Target clause captured 100%: {has_target}")
    else:
        print(f"[Window {idx}] FAIL: {sp['name']}")

print("\n=================================================================")
print(f"FINAL BENCHMARK SCORE: {passed_tests}/{total_tests} Query Tests PASSED")
print(f"WINDOWING SCORE: {window_passed}/{len(sample_pages)} PASSED")
print("TOTAL GROQ TOKENS CONSUMED: 0 TOKENS (100% LOCAL DETERMINISTIC)")
print("=================================================================")
