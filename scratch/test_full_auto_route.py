import sys, os, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import app

q = "tell me about system audit in 2079 directive"

def extract_query_year(query: str) -> int:
    dev_m = re.search(r'२०([७८][०-९])', query)
    if dev_m:
        nep_to_ar = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
        decade_unit = "".join(nep_to_ar.get(c, c) for c in dev_m.group(1))
        return int(f"20{decade_unit}")
    ar_m = re.search(r'\b(20[5-9][0-9]|20[0-4][0-9])\b', query)
    if ar_m:
        return int(ar_m.group(1))
    return 0

target_year = extract_query_year(q)
print("Auto-detected target year:", target_year)

df = app.table.to_pandas()
matching_docs = [d for d in df['source'].unique() if str(target_year) in d]
print("Auto-routed target document:", matching_docs)

auto_doc = matching_docs[0] if matching_docs else None

# Clean query for search (remove 'in 2079 directive' so search focuses on 'system audit')
q_clean = re.sub(r'\b(in|of|from|को)?\s*(20[5-9][0-9]|२०[७८][०-९])\s*(directive|circular|निर्देशन|परिपत्र)?\b', '', q, flags=re.IGNORECASE).strip()
print("Search query cleaned of routing noise:", repr(q_clean))

translated = app.expand_query_crosslingual(q_clean or q, app.groq_client)
results = app.hybrid_search(q_clean or q, app.table, app.embedding_model, translated_terms=translated, selected_doc=auto_doc, top_k=6)

print("\nRetrieved Chunks:")
for r in results:
    print(f"  {r['source']} Page {r['page']} (Score: {r['score']})")

seen_pages = set()
full_page_context = []
full_page_map = {}
total_chars = 0
for item in results:
    sp = (item['source'], item['page'])
    if sp not in seen_pages:
        seen_pages.add(sp)
        try:
            page_records = app.table.search().where(f"source = '{item['source']}' AND page = {item['page']}").to_pandas()
            full_page_text = "\n".join(page_records['text'].tolist())
        except Exception:
            full_page_text = item['text']

        full_page_text = app.decode_preeti_text(full_page_text)
        full_page_map[sp] = full_page_text
        full_page_context.append(f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}]:\n{full_page_text}\n")
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
stream = app.groq_client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": q}
    ],
    temperature=0.1,
    max_tokens=900,
    stream=True
)

full_resp = ""
for chunk in stream:
    t = chunk.choices[0].delta.content or ""
    full_resp += t
    print(t, end="", flush=True)

print("\n\n--- EXACT CITED SOURCES FILTER ---")
cited = app.extract_cited_sources(full_resp, results, full_page_map)
for c in cited:
    print(f"  Verified Source: {c['source']} (Page {c['page']})")

