import os, sys
sys.path.insert(0, os.path.abspath("."))
import inspect_context

q = "In the FY 2024/25 stress testing results, how many Development Banks fail to meet the minimum Capital Adequacy Ratio under Credit Shock C1 (15% performing loans deteriorating into substandard)?"
hits = inspect_context.offline_hybrid_retrieve(q, top_k=15)
for i, h in enumerate(hits, 1):
    print(f"{i}. {h['source']} p.{h['page']} score: {round(h['score'], 4)}")

