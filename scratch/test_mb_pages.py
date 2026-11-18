import sys, os
sys.path.insert(0, os.path.abspath('.'))
import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search, expand_query_crosslingual
from app import GROQ_API_KEY
from groq import Groq

client = Groq(api_key=GROQ_API_KEY)
db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

q = 'mobile banking limit'
terms = expand_query_crosslingual(q, client)
print('Expanded terms:', terms)

results = hybrid_search(q, table, model, translated_terms=terms, selected_doc='All Documents', top_k=6)
for i, r in enumerate(results):
    src = r.get('source')
    pg = r.get('page')
    txt = r.get('text', '')[:120].replace('\n', ' ')
    print(f"#{i+1}: {src} p.{pg} -> {txt}")
