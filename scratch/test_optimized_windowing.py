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

test_cases = [
    "qualification of compliance officer",
    "Directors' Meeting Allowance",
    "mobile banking limit"
]

def build_smart_page_context(results, live_table, max_chars=7500, max_pages=5):
    seen_pages = set()
    full_page_context = []
    full_page_map = {}
    total_chars = 0

    for item in results:
        sp = (item['source'], item['page'])
        if sp not in seen_pages:
            seen_pages.add(sp)
            try:
                page_records = live_table.search().where(f"source = '{item['source']}' AND page = {item['page']}").select(["text"]).to_pandas()
                full_page_text = "\n".join(page_records['text'].tolist())
            except Exception:
                full_page_text = item['text']

            full_page_text = decode_preeti_text(full_page_text)
            
            # Smart Clause Windowing: If full page is very long (> 2200 chars), center around the matched chunk
            if len(full_page_text) > 2200:
                chunk_txt = decode_preeti_text(item.get('text', ''))
                # Find start of chunk in page
                pos = full_page_text.find(chunk_txt[:80]) if len(chunk_txt) >= 80 else -1
                if pos != -1:
                    start = max(0, pos - 400)
                    end = min(len(full_page_text), pos + len(chunk_txt) + 600)
                    page_excerpt = full_page_text[start:end]
                else:
                    page_excerpt = full_page_text[:2200]
            else:
                page_excerpt = full_page_text

            full_page_map[sp] = page_excerpt

            dir_info = get_unified_directive_for_page(item['page'], item['source']) if 'unified' in item['source'].lower() else None
            dir_tag = f" | {dir_info[1]}" if dir_info else ""
            full_page_context.append(f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}{dir_tag}]:\n{page_excerpt}\n")
            total_chars += len(page_excerpt)
            if len(seen_pages) >= max_pages or total_chars >= max_chars:
                break

    return "\n".join(full_page_context), len(seen_pages), total_chars

for q in test_cases:
    print(f"\n=======================================================")
    print(f"QUERY: {q}")
    print(f"=======================================================")
    t0 = time.time()
    terms = expand_query_crosslingual(q, client)
    results = hybrid_search(q, table, model, translated_terms=terms, selected_doc="All Documents", top_k=8)
    context_text, num_pages, total_chars = build_smart_page_context(results, table)
    prompt = build_rag_prompt(context_text)
    
    t_retrieval = time.time() - t0
    print(f"Retrieval done in {t_retrieval:.2f}s | Pages covered: {num_pages} | Context chars: {total_chars} | Prompt len: {len(prompt)}")
    
    # Run completion with openai/gpt-oss-120b
    t0_llm = time.time()
    res = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": q}
        ],
        temperature=0.1,
        max_tokens=600
    )
    t_llm = time.time() - t0_llm
    ans = res.choices[0].message.content.strip()
    print(f"LLM Answered in {t_llm:.2f}s (Total: {t_retrieval+t_llm:.2f}s)")
    print(f"Preview:\n{ans[:300]}...\n")
