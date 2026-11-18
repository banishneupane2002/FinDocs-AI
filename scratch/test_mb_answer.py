import os, sys, time
sys.path.insert(0, os.path.abspath('.'))
from groq import Groq
import lancedb
from sentence_transformers import SentenceTransformer
from core.llm import build_rag_prompt
from core.search import hybrid_search, expand_query_crosslingual
from core.preeti import decode_preeti_text
from core.routing import get_unified_directive_for_page
from app import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

q = "mobile banking limit"
terms = expand_query_crosslingual(q, client)
results = hybrid_search(q, table, model, translated_terms=terms, selected_doc="All Documents", top_k=6)

seen_pages = set()
full_context_parts = []
for item in results:
    sp = (item['source'], item['page'])
    if sp not in seen_pages:
        seen_pages.add(sp)
        try:
            page_records = table.search().where(f"source = '{item['source']}' AND page = {item['page']}").select(["text"]).to_pandas()
            full_page_text = "\n".join(page_records['text'].tolist())
        except Exception:
            full_page_text = item['text']

        full_page_text = decode_preeti_text(full_page_text)
        dir_info = get_unified_directive_for_page(item['page'], item['source']) if 'unified' in item['source'].lower() else None
        dir_tag = f" | {dir_info[1]}" if dir_info else ""
        full_context_parts.append(f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}{dir_tag}]:\n{full_page_text}\n")
        if len(seen_pages) >= 4:
            break

context_text = "\n".join(full_context_parts)
prompt = build_rag_prompt(context_text)

t0 = time.time()
res = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": q}
    ],
    temperature=0.1,
    max_tokens=400
)
t_el = time.time() - t0
print(f"Answered in {t_el:.2f}s:")
print(res.choices[0].message.content)
