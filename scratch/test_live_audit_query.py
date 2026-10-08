import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ask

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

q = "When must a licensed non-bank Payment Service Provider conduct its first System Audit, and how often must it be conducted thereafter if the system is not replaced or upgraded?"

print("Running query:", q)
translated_terms = ask.expand_query_crosslingual(q, ask.client)
print("Translated terms:", translated_terms)

results = ask.hybrid_search(q, ask.table, ask.embedding_model, translated_terms=translated_terms, top_k=4)

seen_pages = set()
full_page_context = []
sources = []
total_chars = 0
for item in results:
    sp = (item['source'], item['page'])
    if sp not in seen_pages:
        seen_pages.add(sp)
        try:
            page_records = ask.table.search().where(f"source = '{item['source']}' AND page = {item['page']}").to_pandas()
            full_page_text = "\n".join(page_records['text'].tolist())
        except Exception:
            full_page_text = item['text']

        full_page_text = ask.decode_preeti_text(full_page_text)
        full_page_context.append(f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}]:\n{full_page_text}\n")
        sources.append(f"{item['source']} (Page {item['page']})")
        total_chars += len(full_page_text)
        if len(seen_pages) >= 4 or total_chars > 12000:
            break

context_text = "\n".join(full_page_context)

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
8. Strict Citation Boundary: Cite ONLY the specific document and page where the extracted provision or clause is actually stated. Do NOT invent, assume, or add speculative notes claiming that a clause or provision is also present in other documents or pages unless that exact clause is explicitly found in that other document within the provided context.

Context from files:
{context_text}"""

print("\n--- GENERATING RESPONSE ---")
stream, model = ask.call_groq_with_retry(
    ask.client,
    [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": q}
    ]
)

response_text = ""
for chunk in stream:
    c = chunk.choices[0].delta.content or ""
    response_text += c
    print(c, end="", flush=True)

print(f"\n\n[Model Used: {model}]")
