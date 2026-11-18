import os, sys
sys.path.insert(0, os.path.abspath('.'))
from groq import Groq
from core.llm import build_rag_prompt, call_groq_with_retry
import lancedb

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    from app import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")

def test_query(q, doc_name, page_no):
    print(f"\n==============================================")
    print(f"QUERY: {q} | Using {doc_name} p.{page_no}")
    print(f"==============================================")
    chunks = table.search().where(f"source = '{doc_name}' AND page = {page_no}").to_list()
    context = "\n\n".join([f"[{c['source']} | पृष्ठ: {c['page']}]\n{c['text']}" for c in chunks])
    prompt = build_rag_prompt(context)
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": q}
    ]
    
    for model_name in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
        try:
            res = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=600
            )
            ans = res.choices[0].message.content.strip()
            print(f"\n--- MODEL: {model_name} ---")
            print(ans[:400])
        except Exception as e:
            print(f"Error on {model_name}: {e}")

test_query("Directors' Meeting Allowance", "Unified_directive_2082.pdf", 75)
test_query("qualification of compliance officer", "Unified_directive_2082.pdf", 173)
