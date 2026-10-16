import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import lancedb, numpy as np
from sentence_transformers import SentenceTransformer

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
tbl = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

t11 = "मार्जिन कर्जा, शेयर धितो कर्जा, ७० प्रतिशत, १८० दिन"
q_vec = np.array(model.encode(t11))

df23 = tbl.search().where("source = 'Unified_directive_2082.pdf' AND page = 23").select(['text', 'vector']).to_pandas()
for i, r in df23.iterrows():
    d = np.linalg.norm(q_vec - np.array(r['vector']))
    print(f"Chunk {i}: dist = {d:.4f}")
    print(f"  Text: {r['text'][:120]}...\n")

