import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath("."))
import ask

questions = [
    ("Q1", "When was Nepal Bank Limited (NBL) established as the first commercial bank, and in which year was Nepal Rastra Bank (NRB) established?"),
    ("Q2", "What were the top three asset components and their respective shares for Development Banks (DBs) as of Mid-July 2024?"),
    ("Q3", "What was the Non-Performing Loan (NPL) ratio of Development Banks (B-class) versus Finance Companies (C-class) as of Mid-July 2024 compared to Mid-July 2023?"),
    ("Q4", "Under NRB regulations, which Capital Adequacy Framework applies to national-level Development Banks versus regional-level Development Banks and Finance Companies?"),
    ("Q5", "Did Finance Companies post a consolidated net profit or loss in FY 2024/25, and how did it compare to FY 2023/24?"),
    ("Q6", "According to the onsite supervision observations in FY 2024/25, which specific loan types are board members of financial institutions permitted to obtain under the Unified Directives?"),
    ("Q7", "In the FY 2024/25 stress testing results, how many Development Banks fail to meet the minimum Capital Adequacy Ratio under Credit Shock C1 (15% performing loans deteriorating into substandard)?"),
    ("Q8", "How long (in days) must banks and financial institutions retain the CCTV camera memory backup at ATM kiosks?"),
    ("Q9", "What is the required timeline for Force Settlement when an electronic transaction fails (account debited but cash not dispensed / transaction not completed) and both Issuer and Acquirer are different Nepali institutions?"),
    ("Q10", "What is the maximum overnight balance allowed in a natural person's digital wallet, and where must the excess balance be transferred?"),
    ("Q11", "Under the AML/CFT payment directives, what is the maximum annual transaction limit for merchants eligible for Simplified Customer Due Diligence (Simplified KYC)?"),
    ("Q12", "What is the maximum fee service providers can charge individual customers per transaction for Inter Bank Fund Transfer (IBFT) through Mobile App or Internet Banking?"),
    ("Q13", "When must a licensed non-bank Payment Service Provider conduct its first System Audit, and how often must it be conducted thereafter if the system is not replaced or upgraded?"),
    ("Q14", "Under what conditions must a Threshold Transaction Report (TTR) be submitted to the FIU, and what is the reporting deadline and required platform?"),
    ("Q15", "What is the daily ATM cash withdrawal limit on debit cards issued by banks and financial institutions in the 2081 directive versus the updated 2082 directive?")
]

results = []

for q_id, q_text in questions:
    print(f"\n[{q_id}] Running: {q_text[:60]}...")
    trans = ask.expand_query_crosslingual(q_text, ask.client)
    hits = ask.hybrid_search(q_text, ask.table, ask.embedding_model, translated_terms=trans, top_k=6)
    
    seen = set()
    pages_context = []
    citations = []
    total_chars = 0
    for h in hits:
        sp = (h['source'], h['page'])
        if sp not in seen:
            seen.add(sp)
            rec = ask.table.search().where(f"source = '{h['source']}' AND page = {h['page']}").to_pandas()
            raw_text = "\n".join(rec['text'].tolist()) if not rec.empty else h['text']
            clean_page_text = ask.decode_preeti_text(raw_text)
            pages_context.append(f"\n[कागजात: {h['source']} | पृष्ठ: {h['page']}]:\n{clean_page_text}\n")
            citations.append(f"{h['source']} (Page {h['page']})")
            total_chars += len(clean_page_text)
            if len(seen) >= 4 or total_chars > 12000:
                break
                
    context_str = "\n".join(pages_context)
    system_prompt = f"""You are an official banking document intelligence assistant for Nepal Rastra Bank.
Your job is to extract exact figures, limits, fee tiers, and regulatory clauses from the provided context.

RULES:
1. If the question is in Nepali, answer in formal, professional Nepali (zero Hindi words).
2. If the question is in English, answer in clear, professional English.
3. Present the exact numbers, fee tier ranges, and limits clearly.
4. Quote the exact clause from the document whenever applicable.
5. Always cite the document name and page number.
6. Only state "Information not found in the documents" if genuinely absent.

Context from files:
{context_str}"""

    try:
        stream, model_used = ask.call_groq_with_retry(
            ask.client,
            [{"role": "system", "content": system_prompt}, {"role": "user", "content": q_text}]
        )
        answer = "".join([chunk.choices[0].delta.content or "" for chunk in stream])
        print(f" -> Generated via {model_used}. Citations: {citations[:2]}")
        results.append({
            "id": q_id,
            "question": q_text,
            "sources": citations,
            "answer": answer,
            "model": model_used
        })
    except Exception as e:
        print(f" -> ERROR: {e}")
        results.append({
            "id": q_id,
            "question": q_text,
            "sources": citations,
            "answer": f"ERROR: {e}",
            "model": "error"
        })
    time.sleep(1)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_final_15.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nSaved all 15 benchmark outputs to: {out_path} (exists={os.path.exists(out_path)})")
