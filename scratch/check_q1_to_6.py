import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
import ask, time

for qid, q in [
    (1, 'How many debit cards were issued by Development Banks as of Mid-July 2025?'),
    (2, 'What was the number of mobile banking customers in Finance Companies (FCs) in 2024/25?'),
    (3, 'What was the total number of ATMs across all banks and financial institutions as of Mid-July 2025?'),
    (4, 'विकास बैंकहरूमा इन्टरनेट बैंकिङ प्रयोग गर्ने ग्राहक संख्या कति पुगेको छ?'),
    (5, 'एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?'),
    (6, 'What is the maximum cash withdrawal limit through an agent from a digital wallet?')
]:
    terms = ask.expand_query_crosslingual(q, ask.client)
    res = ask.hybrid_search(q, ask.table, ask.embedding_model, translated_terms=terms, top_k=5)
    ctx = "\n".join([f"[{r['source']} P{r['page']}]:\n{r['text']}" for r in res])
    sys_p = "You are an official banking document intelligence assistant for Nepal Rastra Bank. Extract exact numbers/clauses from context. Always cite document name and page. If missing say not found."
    stream = ask.call_groq_with_retry(ask.client, [{'role': 'system', 'content': sys_p}, {'role': 'user', 'content': f'Context:\n{ctx}\n\nQuestion: {q}'}])
    ans = ''.join([c.choices[0].delta.content or '' for c in stream])
    print(f"=== Q{qid} ===")
    print(f"Q: {q}")
    print(f"A: {ans.strip()}")
    print("-" * 50)
    time.sleep(1.5)

