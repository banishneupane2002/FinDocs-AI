import os, sys

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search, expand_query_crosslingual
from core.routing import build_document_year_map, extract_query_years, clean_query_for_search
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db = lancedb.connect('lancedb_data')
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

q = "show me list of finance companies"
print("Query:", q)

doc_year_map = build_document_year_map(table)
available_years = set.union(*doc_year_map.values()) if doc_year_map else set()

matched_years = extract_query_years(q, available_years)
print("Matched years:", matched_years)

effective_doc = None
if len(matched_years) == 1:
    target_yr = list(matched_years)[0]
    matching_docs = [d for d, yrs in doc_year_map.items() if target_yr in yrs]
    if matching_docs:
        effective_doc = matching_docs if len(matching_docs) > 1 else matching_docs[0]
print("Effective doc:", effective_doc)

trans = expand_query_crosslingual(q, client)
print("Translated / Expanded terms:", trans)

results = hybrid_search(q, table, model, trans, selected_doc="All Documents", top_k=8)
print("\nRetrieved results (count = %d):" % len(results))
for i, r in enumerate(results, 1):
    print(f"Rank {i}: {r['source']} p.{r['page']} | snippet: {r['text'][:140].replace(chr(10), ' ')}")
