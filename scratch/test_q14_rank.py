import os, sys
sys.path.insert(0, os.path.abspath("."))
import inspect_context

q = "Under what conditions must a Threshold Transaction Report (TTR) be submitted to the FIU, and what is the reporting deadline and required platform?"
hits = inspect_context.offline_hybrid_retrieve(q, top_k=10)
for i, h in enumerate(hits, 1):
    print(f"{i}. {h['source']} p.{h['page']} score: {round(h['score'], 4)}")

