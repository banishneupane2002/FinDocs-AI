import time
print("Starting import tests...", flush=True)

t0 = time.time()
import lancedb
print("lancedb imported in", time.time() - t0, flush=True)

t0 = time.time()
import core.routing
print("core.routing imported in", time.time() - t0, flush=True)

t0 = time.time()
import core.preeti
print("core.preeti imported in", time.time() - t0, flush=True)

t0 = time.time()
import core.search
print("core.search imported in", time.time() - t0, flush=True)

t0 = time.time()
from sentence_transformers import SentenceTransformer
print("sentence_transformers imported in", time.time() - t0, flush=True)
