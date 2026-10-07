import sys
sys.stdout.reconfigure(encoding='utf-8')
import lancedb
from sentence_transformers import SentenceTransformer
from groq import Groq
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.strip().split("=", 1)[1].strip()

import ask

print("Testing hybrid_search on 'What agreement must a bank make with a customer for branchless banking?'...")
terms = ask.expand_query_crosslingual("What agreement must a bank make with a customer for branchless banking?", ask.client)
print(f"Translated terms: {terms}")

results = ask.hybrid_search("What agreement must a bank make with a customer for branchless banking?", ask.table, ask.embedding_model, translated_terms=terms, top_k=4)
print(f"Retrieved {len(results)} results:")
for r in results:
    print(f" - [{r['source']} - Page {r['page']}] Score: {r['score']:.3f} | {r['text'][:80].replace(chr(10), ' ')}")

