import sys, os, re
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import lancedb
from sentence_transformers import SentenceTransformer

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def split_compound_query(q: str) -> list[str]:
    """Splits compound queries containing 'and', 'or', 'तथा', 'र' into sub-queries without LLM calls."""
    # Pattern to detect compound subjects like "CRR and SLR", "agriculture and MSME"
    delims = r'\s+(?:and|तथा|र|as well as)\s+|,\s*'
    parts = re.split(delims, q, flags=re.IGNORECASE)
    cleaned = [p.strip() for p in parts if len(p.strip()) > 3]
    return cleaned if len(cleaned) > 1 else [q]

q5 = "What is the minimum Statutory Liquidity Ratio (SLR) and Cash Reserve Ratio (CRR) required for a 'C' class finance company?"
parts = split_compound_query(q5)
print("Split parts:", parts)

# Search each part in LanceDB FTS
for p in parts:
    print(f"\n--- Searching sub-clause: '{p}' ---")
    res = table.search(p).limit(5).to_pandas()
    for _, r in res.iterrows():
        print(f"  {r['source']} P{r['page']} score={r['_score']:.2f}")

