import sys, os, time, json, re
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

import lancedb
from sentence_transformers import SentenceTransformer
from groq import Groq

from core.routing import build_document_year_map, extract_query_years, clean_query_for_search
from core.search import expand_query_crosslingual, hybrid_search, extract_cited_sources
from core.preeti import decode_preeti_text
from core.llm import call_groq_with_retry

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
groq_key = os.getenv('GROQ_API_KEY')
groq_client = Groq(api_key=groq_key) if groq_key else None

# Ground truth benchmarks: Question, governing regulation, expected answer, key factual constraints
AUDIT_BENCHMARKS = [
    {
        "id": "Q1",
        "category": "Credit Classification & Provisioning",
        "query": "What are the conditions for classifying a loan as a Watchlist (सूक्ष्म निगरानी) loan, and what is the required loan loss provision for it?",
        "expected_facts": {
            "provision": ["5%", "५ प्रतिशत", "५%"],
            "conditions": ["१ देखि ३ महिना", "1 to 3 months", "महिना", "म्याद भुक्तान नभएको", "सूक्ष्म निगरानी"]
        },
        "governing_directive": "Directive 2 (कर्जा वर्गीकरण)",
        "governing_keywords": ["सूक्ष्म निगरानी", "५ प्रतिशत", "नोक्सानी"]
    },
    {
        "id": "Q2",
        "category": "Credit Classification & Provisioning",
        "query": "If a loan is fully secured by a personal guarantee (व्यक्तिगत जमानी) only, what is the additional loan loss provision required?",
        "expected_facts": {
            "additional_provision": ["20%", "२० प्रतिशत", "२०%"],
            "subject": ["व्यक्तिगत जमानी", "personal guarantee"]
        },
        "governing_directive": "Directive 2",
        "governing_keywords": ["व्यक्तिगत जमानी", "२० प्रतिशत"]
    },
    {
        "id": "Q3",
        "category": "Credit Classification & Provisioning",
        "query": "If a borrower is blacklisted by the Credit Information Bureau (CIC), how should we classify their loan and what provision is needed?",
        "expected_facts": {
            "classification": ["खराब", "Bad", "Loss"],
            "provision": ["100%", "१०० प्रतिशत", "१००%"]
        },
        "governing_directive": "Directive 2 / Directive 12",
        "governing_keywords": ["कालोसूची", "खराब", "१०० प्रतिशत"]
    },
    {
        "id": "Q4",
        "category": "Capital Adequacy & Core Ratios",
        "query": "What is the maximum allowed Credit-Deposit (CD) Ratio for our finance company, and what is the penalty for breaching it?",
        "expected_facts": {
            "cd_limit": ["90%", "९० प्रतिशत", "९०%"],
            "penalty": ["हर्जाना", "penalty", "बैंक दर", "bank rate"]
        },
        "governing_directive": "Directive 13",
        "governing_keywords": ["Credit to Deposit", "९०", "हर्जाना"]
    },
    {
        "id": "Q5",
        "category": "Capital Adequacy & Core Ratios",
        "query": "What is the minimum Statutory Liquidity Ratio (SLR) and Cash Reserve Ratio (CRR) required for a 'C' class finance company?",
        "expected_facts": {
            "slr": ["10%", "१० प्रतिशत", "१०%"],
            "crr": ["4%", "४ प्रतिशत", "४%"]
        },
        "governing_directive": "Directive 13",
        "governing_keywords": ["वैधानिक तरलता", "अनिवार्य नगद", "१०", "४"]
    },
    {
        "id": "Q6",
        "category": "Capital Adequacy & Core Ratios",
        "query": "When calculating the Capital Adequacy Ratio (CAR), what is the risk weight assigned to loans secured by residential properties?",
        "expected_facts": {
            "risk_weight": ["60%", "६० प्रतिशत", "६०%"],
            "property": ["residential", "आवासीय"]
        },
        "governing_directive": "Directive 1 (Capital Adequacy Framework)",
        "governing_keywords": ["६०", "आवासीय", "Risk Weight"]
    },
    {
        "id": "Q7",
        "category": "Sectoral & Deprived Sector Lending",
        "query": "What percentage of our total loan portfolio must be directed towards the Deprived Sector (विपन्न वर्ग कर्जा)?",
        "expected_facts": {
            "percentage": ["5%", "५ प्रतिशत", "५.०%", "५.० प्रतिशत"]
        },
        "governing_directive": "Directive 17",
        "governing_keywords": ["विपन्न वर्ग", "५ प्रतिशत"]
    },
    {
        "id": "Q8",
        "category": "Sectoral & Deprived Sector Lending",
        "query": "For a 'C' class finance company, what is the minimum lending requirement for the agriculture, micro, small, and medium enterprises (MSME) sectors by Ashad 2084?",
        "expected_facts": {
            "target_2084": ["13%", "१३ प्रतिशत", "१३%"],
            "future_2085": ["15%", "१५ प्रतिशत", "१५%"]
        },
        "governing_directive": "Directive 17",
        "governing_keywords": ["कृषि", "साना तथा मझौला", "१३ प्रतिशत", "२०८४"]
    },
    {
        "id": "Q9",
        "category": "Sectoral & Deprived Sector Lending",
        "query": "What is the maximum limit for a personal residential home loan (व्यक्तिगत आवासीय घर कर्जा)?",
        "expected_facts": {
            "limit": ["3 Crore", "३ करोड", "३० मिलियन", "30 Million", "३,००,००,०००"]
        },
        "governing_directive": "Directive 3",
        "governing_keywords": ["व्यक्तिगत आवासीय", "३ करोड"]
    },
    {
        "id": "Q10",
        "category": "Single Obligor Limits & Margin Lending",
        "query": "What is the Single Obligor Limit (SOL) for fund-based loans for a finance company?",
        "expected_facts": {
            "sol_limit": ["25%", "२५ प्रतिशत", "२५%"],
            "base": ["प्राथमिक पुँजी", "Core Capital", "Tier 1"]
        },
        "governing_directive": "Directive 3",
        "governing_keywords": ["एकल ग्राहक", "२५ प्रतिशत", "प्राथमिक पुँजी"]
    },
    {
        "id": "Q11",
        "category": "Single Obligor Limits & Margin Lending",
        "query": "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?",
        "expected_facts": {
            "ltv_limit": ["70%", "७० प्रतिशत", "७०%"],
            "valuation": ["180", "१८०", "औसत मूल्य", "बजार मूल्य"]
        },
        "governing_directive": "Directive 3 (Margin Lending)",
        "governing_keywords": ["Margin Lending", "७० प्रतिशत", "१८०"]
    },
    {
        "id": "Q12",
        "category": "Corporate Governance & HR",
        "query": "What is the age limit for appointing a Chief Executive Officer (CEO) in a finance company?",
        "expected_facts": {
            "appointment_age": ["65", "६५"],
            "retirement_age": ["69", "६९"]
        },
        "governing_directive": "Directive 6",
        "governing_keywords": ["प्रमुख कार्यकारी", "६५", "६९"]
    },
    {
        "id": "Q13",
        "category": "Corporate Governance & HR",
        "query": "Within how many days must a vacant CEO or senior management position be filled?",
        "expected_facts": {
            "timeframe": ["3 months", "तीन महिना", "३ महिना", "९० दिन", "90 days"]
        },
        "governing_directive": "Directive 6",
        "governing_keywords": ["पदपूर्ति", "रिक्त", "तीन महिना", "३ महिना"]
    },
    {
        "id": "Q14",
        "category": "Corporate Governance & HR",
        "query": "Can a member of the Board of Directors take a loan from our finance company?",
        "expected_facts": {
            "rule": ["पाइने छैन", "लिन पाउने छैन", "cannot", "prohibited", "छैन"],
            "exceptions": ["मुद्दती", "स्वर्ण", "सरकारी", "Fixed Deposit"]
        },
        "governing_directive": "Directive 6",
        "governing_keywords": ["सञ्चालक", "कर्जा", "लिन पाइने छैन"]
    },
    {
        "id": "Q15",
        "category": "AML/CFT & Blacklisting",
        "query": "What is the threshold amount for reporting a cash transaction (TTR) to the Financial Information Unit (FIU)?",
        "expected_facts": {
            "threshold": ["10 Lakh", "१० लाख", "1 Million", "१,०००,०००", "१०,००,०००"]
        },
        "governing_directive": "Directive 19 (AML/CFT)",
        "governing_keywords": ["सीमा कारोबार", "त्त्च्", "१० लाख", "goAML"]
    },
    {
        "id": "Q16",
        "category": "AML/CFT & Blacklisting",
        "query": "Within how many days must a Suspicious Transaction Report (STR) be submitted to the FIU after identifying a suspicious activity?",
        "expected_facts": {
            "timeframe": ["3 days", "३ दिन", "तीन दिन", "३ कार्यदिन"]
        },
        "governing_directive": "Directive 19 (AML/CFT)",
        "governing_keywords": ["शंकास्पद", "क्त्च्", "३ दिन", "तीन दिन"]
    },
    {
        "id": "Q17",
        "category": "AML/CFT & Blacklisting",
        "query": "What is the minimum loan default amount to recommend a borrower for blacklisting to the Credit Information Center?",
        "expected_facts": {
            "threshold": ["10 Lakh", "१० लाख", "1 Million", "१०,००,०००"]
        },
        "governing_directive": "Directive 12 (कर्जा सूचना तथा कालोसूची)",
        "governing_keywords": ["कालोसूची", "१० लाख", "कर्जा सूचना"]
    },
    {
        "id": "Q18",
        "category": "Digital Banking & Payments",
        "query": "What is the maximum daily limit for transferring money using a Mobile Banking App or QR code?",
        "expected_facts": {
            "daily_limit": ["3 Lakh", "३ लाख", "३,००,०००", "300,000"]
        },
        "governing_directive": "Payment Systems Directives",
        "governing_keywords": ["मोबाइल बैंकिङ्ग", "क्युआर", "३ लाख", "३,००,०००"]
    },
    {
        "id": "Q19",
        "category": "Digital Banking & Payments",
        "query": "What is the maximum amount a customer can transfer from a bank account to a digital wallet per day?",
        "expected_facts": {
            "wallet_limit": ["2 Lakh", "२ लाख", "१० लाख", "10 Lakh", "२,००,०००"]
        },
        "governing_directive": "Payment Systems Directives",
        "governing_keywords": ["वालेट", "बैंक खाता", "२ लाख", "१० लाख"]
    },
    {
        "id": "Q20",
        "category": "Digital Banking & Payments",
        "query": "How long should CCTV footage/Memory Backup of an ATM be preserved?",
        "expected_facts": {
            "duration": ["90 days", "९० दिन", "नब्बे दिन", "90", "९०"]
        },
        "governing_directive": "Payment / IT Directives",
        "governing_keywords": ["ऋऋत्ख्", "CCTV", "क्यामेरा", "९०", "नब्बे"]
    }
]

