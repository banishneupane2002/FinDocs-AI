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
from core.search import expand_query_crosslingual, hybrid_search
from core.preeti import decode_preeti_text

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
groq_key = os.getenv('GROQ_API_KEY')
groq_client = Groq(api_key=groq_key) if groq_key else None

TEST_CASES = [
    # Category 1: Credit Classification & Provisioning
    {
        "id": "Q1",
        "category": "Credit Classification & Provisioning",
        "query": "What are the conditions for classifying a loan as a Watchlist (सूक्ष्म निगरानी) loan, and what is the required loan loss provision for it?",
        "targets": ["सूक्ष्म निगरानी", "५", "5", "Watchlist", "महिना", "१ देखि ३"]
    },
    {
        "id": "Q2",
        "category": "Credit Classification & Provisioning",
        "query": "If a loan is fully secured by a personal guarantee (व्यक्तिगत जमानी) only, what is the additional loan loss provision required?",
        "targets": ["व्यक्तिगत जमानी", "२०", "20"]
    },
    {
        "id": "Q3",
        "category": "Credit Classification & Provisioning",
        "query": "If a borrower is blacklisted by the Credit Information Bureau (CIC), how should we classify their loan and what provision is needed?",
        "targets": ["कालोसूची", "खराब", "१००", "100", "Bad"]
    },

    # Category 2: Capital Adequacy & Core Ratios
    {
        "id": "Q4",
        "category": "Capital Adequacy & Core Ratios",
        "query": "What is the maximum allowed Credit-Deposit (CD) Ratio for our finance company, and what is the penalty for breaching it?",
        "targets": ["९०", "90", "Credit-Deposit", "CD", "हर्जाना", "penalty", "बैंक दर"]
    },
    {
        "id": "Q5",
        "category": "Capital Adequacy & Core Ratios",
        "query": "What is the minimum Statutory Liquidity Ratio (SLR) and Cash Reserve Ratio (CRR) required for a 'C' class finance company?",
        "targets": ["१०", "10", "४", "4", "SLR", "CRR", "तरलता", "अनिवार्य नगद"]
    },
    {
        "id": "Q6",
        "category": "Capital Adequacy & Core Ratios",
        "query": "When calculating the Capital Adequacy Ratio (CAR), what is the risk weight assigned to loans secured by residential properties?",
        "targets": ["६०", "60", "residential", "आवासीय", "Risk", "Weight"]
    },

    # Category 3: Sectoral & Deprived Sector Lending
    {
        "id": "Q7",
        "category": "Sectoral & Deprived Sector Lending",
        "query": "What percentage of our total loan portfolio must be directed towards the Deprived Sector (विपन्न वर्ग कर्जा)?",
        "targets": ["विपन्न वर्ग", "५", "5"]
    },
    {
        "id": "Q8",
        "category": "Sectoral & Deprived Sector Lending",
        "query": "For a 'C' class finance company, what is the minimum lending requirement for the agriculture, micro, small, and medium enterprises (MSME) sectors by Ashad 2084?",
        "targets": ["१३", "13", "१५", "15", "२०८४", "2084", "कृषि", "साना तथा मझौला"]
    },
    {
        "id": "Q9",
        "category": "Sectoral & Deprived Sector Lending",
        "query": "What is the maximum limit for a personal residential home loan (व्यक्तिगत आवासीय घर कर्जा)?",
        "targets": ["व्यक्तिगत आवासीय", "३ करोड", "3 करोड", "3 Crore", "३० मिलियन"]
    },

    # Category 4: Single Obligor Limits & Margin Lending
    {
        "id": "Q10",
        "category": "Single Obligor Limits & Margin Lending",
        "query": "What is the Single Obligor Limit (SOL) for fund-based loans for a finance company?",
        "targets": ["२५", "25", "प्राथमिक पुँजी", "Core Capital", "Single Obligor", "एकल ग्राहक"]
    },
    {
        "id": "Q11",
        "category": "Single Obligor Limits & Margin Lending",
        "query": "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?",
        "targets": ["७०", "70", "१८०", "180", "सेयर", "शेयर", "मार्जिन"]
    },

    # Category 5: Corporate Governance & HR
    {
        "id": "Q12",
        "category": "Corporate Governance & HR",
        "query": "What is the age limit for appointing a Chief Executive Officer (CEO) in a finance company?",
        "targets": ["६५", "65", "६९", "69", "प्रमुख कार्यकारी", "उमेर"]
    },
    {
        "id": "Q13",
        "category": "Corporate Governance & HR",
        "query": "Within how many days must a vacant CEO or senior management position be filled?",
        "targets": ["३ महिना", "तीन महिना", "3 महिना", "पदपूर्ति", "रिक्त"]
    },
    {
        "id": "Q14",
        "category": "Corporate Governance & HR",
        "query": "Can a member of the Board of Directors take a loan from our finance company?",
        "targets": ["सञ्चालक", "कर्जा", "मुद्दती", "स्वर्ण", "ऋणपत्र", "लिन पाइने छैन"]
    },

    # Category 6: AML/CFT & Blacklisting
    {
        "id": "Q15",
        "category": "AML/CFT & Blacklisting",
        "query": "What is the threshold amount for reporting a cash transaction (TTR) to the Financial Information Unit (FIU)?",
        "targets": ["१० लाख", "10 लाख", "त्त्च्", "TTR", "सीमा कारोबार"]
    },
    {
        "id": "Q16",
        "category": "AML/CFT & Blacklisting",
        "query": "Within how many days must a Suspicious Transaction Report (STR) be submitted to the FIU after identifying a suspicious activity?",
        "targets": ["३ दिन", "तीन दिन", "3 दिन", "क्त्च्", "STR", "goAML", "शंकास्पद"]
    },
    {
        "id": "Q17",
        "category": "AML/CFT & Blacklisting",
        "query": "What is the minimum loan default amount to recommend a borrower for blacklisting to the Credit Information Center?",
        "targets": ["१० लाख", "10 लाख", "कालोसूची", "कर्जा सूचना"]
    },

    # Category 7: Digital Banking & Payments
    {
        "id": "Q18",
        "category": "Digital Banking & Payments",
        "query": "What is the maximum daily limit for transferring money using a Mobile Banking App or QR code?",
        "targets": ["३ लाख", "3 लाख", "क्युआर", "QR", "मोबाइल बैंकिङ्ग"]
    },
    {
        "id": "Q19",
        "category": "Digital Banking & Payments",
        "query": "What is the maximum amount a customer can transfer from a bank account to a digital wallet per day?",
        "targets": ["२ लाख", "2 लाख", "१० लाख", "10 लाख", "वालेट", "बैंक खाता"]
    },
    {
        "id": "Q20",
        "category": "Digital Banking & Payments",
        "query": "How long should CCTV footage/Memory Backup of an ATM be preserved?",
        "targets": ["९०", "90", "नब्बे", "दिन", "ऋऋत्ख्", "CCTV", "फुटेज", "ब्याकअप"]
    }
]

