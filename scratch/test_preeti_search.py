import lancedb
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

test_terms = [
    'ऋऋत्ख्', # CCTV
    'ँयचअभ', # Force
    'क्भततभिफभलत', # Settlement
    'त्ंघ', # T+3
    'त्ंज्ञ', # T+1
    'क्ष्धँत्', # IBFT
    'क्थकतभफ', # System
    'ब्गमष्त', # Audit
    'ग्क्क्म्', # USSD
    'सरलीकृत', # Simplified
    'मचर्ेन्ट', # Merchant
    'सीमा कारोबार', # TTR
    'goAML',
    'नब्बे'
]

for term in test_terms:
    res = t.search(term).limit(3).to_pandas()
    sources = [f"{r['source']} p.{r['page']}" for _, r in res.iterrows()]
    print(f"'{term}' -> {sources}")

