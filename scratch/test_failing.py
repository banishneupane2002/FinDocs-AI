import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

import lancedb
from sentence_transformers import SentenceTransformer
from core.search import hybrid_search
from core.preeti import decode_preeti_text

db = lancedb.connect('lancedb_data')
table = db.open_table('bank_documents')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

test_cases = [
    ("Q3", "If a borrower is blacklisted by the Credit Information Bureau (CIC), how should we classify their loan and what provision is needed?",
     "कालोसूचीमा कायम खराब वर्ग वर्गीकरण, खराब कर्जा १०० प्रतिशत कर्जा नोक्सानी व्यवस्था"),
    ("Q5", "What is the minimum Statutory Liquidity Ratio (SLR) and Cash Reserve Ratio (CRR) required for a 'C' class finance company?",
     "४ प्रतिशत अनिवार्य नगद मौज्दात, १० प्रतिशत वैधानिक तरलता अनुपात"),
    ("Q17", "What is the minimum default loan amount and days past due required for recommending a borrower for blacklisting to CIC?",
     "कालोसूचीमा समावेश दश लाख कर्जा सूचना केन्द्र, १० लाख, ९० दिन"),
    ("Q18", "What is the per-day transaction limit for person-to-merchant (QR code) payments through mobile banking?",
     "मोबाइल बैंकिङ्ग क्युआर कोड, ३ लाख प्रतिदिन, ३,००,०००")
]

for qid, query, trans in test_cases:
    results = hybrid_search(query, table, model, translated_terms=trans, selected_doc="All Documents", top_k=6)
    print(f"\n--- {qid} ---")
    for r in results:
        print(f"{r['source']} Page {r['page']}")