doc_year_map = build_document_year_map(table)
available_years = set.union(*doc_year_map.values()) if doc_year_map else set()

results_summary = []

print("=" * 80)
print(f"🚀 RUNNING OFFLINE RETRIEVAL EVALUATION FOR 20 BANKING QUESTIONS (ZERO LLM GENERATION)")
print("=" * 80)

for idx, tc in enumerate(TEST_CASES, 1):
    q = tc["query"]
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
    
    # 3. Hybrid Search
    search_results = hybrid_search(search_query, table, model, translated_terms=trans, selected_doc=effective_doc, top_k=6)
    
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
            if len(seen_pages) >= 4 or total_chars > 12000:
                break
                
    generated_context = "\n".join(full_page_context)
    elapsed = time.time() - t0
    
    # 5. Check Target Facts in Context
    matched_targets = [t for t in tc["targets"] if t.lower() in generated_context.lower()]
    missing_targets = [t for t in tc["targets"] if t.lower() not in generated_context.lower()]
    
    # Pass criteria: at least 2 key targets present or >= 50%
    is_pass = len(matched_targets) >= 2 or (len(matched_targets) >= 1 and len(tc["targets"]) <= 2)
    
    status_icon = "✅ PASS" if is_pass else "❌ FAIL"
    
    print(f"\n[{tc['id']}] {status_icon} | {tc['category']} ({elapsed:.2f}s)")
    print(f"  Q: {q}")
    print(f"  Retrieved: {', '.join(retrieved_sources[:3])}")
    print(f"  Matched Facts: {matched_targets}")
    if missing_targets:
        print(f"  Missing Facts: {missing_targets}")
        
    # Store record
    results_summary.append({
        "id": tc["id"],
        "category": tc["category"],
        "query": q,
        "is_pass": is_pass,
        "matched_targets": matched_targets,
        "missing_targets": missing_targets,
        "retrieved_sources": retrieved_sources,
        "context_length": len(generated_context),
        "context_snippet": generated_context[:600]
    })

# Summary Table
total = len(results_summary)
passed = sum(1 for r in results_summary if r["is_pass"])
print("\n" + "=" * 80)
print(f"🏁 EVALUATION SUMMARY: {passed}/{total} Passed ({passed/total*100:.1f}%)")
print("=" * 80)

# Write report json
with open(os.path.join(PROJECT_ROOT, "scratch", "eval_20_results.json"), "w", encoding="utf-8") as f:
    json.dump(results_summary, f, ensure_ascii=False, indent=2)
print("Saved report to scratch/eval_20_results.json")

