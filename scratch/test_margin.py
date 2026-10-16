import lancedb, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

q = "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?"
trans = "Margin Lending, शेयर धितो कर्जा, मार्जिन कर्जा, ७० प्रतिशत, १८० दिन, बजार मूल्य"

# Let's inspect the 4 passes individually
where_filter = None
q_vec = model.encode(q).tolist()
res_d_pri = tbl.search(q_vec).limit(100).to_pandas()
print("d_pri rank of page 23 in 2082:", res_d_pri[(res_d_pri['source']=='Unified_directive_2082.pdf') & (res_d_pri['page']==23)].index.tolist())

t_vec = model.encode(trans).tolist()
res_d_trans = tbl.search(t_vec).limit(100).to_pandas()
print("d_trans rank of page 23 in 2082:", res_d_trans[(res_d_trans['source']=='Unified_directive_2082.pdf') & (res_d_trans['page']==23)].index.tolist())

from core.lexicon import extract_meaningful_keywords
pri_kw = extract_meaningful_keywords(q)
clean_pri_fts = " ".join([w for w in pri_kw if len(w) > 1])
res_f_pri = tbl.search(clean_pri_fts).limit(100).to_pandas()
print("f_pri query:", clean_pri_fts)
print("f_pri rank of page 23 in 2082:", res_f_pri[(res_f_pri['source']=='Unified_directive_2082.pdf') & (res_f_pri['page']==23)].index.tolist())

res = hybrid_search(q, tbl, model, translated_terms=trans, selected_doc="All Documents", top_k=15)
print("\n=== TOP 15 HYBRID SEARCH RESULTS ===")
for i, r in enumerate(res):
    print(f"{i+1}: {r['source']} page {r['page']}")



