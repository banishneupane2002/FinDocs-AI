import sys
import os
import json
import time

sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

import ask

TEST_QUESTIONS = [
    # Category 1: Annual Supervision Report 2024/25 (Statistics & Data)
    {
        "id": 1,
        "category": "Category 1: Statistics & Data",
        "question": "How many debit cards were issued by Development Banks as of Mid-July 2025?",
        "expected": "1,216,322 debit cards (increased from 1,076,072 in 2023/24). Source: Annual_Report_2025.pdf — Page 33, Table 3.6"
    },
    {
        "id": 2,
        "category": "Category 1: Statistics & Data",
        "question": "What was the number of mobile banking customers in Finance Companies (FCs) in 2024/25?",
        "expected": "294,739 customers (increased from 231,852 in 2023/24). Source: Annual_Report_2025.pdf — Page 43, Table 4.5"
    },
    {
        "id": 3,
        "category": "Category 1: Statistics & Data",
        "question": "What was the total number of ATMs across all banks and financial institutions as of Mid-July 2025?",
        "expected": "5,222 ATMs overall (Commercial Banks: 4,837, Development Banks: 344, Finance Companies: 41). Source: Annual_Report_2025.pdf — Page 16"
    },
    {
        "id": 4,
        "category": "Category 1: Statistics & Data",
        "question": "विकास बैंकहरूमा इन्टरनेट बैंकिङ प्रयोग गर्ने ग्राहक संख्या कति पुगेको छ?",
        "expected": "५,९९,३१६ (599,316) ग्राहक। Source: Annual_Report_2025.pdf — Page 33, Table 3.6"
    },

    # Category 2: Transaction Limits & Caps (Numerical Compliance)
    {
        "id": 5,
        "category": "Category 2: Transaction Limits & Caps",
        "question": "एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?",
        "expected": "प्रतिदिन अधिकतम रु. २५ हजार (NPR 25,000) र प्रतिमहिना अधिकतम रु. १ लाख (NPR 100,000)। Source: directive_1.pdf / directive_2.pdf — Page 22, Clause द्ध(ज्ञ)"
    },
    {
        "id": 6,
        "category": "Category 2: Transaction Limits & Caps",
        "question": "What is the maximum cash withdrawal limit through an agent from a digital wallet?",
        "expected": "Per day up to NPR 5,000, and per month maximum NPR 25,000. Source: directive_1.pdf — Page 22, Clause द्ध(द्द)"
    },
    {
        "id": 7,
        "category": "Category 2: Transaction Limits & Caps",
        "question": "वालेटमा अधिकतम ओभरनाइट मौज्दात (Overnight Balance) कति राख्न पाइन्छ?",
        "expected": "अधिकतम रु. ५०,००० (NPR 50,000)। सोभन्दा बढी रकम अनिवार्य रूपमा सम्बन्धित बैंक खातामा जम्मा हुनुपर्नेछ। Source: directive_1.pdf — Page 22, Clause घ"
    },
    {
        "id": 8,
        "category": "Category 2: Transaction Limits & Caps",
        "question": "What is the transaction limit for USSD-based mobile payments?",
        "expected": "Daily maximum NPR 10,000, and per-transaction maximum NPR 5,000. Source: directive_1.pdf — Page 22, Clause ठ"
    },

    # Category 3: Legal & Governance Rules
    {
        "id": 9,
        "category": "Category 3: Legal & Governance Rules",
        "question": "स्वःघोषणासम्बन्धी व्यवस्था बारेमा भन्नुहोस",
        "expected": "सञ्चालक पदमा नियुक्त व्यक्तिले अनुसूची ११.१ बमोजिम स्वघोषणा गर्नुपर्ने र नियुक्त भएको १५ दिनभित्र विभागमा पेश गर्नुपर्ने व्यवस्था। Source: directive_1.pdf / directive_2.pdf — Page 59, Clause ठ"
    },
    {
        "id": 10,
        "category": "Category 3: Legal & Governance Rules",
        "question": "What is the cooling-off period required if an agent was previously blacklisted?",
        "expected": "At least 3 years must have elapsed since removal from the credit blacklist. Source: directive_1.pdf / directive_2.pdf — Page 33/35"
    },
    {
        "id": 11,
        "category": "Category 3: Legal & Governance Rules",
        "question": "संस्थागत सुशासनसम्बन्धी व्यवस्था कुन निर्देशनमा छ?",
        "expected": "भुक्तानी प्रणाली विभागको अ.प्रा. निर्देशन नं. ११/०८१ र ११/०८२। Source: directive_1.pdf / directive_2.pdf — Page 56"
    },

    # Category 4: Cross-Lingual Tests
    {
        "id": 12,
        "category": "Category 4: Cross-Lingual Tests",
        "question": "Tell us about the self-declaration system for board directors.",
        "expected": "Responds in English explaining the Director appointment rule, Schedule 11.1 format, and the 15-day deadline. Source: directive_1.pdf — Page 59"
    },
    {
        "id": 13,
        "category": "Category 4: Cross-Lingual Tests",
        "question": "What are the reporting requirements for failed and successful electronic transactions?",
        "expected": "Cites reporting portal requirements and Schedule 10.1.6 (Statement of Success and Failed Transaction). Source: directive_1.pdf — Page 41 & Page 47"
    },

    # Category 5: Anti-Hallucination / Negative Tests
    {
        "id": 14,
        "category": "Category 5: Anti-Hallucination / Negative Tests",
        "question": "Can a digital wallet provide home loans or personal loans directly?",
        "expected": "Information not found / Not authorized in directives"
    },
    {
        "id": 15,
        "category": "Category 5: Anti-Hallucination / Negative Tests",
        "question": "के ग्राहकले वालेटबाट सिधै क्रिप्टोकरेन्सी (Cryptocurrency) किन्न पाउँछ?",
        "expected": "उपलब्ध कागजातमा यो जानकारी फेला परेन / यो अनुमति प्रदान गरिएको छैन।"
    },

    # Category 6: Additional Analytical & Reasoning Questions
    {
        "id": 16,
        "category": "Category 6: Analytical & Reasoning",
        "question": "DB हरूको deprived sector lending घट्दै गएको हो? तथ्यांकसहित भन्नुहोस्।",
        "expected": "Deprived sector lending trends from Annual Supervision Report"
    },
    {
        "id": 17,
        "category": "Category 6: Analytical & Reasoning",
        "question": "२०२४ मा mobile banking users कति पुगेका थिए?",
        "expected": "Mobile banking users count in 2024 from report"
    },
    {
        "id": 18,
        "category": "Category 6: Analytical & Reasoning",
        "question": "What happened to the base rate during FY 2023/24?",
        "expected": "Base rate trend/movement during FY 2023/24"
    },
    {
        "id": 19,
        "category": "Category 6: Analytical & Reasoning",
        "question": "वञ्चित क्षेत्र कर्जाको प्रतिशत २०२१/२२ देखि २०२३/२४ सम्म कसरी परिवर्तन भयो?",
        "expected": "Deprived sector loan percentage changes from 2021/22 to 2023/24"
    },
    {
        "id": 20,
        "category": "Category 6: Analytical & Reasoning",
        "question": "Why does the report say that banking customers are becoming more technology savvy?",
        "expected": "Explanation on surge in electronic/mobile banking, QR payments, digital adoption"
    },
    {
        "id": 21,
        "category": "Category 6: Analytical & Reasoning",
        "question": "Stress test अनुसार DB हरूको मुख्य जोखिम के देखिएको छ?",
        "expected": "Main risks identified in stress testing for Development Banks"
    },
    {
        "id": 22,
        "category": "Category 6: Analytical & Reasoning",
        "question": "२० प्रतिशत deposit withdrawal हुँदा liquidity सम्बन्धी के समस्या आउन सक्छ?",
        "expected": "Liquidity stress test scenario outcome (20% deposit withdrawal impact)"
    },
    {
        "id": 23,
        "category": "Category 6: Analytical & Reasoning",
        "question": "प्रतिवेदनअनुसार DB हरूमाथि regulatory action लिनुका मुख्य कारणहरू के थिए?",
        "expected": "Reasons for supervisory/regulatory actions on DBs"
    },
    {
        "id": 24,
        "category": "Category 6: Analytical & Reasoning",
        "question": "How many DBs were placed under Prompt Corrective Actions and why?",
        "expected": "Number of DBs under PCA and supervisory reasons"
    },
    {
        "id": 25,
        "category": "Category 6: Analytical & Reasoning",
        "question": "शाखारहित बैंकिङ केन्द्रको संख्या घट्दा पनि mobile banking ग्राहक किन बढिरहेको देखिन्छ?",
        "expected": "Analysis on shift from physical BLB touchpoints to direct smartphone/mobile banking"
    }
]

