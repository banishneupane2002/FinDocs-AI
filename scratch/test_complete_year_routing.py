import sys, os, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import app

PREETI_NUM_MAP = {'!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0'}
NEP_TO_ARABIC = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}

def detect_document_year(filename: str, sample_text: str = "") -> int:
    fn_m = re.search(r'(20[5-9][0-9]|20[0-4][0-9])', filename)
    if fn_m:
        return int(fn_m.group(1))

    preeti_m = re.search(r'@\)([&*][!@#$%\^&*()०-९0-9])', sample_text)
    if preeti_m:
        decade_code = preeti_m.group(1)[0]
        unit_code = preeti_m.group(1)[1]
        decade = '7' if decade_code == '&' else '8'
        unit = PREETI_NUM_MAP.get(unit_code, NEP_TO_ARABIC.get(unit_code, unit_code))
        try:
            return int(f"20{decade}{unit}")
        except Exception:
            pass

    dev_m = re.search(r'२०([७८][०-९])', sample_text)
    if dev_m:
        decade_unit = "".join(NEP_TO_ARABIC.get(c, c) for c in dev_m.group(1))
        return int(f"20{decade_unit}")

    ascii_m = re.search(r'\b(20[78][0-9]|20[12][0-9])\b', sample_text)
    if ascii_m:
        return int(ascii_m.group(1))

    return 0

def extract_query_year(query: str) -> int:
    dev_m = re.search(r'२०([७८][०-९])', query)
    if dev_m:
        nep_to_ar = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
        decade_unit = "".join(nep_to_ar.get(c, c) for c in dev_m.group(1))
        return int(f"20{decade_unit}")
    ar_m = re.search(r'\b(20[5-9][0-9]|20[0-4][0-9])\b', query)
    if ar_m:
        return int(ar_m.group(1))
    return 0

def clean_routing_noise(query: str) -> str:
    return re.sub(r'\b(in|of|from|को|अनुसार)?\s*(20[5-9][0-9]|20[0-4][0-9]|२०[७८][०-९])\s*(directive|circular|report|निर्देशन|परिपत्र|प्रतिवेदन)?\b', '', query, flags=re.IGNORECASE).strip()

def build_document_year_map(table) -> dict:
    doc_map = {}
    try:
        df = table.to_pandas()
        for s in df['source'].unique():
            fn_m = re.search(r'(20[5-9][0-9]|20[0-4][0-9])', s)
            if fn_m:
                doc_map[s] = int(fn_m.group(1))
            else:
                p1_records = df[(df['source'] == s) & (df['page'] <= 3)]
                sample_text = " ".join(p1_records['text'].tolist())
                doc_map[s] = detect_document_year(s, sample_text)
    except Exception as e:
        print("Error building map:", e)
    return doc_map

print("Building doc year map...")
doc_map = build_document_year_map(app.table)
for d, y in sorted(doc_map.items()):
    print(f"  {d:<25} -> Year: {y}")

test_queries = [
    "tell me about system audit in 2079 directive",
    "२०८० को परिपत्र अनुसार वालेटको सीमा कति छ?",
    "What was the total profit in 2024 annual report?",
    "What is the daily transaction limit in an e-wallet?"
]

print("\nTesting Query Routing:")
for q in test_queries:
    y = extract_query_year(q)
    cleaned = clean_routing_noise(q)
    matched = [d for d, yr in doc_map.items() if yr == y]
    print(f"\nQuery: {repr(q)}")
    print(f"  Target Year : {y}")
    print(f"  Clean Query : {repr(cleaned)}")
    print(f"  Auto Routed : {matched or 'All Documents (No Year Constraint)'}")

