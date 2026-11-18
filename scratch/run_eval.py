import sys, os, time

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search, detect_query_disambiguation, is_specific_query
from core.routing import build_document_year_map, extract_query_years, clean_query_for_search, get_unified_directive_for_page
from core.preeti import decode_preeti_text

print("1. Connecting to LanceDB...", flush=True)
db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')

print("2. Loading SentenceTransformer model (0 Groq tokens)...", flush=True)
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

print("3. Building document year map...", flush=True)
doc_year_map = build_document_year_map(table)
available_years = set.union(*doc_year_map.values()) if doc_year_map else set()

TEST_QUERIES = [
    # Loan Classification & NPL
    {"q": "categories of bad loan", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["खराब", "कमसल", "शंकास्पद"]},
    {"q": "what are the categories of non performing loans?", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["कमसल", "शंकास्पद", "खराब"]},
    {"q": "substandard loan criteria and provision", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["कमसल", "२५ प्रतिशत", "भाखा नाघेको"]},
    {"q": "सूक्ष्म निगरानी कर्जाको समयसीमा र नोक्सानी व्यवस्था कति हो?", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["सूक्ष्म निगरानी", "५ प्रतिशत"]},
    {"q": "loss loan provisioning percentage", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["१०० प्रतिशत", "खराब"]},

    # Governance & Allowances & HR
    {"q": "Directors' Meeting Allowance", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["बैठक भत्ता", "नियमावली"]},
    {"q": "allowance of board directors in finance companies", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["बैठक भत्ता", "सञ्चालक"]},
    {"q": "सञ्चालक समितिको बैठक भत्ता कति लिन पाइन्छ?", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["बैठक भत्ता", "नियमावली"]},
    {"q": "qualification of compliance officer", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["कार्यान्वयन अधिकारी", "अधिकृत"]},
    {"q": "कम्प्लायन्स अफिसरको योग्यता के हुनुपर्छ?", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["कार्यान्वयन अधिकारी", "अधिकृत"]},
    {"q": "what is the maximum age limit for bank CEO?", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["६५ वर्ष", "६९ वर्ष"]},
    {"q": "promoter share lock-in period for finance companies", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["संस्थापक", "५ वर्ष"]},

    # Digital Banking & Limits
    {"q": "mobile banking limit", "act": "direct", "doc": "directive_2082.pdf", "facts": ["३ लाख", "प्रतिदिन"]},
    {"q": "daily fund transfer limit from digital wallet to bank account", "act": "direct", "doc": "directive_2082.pdf", "facts": ["२ लाख", "१० लाख"]},
    {"q": "ATM debit card cash withdrawal daily limit", "act": "direct", "doc": "directive_2082.pdf", "facts": ["२५ हजार", "१ लाख"]},
    {"q": "contactless payment limit without pin", "act": "direct", "doc": "directive_2082.pdf", "facts": ["५ हजार", "५,०००"]},
    {"q": "how much cash can agent deposit in a wallet per day?", "act": "direct", "doc": "directive_2082.pdf", "facts": ["२५ हजार", "१ लाख"]},
    {"q": "failed transaction claim settlement reversal timeframe", "act": "direct", "doc": "directive_2082.pdf", "facts": ["T+1", "T+3", "फर्छ्यौट"]},

    # Ratios & Regulatory Caps
    {"q": "minimum CRR and SLR requirement for class C finance companies", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["४ प्रतिशत", "१० प्रतिशत"]},
    {"q": "credit to deposit CD ratio maximum limit and penalty", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["९० प्रतिशत", "हर्जाना"]},
    {"q": "single obligor limit for fund based loan", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["२५ प्रतिशत", "प्राथमिक पुँजी"]},
    {"q": "personal residential home loan maximum ceiling and LTV", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["३ करोड", "७० प्रतिशत", "८० प्रतिशत"]},

    # Operations & Trade
    {"q": "can finance companies issue international import letter of credit LC?", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["वाणिज्य बैंक", "प्रतितपत्र"]},
    {"q": "are directors allowed to take loan from their own finance company?", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["सञ्चालक", "लिन पाउने छैन"]},
    {"q": "non banking assets NBA holding period before mandatory sale", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["गैर-बैंकिङ सम्पत्ति", "बिक्री"]},

    # AML/CFT & Security
    {"q": "threshold transaction reporting TTR amount limit and days", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["१० लाख", "१५ दिन"]},
    {"q": "suspicious transaction reporting STR timeframe in days", "act": "direct", "doc": "Unified_directive_2082.pdf", "facts": ["३ दिन", "वित्तीय जानकारी इकाई"]},
    {"q": "cctv footage backup storage days for cash counters and ATMs", "act": "direct", "doc": "directive_2082.pdf", "facts": ["९० दिन", "क्यामेरा"]},

    # Intentional Broad Ambiguity (Must show card)
    {"q": "loan", "act": "card"},
    {"q": "kyc", "act": "card"},
    {"q": "fee", "act": "card"},
    {"q": "ब्याजदर", "act": "card"},
    {"q": "कालोसूची", "act": "card"}
]