print(f"Starting test execution of all {len(TEST_QUESTIONS)} questions...")
results_log = []

for idx, item in enumerate(TEST_QUESTIONS, 1):
    q_id = item["id"]
    category = item["category"]
    question = item["question"]
    expected = item["expected"]

    print(f"\n=======================================================")
    print(f"[{idx}/{len(TEST_QUESTIONS)}] Testing Q{q_id} ({category})")
    print(f"Question: {question}")

    start_time = time.time()
    terms = ask.expand_query_crosslingual(question, ask.client)
    retrieved = ask.hybrid_search(question, ask.table, ask.embedding_model, translated_terms=terms, top_k=6)
    search_time = time.time() - start_time

    context_text = ""
    sources = []
    for r in retrieved:
        context_text += f"\n[कागजात: {r['source']} | पृष्ठ: {r['page']}]:\n{r['text']}\n"
        sources.append(f"{r['source']} (Page {r['page']})")

    system_prompt = f"""You are an official banking document intelligence assistant for Nepal Rastra Bank.
Your job is to extract exact figures, limits, fee tiers, and regulatory clauses from the provided context.

RULES:
1. If the question is in Nepali, answer in formal, professional Nepali (zero Hindi words).
2. If the question is in English, answer in clear, professional English.
3. Present the exact numbers, fee tier ranges, and limits clearly.
4. Quote the exact clause from the document whenever applicable.
5. Always cite the document name and page number.
6. Interpret statutory conditions and exclusionary scopes logically:
   - For example, if a directive states that a service is permitted in "X बाहेकका क्षेत्रमा" (areas except/excluding X), state definitively that it cannot be operated / is not permitted in X. Do not claim information is missing when the regulatory scope is explicitly defined.
7. Only state "उपलब्ध कागजातमा यो जानकारी फेला परेन / Information not found in the documents" if the subject matter is genuinely absent from the provided context.

Context from files:
{context_text}"""

    gen_start = time.time()
    try:
        stream = ask.call_groq_with_retry(
            ask.client,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        )
        full_answer = ""
        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            full_answer += token
        gen_time = time.time() - gen_start
        status = "SUCCESS"
    except Exception as e:
        full_answer = f"Error: {e}"
        gen_time = time.time() - gen_start
        status = "ERROR"

    total_time = search_time + gen_time
    unique_sources = list(set(sources))

    print(f"Latency: {total_time:.2f}s (Search: {search_time*1000:.1f}ms, Gen: {gen_time:.2f}s)")
    print(f"Sources: {', '.join(unique_sources)}")
    print(f"Answer snippet: {full_answer[:160].replace(chr(10), ' ')}...")

    results_log.append({
        "id": q_id,
        "category": category,
        "question": question,
        "expected": expected,
        "retrieved_sources": unique_sources,
        "answer": full_answer,
        "search_ms": round(search_time * 1000, 1),
        "gen_sec": round(gen_time, 2),
        "total_sec": round(total_time, 2),
        "status": status
    })

    # Small pause to respect Groq rate limits
    time.sleep(2.0)

# Save results to JSON
output_file = "scratch/test_results_25.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results_log, f, ensure_ascii=False, indent=2)

print(f"\n=======================================================")
print(f"Completed all {len(TEST_QUESTIONS)} tests! Saved to {output_file}")

