import os, sys
sys.path.insert(0, os.path.abspath('.'))
from groq import Groq
from core.llm import build_rag_prompt
from core.search import hybrid_search
import lancedb
from sentence_transformers import SentenceTransformer
from app import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

q = "Directors' Meeting Allowance"
terms = "सञ्चालक बैठक भत्ता"
results = hybrid_search(q, table, model, translated_terms=terms, selected_doc="All Documents", top_k=8)

seen_pages = set()
full_context_parts = []
for item in results:
    sp = (item['source'], item['page'])
    if sp not in seen_pages:
        seen_pages.add(sp)
        chunks = table.search().where(f"source = '{item['source']}' AND page = {item['page']}").to_list()
        txt = "\n".join([c['text'] for c in chunks])
        full_context_parts.append(f"[{item['source']} | पृष्ठ: {item['page']}]\n{txt}")

context_text = "\n\n".join(full_context_parts)
prompt = build_rag_prompt(context_text)

messages = [
    {"role": "system", "content": prompt},
    {"role": "user", "content": q}
]

res = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=messages,
    temperature=0.1,
    max_tokens=600
)

print("Answer from gpt-oss-20b on retrieved context:")
print(res.choices[0].message.content)
