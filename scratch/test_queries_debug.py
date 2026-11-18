import sys, os
sys.path.insert(0, os.path.abspath('.'))
import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search, build_where_filter, expand_query_crosslingual
from core.routing import extract_query_years, build_document_year_map, extract_target_directive_number

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
    
    # 1. Check target directive number
    target_dir = extract_target_directive_number(q)
    print(f"Target directive number: {target_dir}")
    
    # 2. Check translation / expansion (client=None uses local fallback/lexicon)
    terms = expand_query_crosslingual(q, client=None)
    print(f"Expanded terms: {terms}")
    
    # 3. Hybrid search
    results = hybrid_search(q, table, model, translated_terms=terms, selected_doc="All Documents", top_k=6)
    print(f"\nTop {len(results)} retrieved chunks:")
    for i, r in enumerate(results):
        src = r.get('source', '')
        pg = r.get('page', 0)
        score = r.get('score', 0)
        txt = r.get('text', '')[:180].replace('\n', ' ')
        print(f"  #{i+1}: {src} (p.{pg}) [score: {score:.4f}] -> {txt}...")
