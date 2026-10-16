import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Let's inspect where Page 225 and Page 23 sit in the sorted RRF list BEFORE diversity capping:
q6 = "When calculating the Capital Adequacy Ratio (CAR), what is the risk weight assigned to loans secured by residential properties?"
q11 = "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?"

from core.search import extract_meaningful_keywords, build_where_filter

def inspect_uncapped_rrf(q, trans=""):
    print(f"\nQuery: {q}")
    k_const = 30
    q_vec = model.encode(q).tolist()
    d_pri = { (r['source'], int(r['page'])): (rank, r) for rank, (_, r) in enumerate(tbl.search(q_vec).limit(100).to_pandas().iterrows(), 1) }
    
    kw_pri = extract_meaningful_keywords(q)
    clean_pri_fts = " ".join([w for w in kw_pri if len(w) > 1 or w in '०१२३४५६७८९0123456789'])
    s_pri = {}
    if clean_pri_fts.strip():
        for rank, (_, r) in enumerate(tbl.search(clean_pri_fts).limit(100).to_pandas().iterrows(), 1):
            k = (r['source'], int(r['page']))
            if k not in s_pri: s_pri[k] = (rank, r)
            
    rrf = {}
    for k in set(d_pri.keys()) | set(s_pri.keys()):
        score = 0.0
        row = None
        if k in d_pri:
            score += 1.0 / (k_const + d_pri[k][0])
            row = d_pri[k][1]
        if k in s_pri:
            score += 1.3 / (k_const + s_pri[k][0])
            if row is None: row = s_pri[k][1]
        if '2082' in k[0]:
            score *= 1.5
        rrf[k] = (score, row)
        
    sorted_items = sorted(rrf.items(), key=lambda x: x[1][0], reverse=True)
    print("Top 15 uncapped candidates:")
    for rank, (k, (score, row)) in enumerate(sorted_items[:15], 1):
        target = " *** TARGET ***" if (k[1] in [225, 23, 118] and '2082' in k[0]) else ""
        print(f"  {rank}: {k[0]} page {k[1]} score={score:.4f}{target}")

inspect_uncapped_rrf(q6)
inspect_uncapped_rrf(q11, trans="मार्जिन कर्जा, शेयर धितो कर्जा, ७० प्रतिशत")

