import sys, os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('.'))

from scratch.test_accuracy15 import test_search, q7

res = test_search(q7, top_k=6)
for rank, r in enumerate(res, 1):
    print(f"Rank {rank}: {r['source']} p.{r['page']} score={r['score']}")

