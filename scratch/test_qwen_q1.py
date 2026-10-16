import os, sys
sys.path.insert(0, os.getcwd())
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()
from groq import Groq
import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search, expand_query_crosslingual
from core.preeti import decode_preeti_text

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

q = "What are the conditions for classifying a loan as a Watchlist (सूक्ष्म निगरानी) loan, and what is the required loan loss provision for it?"
trans = expand_query_crosslingual(q, groq_client)
print("Query:", q)
print("Translation:", trans)

res = hybrid_search(q, tbl, model, translated_terms=trans, selected_doc="All Documents", top_k=8)
seen_pages = set()
full_page_context = []
for item in res:
    sp = (item['source'], item['page'])
    if sp not in seen_pages:
        seen_pages.add(sp)
        try:
            page_records = tbl.search().where(f"source = '{item['source']}' AND page = {item['page']}").select(["text"]).to_pandas()
            full_page_text = "\n".join(page_records['text'].tolist())
        except Exception:
            full_page_text = item.get('text', '')
        full_page_text = decode_preeti_text(full_page_text)
        full_page_context.append(f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}]:\n{full_page_text}\n")
        print(f"Added page: {item['source']} page {item['page']}")
        if len(seen_pages) >= 6: break

context_text = "\n".join(full_page_context)

prompt = (
    f"You are a strict compliance officer for Nepal Rastra Bank regulated institutions.\n"
    f"Answer the question concisely using ONLY the provided official context.\n"
    f"Context:\n{context_text[:8000]}\n\n"
    f"Question: {q}\n"
    f"Answer in 2-3 sentences with exact numbers and citation (Document and Page):"
)

resp = groq_client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.0,
    max_tokens=300
)
print("\n=== QWEN RESPONSE ===")
print(resp.choices[0].message.content)
