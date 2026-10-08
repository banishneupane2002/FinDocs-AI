import sys, os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('.'))

from scratch.test_accuracy15 import embedding_model, extract_meaningful_keywords, table

q7 = "In the FY 2024/25 stress testing results, how many Development Banks fail to meet the minimum Capital Adequacy Ratio under Credit Shock C1 (15% performing loans deteriorating into substandard)?"
k_target = ('Annual_Report_2025.pdf', 33)


q_vec = embedding_model.encode(q7).tolist()
d_pri = {}
for rank, (_, row) in enumerate(table.search(q_vec).limit(100).to_pandas().iterrows(), 1):
    k = (row['source'], int(row['page']))
    if k not in d_pri:
        d_pri[k] = (rank, row)

print("d_pri for p.33:", d_pri.get(k_target))

kw_pri = extract_meaningful_keywords(q7)
clean_pri_fts = " ".join([w for w in kw_pri if len(w) > 1])
s_pri = {}
for rank, (_, row) in enumerate(table.search(clean_pri_fts).limit(100).to_pandas().iterrows(), 1):
    k = (row['source'], int(row['page']))
    if k not in s_pri:
        s_pri[k] = (rank, row)

print("s_pri for p.33:", s_pri.get(k_target))
