import os
import sys
import json
import re

sys.path.insert(0, os.path.abspath("."))
import inspect_context

# 15 questions from the user
eval_suite = [
    {
        "id": "Q1",
        "title": "Establishment of Banking Institutions in Nepal",
        "question": "When was Nepal Bank Limited (NBL) established as the first commercial bank, and in which year was Nepal Rastra Bank (NRB) established?",
        "expected_facts": ["1937", "1956", "Nepal Bank Limited", "Nepal Rastra Bank"],
        "target_doc": "Annual_Report_2024.pdf",
        "target_page": 11
    },
    {
        "id": "Q2",
        "title": "Asset Composition of Development Banks (Mid-July 2024)",
        "question": "What were the top three asset components and their respective shares for Development Banks (DBs) as of Mid-July 2024?",
        "expected_facts": ["70.5", "17.1", "7.5", "Loans and advances", "Investment"],
        "target_doc": "Annual_Report_2024.pdf",
        "target_page": 24
    },
    {
        "id": "Q3",
        "title": "Comparison of Non-Performing Loans (NPL) between DBs and FCs",
        "question": "What was the Non-Performing Loan (NPL) ratio of Development Banks (B-class) versus Finance Companies (C-class) as of Mid-July 2024 compared to Mid-July 2023?",
        "expected_facts": ["3.97", "2.50", "10.31", "4.50"],
        "target_doc": "Annual_Report_2024.pdf",
        "target_page": 13
    },
    {
        "id": "Q4",
        "title": "Capital Adequacy Framework Regulations",
        "question": "Under NRB regulations, which Capital Adequacy Framework applies to national-level Development Banks versus regional-level Development Banks and Finance Companies?",
        "expected_facts": ["Capital Adequacy Framework (2015)", "Capital Adequacy Framework (2007", "national level DBs"],
        "target_doc": "Annual_Report_2024.pdf",
        "target_page": 16
    },
    {
        "id": "Q5",
        "title": "Profitability Shift of Finance Companies (FY 2024/25 vs FY 2023/24)",
        "question": "Did Finance Companies post a consolidated net profit or loss in FY 2024/25, and how did it compare to FY 2023/24?",
        "expected_facts": ["0.67", "1.27", "net profit", "net loss"],
        "target_doc": "Annual_Report_2025.pdf",
        "target_page": 41
    },
    {
        "id": "Q6",
        "title": "Key Onsite Findings on Board Member Borrowing Restrictions",
        "question": "According to the onsite supervision observations in FY 2024/25, which specific loan types are board members of financial institutions permitted to obtain under the Unified Directives?",
        "expected_facts": ["educational loan", "hair Purchase loan", "housing loan", "hous ehold"],
        "target_doc": "Annual_Report_2025.pdf",
        "target_page": 45
    },
    {
        "id": "Q7",
        "title": "Stress Testing of Development Banks (Credit Shock C1 - 2024/25)",
        "question": "In the FY 2024/25 stress testing results, how many Development Banks fail to meet the minimum Capital Adequacy Ratio under Credit Shock C1 (15% performing loans deteriorating into substandard)?",
        "expected_facts": ["Credit Shock (C1)", "15 percent of performing loans", "6 national", "4 provincial"],
        "target_doc": "Annual_Report_2025.pdf",
        "target_page": 33
    },
    {
        "id": "Q8",
        "title": "ATM CCTV Footage Retention Requirement",
        "question": "How long (in days) must banks and financial institutions retain the CCTV camera memory backup at ATM kiosks?",
        "expected_facts": ["CCTV Camera", "Memory Backup", "नब्बे", "९०"],
        "target_doc": "directive_3.pdf",
        "target_page": 8
    },
    {
        "id": "Q9",
        "title": "Force Settlement Window for Failed Card Transactions",
        "question": "What is the required timeline for Force Settlement when an electronic transaction fails (account debited but cash not dispensed / transaction not completed) and both Issuer and Acquirer are different Nepali institutions?",
        "expected_facts": ["Issuer", "Acquirer", "T+3", "Force Settlement"],
        "target_doc": "directive_3.pdf",
        "target_page": 7
    },
    {
        "id": "Q10",
        "title": "Digital Wallet Overnight Balance Cap",
        "question": "What is the maximum overnight balance allowed in a natural person's digital wallet, and where must the excess balance be transferred?",
        "expected_facts": ["५० हजार", "Overnight Balance", "बैंक खाता"],
        "target_doc": "directive_3.pdf",
        "target_page": 19
    },
    {
        "id": "Q11",
        "title": "Simplified KYC for Small Merchants (Annual Limit)",
        "question": "Under the AML/CFT payment directives, what is the maximum annual transaction limit for merchants eligible for Simplified Customer Due Diligence (Simplified KYC)?",
        "expected_facts": ["१,००,०००", "एक लाख", "सरलीकृत", "मचर्ेन्ट"],
        "target_doc": "directive_1.pdf",
        "target_page": 78
    },
    {
        "id": "Q12",
        "title": "Maximum Fee for Inter Bank Fund Transfer (IBFT)",
        "question": "What is the maximum fee service providers can charge individual customers per transaction for Inter Bank Fund Transfer (IBFT) through Mobile App or Internet Banking?",
        "expected_facts": ["IBFT", "१० सम्म", "सेवा शुल्क"],
        "target_doc": "directive_3.pdf",
        "target_page": 21
    },
    {
        "id": "Q13",
        "title": "Periodic Payment System Audit Guidelines",
        "question": "When must a licensed non-bank Payment Service Provider conduct its first System Audit, and how often must it be conducted thereafter if the system is not replaced or upgraded?",
        "expected_facts": ["१ वर्ष", "System Audit", "२ आर्थकि वर्ष"],
        "target_doc": "directive_3.pdf",
        "target_page": 15
    },
    {
        "id": "Q14",
        "title": "Threshold Transaction Reporting (TTR) via goAML",
        "question": "Under what conditions must a Threshold Transaction Report (TTR) be submitted to the FIU, and what is the reporting deadline and required platform?",
        "expected_facts": ["१० लाख", "१५ दिन", "goAML", "Threshold Transaction Reporting"],
        "target_doc": "directive_3.pdf",
        "target_page": 67
    },
    {
        "id": "Q15",
        "title": "Daily Cash Withdrawal Limit on Debit Cards (Version Comparison: २०८१ vs २०८२)",
        "question": "What is the daily ATM cash withdrawal limit on debit cards issued by banks and financial institutions in the 2081 directive versus the updated 2082 directive?",
        "expected_facts": ["डेबिट कार्ड", "प्रतिदिन", "१ लाख", "५० हजार"],
        "target_doc": "directive_1.pdf",
        "target_page": 20
    }
]

