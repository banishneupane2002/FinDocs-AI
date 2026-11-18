import os, sys
sys.path.insert(0, os.path.abspath('.'))
from groq import Groq
from core.search import expand_query_crosslingual, hybrid_search
import lancedb
from sentence_transformers import SentenceTransformer

from app import GROQ_API_KEY
client = Groq(api_key=GROQ_API_KEY)
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

queries = [
    "qualification of compliance officer",
    "Directors' Meeting Allowance"
]

for q in queries:
    print(f"\n==========================================")
    print(f"QUERY: {q}")
    print(f"==========================================")
    terms = expand_query_crosslingual(q, client=client)
    print(f"Groq expanded terms: {terms}")
    
    results = hybrid_search(q, table, model, translated_terms=terms, selected_doc="All Documents", top_k=6)
    print(f"\nTop {len(results)} retrieved chunks with Groq expansion:")
    for i, r in enumerate(results):
        src = r.get('source', '')
        pg = r.get('page', 0)
        score = r.get('score', 0)
        txt = r.get('text', '')[:140].replace('\n', ' ')
        print(f"  #{i+1}: {src} (p.{pg}) [score: {score:.4f}] -> {txt}...")