doc_year_map = build_document_year_map(table)
available_years = set.union(*doc_year_map.values()) if doc_year_map else set()

print("=" * 85)
print("🔍 STRICT BENCHMARK AUDIT: 20 NRB BANKING QUESTIONS")
print("=" * 85)

audit_results = []

for idx, b in enumerate(AUDIT_BENCHMARKS, 1):
    q = b["query"]
    t0 = time.time()

    # 1. Routing
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

    # 2. Translation
    trans = expand_query_crosslingual(search_query, groq_client) if groq_client else ""

    # 3. Hybrid Search (top_k=8)
    search_results = hybrid_search(search_query, table, model, translated_terms=trans, selected_doc=effective_doc, top_k=8)

    # 4. Context Windowing
    seen_pages = set()
    full_page_context = []
    retrieved_sources = []
    total_chars = 0

    for item in search_results:
        sp = (item['source'], item['page'])
        if sp not in seen_pages:
            seen_pages.add(sp)
            try:
                page_records = table.search().where(f"source = '{item['source']}' AND page = {item['page']}").select(["text"]).to_pandas()
                full_page_text = "\n".join(page_records['text'].tolist())
            except Exception:
                full_page_text = item.get('text', '')

            full_page_text = decode_preeti_text(full_page_text)
            retrieved_sources.append(f"{item['source']} (Page {item['page']})")
            full_page_context.append(f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}]:\n{full_page_text}\n")
            total_chars += len(full_page_text)
            if len(seen_pages) >= 6 or total_chars > 20000:
                break

    generated_context = "\n".join(full_page_context)

    # 5. Strict Clause Verification:
    # Does the retrieved context actually contain the governing clause with ALL required facts?
    fact_checks = {}
    for fact_name, variations in b["expected_facts"].items():
        matched_var = [v for v in variations if v.lower() in generated_context.lower()]
        fact_checks[fact_name] = bool(matched_var)

    # Strict pass: ALL required expected facts must be in the retrieved context
    all_facts_retrieved = all(fact_checks.values())
    
    # 6. LLM Verification: Generate an answer using the retrieved context to see what LLM concludes
    llm_answer = ""
    llm_correct = False
    if groq_client:
        try:
            prompt = (
                f"You are a strict compliance officer for Nepal Rastra Bank regulated institutions.\n"
                f"Answer the question concisely using ONLY the provided official context.\n"
                f"If the information is not in the context, say 'Information not found in the documents.'\n\n"
                f"Context:\n{generated_context[:7000]}\n\n"
                f"Question: {q}\n"
                f"Answer in 2-3 sentences with exact numbers and citation (Document and Page):"
            )
            res, model_used = call_groq_with_retry(
                groq_client,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=250,
                stream=False
            )
            llm_answer = res.choices[0].message.content.strip()
            
            # Check if LLM answer contains the expected facts
            llm_fact_checks = {}
            for fact_name, variations in b["expected_facts"].items():
                matched_var = [v for v in variations if v.lower() in llm_answer.lower()]
                llm_fact_checks[fact_name] = bool(matched_var)
            llm_correct = all(llm_fact_checks.values())
        except Exception as e:
            llm_answer = f"Error: {e}"

    time.sleep(1.2)
    elapsed = time.time() - t0

    if all_facts_retrieved and llm_correct:
        status = "✅ TRUE PASS"
    elif all_facts_retrieved and not llm_correct:
        status = "⚠️ RETRIEVED BUT LLM FAILED"
    elif not all_facts_retrieved and llm_correct:
        status = "⚠️ LLM GUESSED WITHOUT CONTEXT"
    else:
        status = "❌ RETRIEVAL FAILED"

    print(f"\n[{b['id']}] {status} | {b['category']} ({elapsed:.2f}s)", flush=True)
    print(f"  Q: {q}", flush=True)
    print(f"  Retrieved Pages: {', '.join(retrieved_sources[:4])}", flush=True)
    print(f"  Context Facts: {fact_checks}", flush=True)
    print(f"  LLM Answer: {llm_answer[:200]}...", flush=True)

    audit_results.append({
        "id": b["id"],
        "category": b["category"],
        "query": q,
        "status": status,
        "all_facts_retrieved": all_facts_retrieved,
        "llm_correct": llm_correct,
        "fact_checks": fact_checks,
        "retrieved_sources": retrieved_sources,
        "llm_answer": llm_answer
    })

print("\n" + "=" * 85)
true_passes = sum(1 for r in audit_results if r["status"] == "✅ TRUE PASS")
print(f"🏁 STRICT AUDIT RESULT: {true_passes}/20 Verified True Passes ({true_passes/20*100:.1f}%)")
print("=" * 85)

with open(os.path.join(PROJECT_ROOT, "scratch", "strict_audit_results.json"), "w", encoding="utf-8") as f:
    json.dump(audit_results, f, ensure_ascii=False, indent=2)
print("Saved full audit results to scratch/strict_audit_results.json")