print(f"\nEvaluating {len(TEST_QUERIES)} banking questions (0 Groq tokens)...\n", flush=True)

passed = 0
failed = 0

for i, t in enumerate(TEST_QUERIES, 1):
    q = t["q"]
    act = t["act"]
    t0 = time.time()

    is_ambig, card = detect_query_disambiguation(q, [])

    if act == "card":
        if is_ambig:
            passed += 1
            print(f"[{i:02d}] PASS: [Ambiguity Card] '{q}' -> Title: '{card.get('title')}'", flush=True)
        else:
            failed += 1
            print(f"[{i:02d}] FAIL: [Ambiguity Card] '{q}' was falsely fast-tracked", flush=True)
        continue

    if is_ambig:
        failed += 1
        print(f"[{i:02d}] FAIL: [Fast-Track] '{q}' was falsely blocked by card '{card.get('title')}'", flush=True)
        continue

    # Routing
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

    # Retrieval (0 LLM tokens, local SentenceTransformer + BM25)
    results = hybrid_search(
        user_query=search_query,
        table=table,
        model=model,
        translated_terms="",
        selected_doc=effective_doc,
        top_k=6
    )
    dt = time.time() - t0

    # Targeted Clause Windowing (identical to app.py)
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

    top_sources = [r['source'] for r in results[:3]]
    top_pages = [r['page'] for r in results[:3]]

    expected_doc = t.get("doc", "")
    doc_ok = any(expected_doc in s for s in top_sources)
    expected_facts = t.get("facts", [])
    matched_facts = [f for f in expected_facts if f in assembled_context]
    facts_ok = len(matched_facts) >= 1 if expected_facts else True
    token_ok = (est_tokens <= 2500)

    hits_str = ", ".join([f"{os.path.basename(s)} p.{p}" for s, p in zip(top_sources, top_pages)])

    if doc_ok and facts_ok and token_ok:
        passed += 1
        print(f"[{i:02d}] PASS ({dt:.2f}s): '{q}'\n     Hits: [{hits_str}] | Facts: {matched_facts} | Context: {total_chars} chars (~{est_tokens} tokens)", flush=True)
    else:
        failed += 1
        print(f"[{i:02d}] FAIL ({dt:.2f}s): '{q}'\n     Doc OK: {doc_ok} | Facts OK: {facts_ok} ({matched_facts}/{expected_facts}) | Token OK: {token_ok} ({est_tokens} toks)\n     Hits: [{hits_str}]", flush=True)

print(f"\n=======================================================")
print(f"FINAL RESULT: {passed}/{len(TEST_QUERIES)} PASSED | {failed} FAILED")
print(f"GROQ LLM TOKENS CONSUMED: 0 (100% LOCAL DETERMINISTIC TEST)")
print(f"=======================================================\n", flush=True)
