import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import lancedb
from scratch.test_all_20_optimized import clean_extract_keywords

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')

trans_tests = {
    "Q11": ["शेयर धितो कर्जा ७० प्रतिशत १८० दिन", "Margin Lending"],
    "Q5": ["वैधानिक तरलता अनुपात १० प्रतिशत", "अनिवार्य नगद मौज्दात ४ प्रतिशत"],
    "Q3": ["कालोसूची खराब वर्ग", "१०० प्रतिशत कर्जा नोक्सानी व्यवस्था"]
}

for qid, phrases in trans_tests.items():
    print(f"\n=== {qid} ===")
    for p in phrases:
        kw = clean_extract_keywords(p)
        clean_fts = " ".join([w for w in kw if len(w) > 1 or w in '०१२३४५६७८९0123456789'])
        res = table.search(clean_fts).limit(3).to_pandas()
        print(f"Phrase '{clean_fts}':")
        for idx, (_, r) in enumerate(res.iterrows(), 1):
            print(f"  {idx}: {r['source']} P{r['page']} score={r['_score']:.2f}")

