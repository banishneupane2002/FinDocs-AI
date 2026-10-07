import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
import ask

query = "What agreement must a bank make with a customer for branchless banking?"
print(f"User Query: {query}")
print("1. Expanding terminology...")
terms = ask.expand_query_crosslingual(query, ask.client)
print(f"   Terms: {terms}")

print("2. Performing fast LanceDB hybrid search...")
results = ask.hybrid_search(query, ask.table, ask.embedding_model, translated_terms=terms, top_k=5)
print(f"   Retrieved {len(results)} chunks:")
for r in results:
    print(f"    - [{r['source']} Page {r['page']}] Score: {r['score']:.3f} | {r['text'][:90].replace(chr(10), ' ')}")

context_text = ""
for item in results:
    context_text += f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}]:\n{item['text']}\n"

system_prompt = f"""You are an official banking document intelligence assistant for Nepal Rastra Bank.
Answer the user's question clearly in English based on the provided context.
Cite the document name and page number.

Context:
{context_text}"""

print("3. Querying Groq LLM...")
stream = ask.call_groq_with_retry(
    ask.client,
    [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
)

full_resp = ""
for chunk in stream:
    token = chunk.choices[0].delta.content or ""
    full_resp += token

print("\n--- LLM RESPONSE ---")
print(full_resp)

