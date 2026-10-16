import os, sys
sys.path.insert(0, os.getcwd())
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search, expand_query_crosslingual
from dotenv import load_dotenv
load_dotenv()
from groq import Groq

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Test 1: Newest commercial bank (Report intent)
q_rep = "newest commercial bank"
trans_rep = expand_query_crosslingual(q_rep, groq_client)
print("--- TEST 1: Report Intent Query ---")
print("Q:", q_rep)
print("Trans:", trans_rep)
res_rep = hybrid_search(q_rep, tbl, model, translated_terms=trans_rep, selected_doc="All Documents", top_k=6)
for i, r in enumerate(res_rep):
    print(f"  {i+1}: {r['source']} page {r['page']}")

# Test 2: Margin Lending LTV (Directive intent)
q_dir = "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?"
trans_dir = expand_query_crosslingual(q_dir, groq_client)
print("\n--- TEST 2: Directive Intent Query ---")
print("Q:", q_dir)
print("Trans:", trans_dir)
res_dir = hybrid_search(q_dir, tbl, model, translated_terms=trans_dir, selected_doc="All Documents", top_k=8)
for i, r in enumerate(res_dir):
    print(f"  {i+1}: {r['source']} page {r['page']}")

