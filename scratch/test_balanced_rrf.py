import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import lancedb
from sentence_transformers import SentenceTransformer
from scratch.test_clean_fixes import clean_extract_keywords

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def balanced_search(user_query, trans_terms="", top_k=6):
    k_const = 30
    
    # In 'All Documents' mode for regulatory directives, filter or boost prevailing 2082
    where_prevailing = "source LIKE '%2082%'"
    
    # 1. Dense Pri (within prevailing 2082 directives for directive intent)
    d_pri = {}
    q_vec = model.encode(user_query).tolist()
    for rank, (_, row) in enumerate(table.search(q_vec).where(where_prevailing).limit(50).to_pandas().iterrows(), 1):
        k = (row['source'], int(row['page']))
        if k not in d_pri: d_pri[k] = (rank, row)

    # 2. Dense Trans (within prevailing 2082 directives)
    d_trans = {}
    if trans_terms.strip():
        t_vec = model.encode(trans_terms).tolist()
        for rank, (_, row) in enumerate(table.search(t_vec).where(where_prevailing).limit(50).to_pandas().iterrows(), 1):
            k = (row['source'], int(row['page']))
            if k not in d_trans: d_trans[k] = (rank, row)

    # 3. Sparse Pri
    s_pri = {}
    kw_pri = clean_extract_keywords(user_query)
    q_pri_clean = " ".join([w for w in kw_pri if len(w) > 1 or w in '०१२३४५६७८९0123456789'])
    if q_pri_clean.strip():
        for rank, (_, row) in enumerate(table.search(q_pri_clean).where(where_prevailing).limit(50).to_pandas().iterrows(), 1):
            k = (row['source'], int(row['page']))
            if k not in s_pri: s_pri[k] = (rank, row)

    # 4. Sparse Trans
    s_trans = {}
    if trans_terms.strip():
        kw_trans = clean_extract_keywords(trans_terms)
        q_trans_clean = " ".join([w for w in kw_trans if len(w) > 1 or w in '०१२३४५६७८९0123456789'])
        if q_trans_clean.strip():
            for rank, (_, row) in enumerate(table.search(q_trans_clean).where(where_prevailing).limit(50).to_pandas().iterrows(), 1):
                k = (row['source'], int(row['page']))
                if k not in s_trans: s_trans[k] = (rank, row)

    rrf = {}
    for k in set(d_pri.keys()) | set(d_trans.keys()) | set(s_pri.keys()) | set(s_trans.keys()):
        score = 0.0
        row = None
        if k in d_pri:
            score += 1.0 / (k_const + d_pri[k][0])
            row = d_pri[k][1]
        if k in d_trans:
            score += 1.2 / (k_const + d_trans[k][0])
            if row is None: row = d_trans[k][1]
        if k in s_pri:
            score += 1.5 / (k_const + s_pri[k][0])
            if row is None: row = s_pri[k][1]
        if k in s_trans:
            score += 1.8 / (k_const + s_trans[k][0])
            if row is None: row = s_trans[k][1]
        rrf[k] = (score, row)

    sorted_res = sorted(rrf.values(), key=lambda x: x[0], reverse=True)
    return [r[1].to_dict() for r in sorted_res[:top_k] if r[1] is not None]

# Test on Q11 and Q5 with top_k=6 ONLY (no token bloat!)
print("--- Q11 Balanced Search (top_k=6) ---")
q11 = "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?"
t11 = "Margin Lending, मार्जिन कर्जा, शेयर धितो कर्जा, ७० प्रतिशत, १८० दिन"
res11 = balanced_search(q11, t11, top_k=6)
for idx, r in enumerate(res11, 1):
    target = " *** TARGET PAGE 23 ***" if r['page'] == 23 else ""
    print(f"  {idx}: {r['source']} P{r['page']}{target}")

print("\n--- Q5 Balanced Search (top_k=6) ---")
q5 = "What is the minimum Statutory Liquidity Ratio (SLR) and Cash Reserve Ratio (CRR) required for a 'C' class finance company?"
t5 = "अनिवार्य नगद मौज्दात, ४ प्रतिशत, वैधानिक तरलता अनुपात, १० प्रतिशत"
res5 = balanced_search(q5, t5, top_k=6)
for idx, r in enumerate(res5, 1):
    target118 = " *** TARGET PAGE 118 (CRR 4%) ***" if r['page'] == 118 else ""
    target120 = " *** TARGET PAGE 120 (SLR 10%) ***" if r['page'] == 120 else ""
    print(f"  {idx}: {r['source']} P{r['page']}{target118}{target120}")

print("\n--- Q6 Balanced Search (top_k=6) ---")
q6 = "When calculating the Capital Adequacy Ratio (CAR), what is the risk weight assigned to loans secured by residential properties?"
t6 = "residential properties, risk weight, 60%, Capital Adequacy Framework"
res6 = balanced_search(q6, t6, top_k=6)
for idx, r in enumerate(res6, 1):
    target225 = " *** TARGET PAGE 225 (60%) ***" if r['page'] == 225 else ""
    print(f"  {idx}: {r['source']} P{r['page']}{target225}")

