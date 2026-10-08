import sys, os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('.'))

from scratch.run_eval_full15 import hybrid_search, table, embedding_model

q4 = "Under NRB regulations, which Capital Adequacy Framework applies to national-level Development Banks versus regional-level Development Banks and Finance Companies?"

res = hybrid_search(q4, table, embedding_model, top_k=6)
for rank, r in enumerate(res, 1):
    print(f"Rank {rank}: {r['source']} p.{r['page']} score={r['score']}")

