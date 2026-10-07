import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
import ask, json, time

questions = [
    (1, "How many debit cards were issued by Development Banks as of Mid-July 2025?"),
    (2, "What was the number of mobile banking customers in Finance Companies (FCs) in 2024/25?"),
    (3, "What was the total number of ATMs across all banks and financial institutions as of Mid-July 2025?"),
    (4, "विकास बैंकहरूमा इन्टरनेट बैंकिङ प्रयोग गर्ने ग्राहक संख्या कति पुगेको छ?"),
    (5, "एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?"),
    (6, "What is the maximum cash withdrawal limit through an agent from a digital wallet?"),
    (7, "वालेटमा अधिकतम ओभरनाइट मौज्दात (Overnight Balance) कति राख्न पाइन्छ?"),
    (8, "What is the transaction limit for USSD-based mobile payments?"),
    (9, "स्वःघोषणासम्बन्धी व्यवस्था बारेमा भन्नुहोस"),
    (10, "What is the cooling-off period required if an agent was previously blacklisted?"),
    (11, "संस्थागत सुशासनसम्बन्धी व्यवस्था कुन निर्देशनमा छ?"),
    (12, "Tell us about the self-declaration system for board directors.")
]

for qid, q in questions:
    terms = ask.expand_query_crosslingual(q, ask.client)
    res = ask.hybrid_search(q, ask.table, ask.embedding_model, translated_terms=terms, top_k=5)
    ctx = "\n".join([f"[{r['source']} P{r['page']}]:\n{r['text']}" for r in res])
    sys_p = "You are an official banking document intelligence assistant for Nepal Rastra Bank. Extract exact numbers/clauses from context. Always cite document name and page. If missing say not found."
    ans = ""
    try:
        stream = ask.call_groq_with_retry(ask.client, [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": f"Context:\n{ctx}\n\nQuestion: {q}"}
        ])
        for c in stream: 
            ans += (c.choices[0].delta.content or "")
    except Exception as e:
        ans = str(e)
    sources_str = ", ".join([f"{r['source']} P{r['page']}" for r in res[:3]])
    print(f"\n=== Q{qid}: {q} ===")
    print(f"Sources: {sources_str}")
    print(f"Answer:\n{ans.strip()}")
    time.sleep(2.0)

