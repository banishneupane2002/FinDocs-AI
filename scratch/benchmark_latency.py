import os, sys, time
sys.path.insert(0, os.path.abspath('.'))
from groq import Groq
import lancedb
from sentence_transformers import SentenceTransformer
from core.llm import build_rag_prompt, call_groq_with_retry, MODELS_TO_TRY
from core.search import hybrid_search, expand_query_crosslingual
from app import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

q = "Directors' Meeting Allowance"

print(f"=== BENCHMARKING QUERY: {q} ===")

# Step 1: Query expansion
t0 = time.time()
terms = expand_query_crosslingual(q, client)
t_expand = time.time() - t0
print(f"Step 1: expand_query_crosslingual took: {t_expand:.2f}s (Terms: {terms})")

# Step 2: Hybrid search
t0 = time.time()
results = hybrid_search(q, table, model, translated_terms=terms, selected_doc="All Documents", top_k=8)
t_search = time.time() - t0
print(f"Step 2: hybrid_search took: {t_search:.2f}s (Results: {len(results)})")

# Step 3: Context building
t0 = time.time()
seen_pages = set()
full_context_parts = []
for item in results:
    sp = (item['source'], item['page'])
    if sp not in seen_pages:
        seen_pages.add(sp)
        chunks = table.search().where(f"source = '{item['source']}' AND page = {item['page']}").to_list()
        txt = "\n".join([c['text'] for c in chunks])
        full_context_parts.append(f"[{item['source']} | पृष्ठ: {item['page']}]\n{txt}")
    if len(seen_pages) >= 5:
        break
context_text = "\n\n".join(full_context_parts)
prompt = build_rag_prompt(context_text)
t_context = time.time() - t0
print(f"Step 3: context building took: {t_context:.2f}s (Prompt chars: {len(prompt)})")

# Step 4: Individual model test
messages = [
    {"role": "system", "content": prompt},
    {"role": "user", "content": q}
]

for m in MODELS_TO_TRY:
    print(f"\n--- Testing model: {m} ---")
    t0 = time.time()
    try:
        stream = client.chat.completions.create(
            model=m,
            messages=messages,
            temperature=0.1,
            max_tokens=600,
            stream=True
        )
        first_token = None
        full_txt = ""
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            if content and first_token is None:
                first_token = time.time() - t0
            full_txt += content
        t_total = time.time() - t0
        print(f"  Result: SUCCESS | First token: {first_token:.2f}s | Total time: {t_total:.2f}s | Output len: {len(full_txt)}")
    except Exception as e:
        print(f"  Result: FAILED in {time.time()-t0:.2f}s: {e}")
