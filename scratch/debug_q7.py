import lancedb
import sys, os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('.'))

from scratch.test_accuracy15 import embedding_model, extract_meaningful_keywords, table

q7 = "In the FY 2024/25 stress testing results, how many Development Banks fail to meet the minimum Capital Adequacy Ratio under Credit Shock C1 (15% performing loans deteriorating into substandard)?"

kw = extract_meaningful_keywords(q7)
clean_fts = " ".join([w for w in kw if len(w) > 1])
print("FTS query:", clean_fts)

fts_res = table.search(clean_fts).limit(10).to_pandas()
print("\n--- FTS TOP 10 ---")
for rank, (_, r) in enumerate(fts_res.iterrows(), 1):
    print(f"{rank}. {r['source']} p.{r['page']} | {r['text'][:70].replace('\n', ' ')}")

vec = embedding_model.encode(q7).tolist()
dense_res = table.search(vec).limit(10).to_pandas()
print("\n--- DENSE TOP 10 ---")
for rank, (_, r) in enumerate(dense_res.iterrows(), 1):
    print(f"{rank}. {r['source']} p.{r['page']} | {r['text'][:70].replace('\n', ' ')}")