print("=== RUNNING ZERO-LLM CONTEXT EXTRACTION VALIDATION ===")
report = []

for item in eval_suite:
    qid = item["id"]
    qtext = item["question"]
    print(f"\n--- Checking {qid}: {item['title']} ---")
    
    # Retrieve top candidates offline
    hits = inspect_context.offline_hybrid_retrieve(qtext, top_k=6)
    
    seen = set()
    pages_data = []
    total_chars = 0
    target_found = False
    facts_found = {f: False for f in item["expected_facts"]}
    
    for h in hits:
        sp = (h['source'], h['page'])
        if sp not in seen:
            seen.add(sp)
            rec = inspect_context.table.search().where(f"source = '{h['source']}' AND page = {h['page']}").to_pandas()
            raw_text = "\n".join(rec['text'].tolist()) if not rec.empty else h['text']
            clean_text = inspect_context.decode_preeti_text(raw_text)
            
            # Check target document / page
            if h['source'] == item['target_doc'] and (abs(h['page'] - item['target_page']) <= 1):
                target_found = True
                
            for fact in item["expected_facts"]:
                if fact.lower() in clean_text.lower():
                    facts_found[fact] = True
                    
            pages_data.append({
                "source": h['source'],
                "page": h['page'],
                "score": round(h['score'], 4),
                "text_snippet": clean_text[:400].replace('\n', ' ')
            })
            total_chars += len(clean_text)
            if len(seen) >= 6 or total_chars > 14000:
                break
                
    all_facts_present = all(facts_found.values())
    present_count = sum(1 for v in facts_found.values() if v)
    
    status = "SUFFICIENT (100% Context Available)" if all_facts_present else f"PARTIAL ({present_count}/{len(facts_found)} facts found)"
    print(f"Status: {status}")
    print(f"Retrieved pages: {[(p['source'], p['page']) for p in pages_data]}")
    print(f"Fact coverage: {facts_found}")
    
    report.append({
        "id": qid,
        "title": item["title"],
        "question": qtext,
        "status": status,
        "is_sufficient": all_facts_present,
        "retrieved_pages": pages_data,
        "fact_coverage": facts_found
    })

with open("scratch/offline_context_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("\nSaved full offline audit report to scratch/offline_context_report.json")
