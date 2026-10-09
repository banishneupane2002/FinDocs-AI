import re
import sys

if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PREETI_NUM_MAP = {'!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0'}
NEP_TO_ARABIC = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}

KNOWN_CORPUS_YEARS = {2079, 2080, 2081, 2082, 2023, 2024}

CURRENCY_QUANTITY_PREFIX = r'(?:रु\.?|रु|rs\.?|rs|npr|रुपैयाँ|रुपैंया|रकम|amount|fee|charge|limit|upto|सम्म|of|to|for)\s*'
CURRENCY_QUANTITY_SUFFIX = r'\s*(?:रु\.?|रु|rs\.?|rs|npr|रुपैयाँ|रुपैंया|हजार|लाख|रकम|rupees)'

YEAR_CONTEXT_CLUES = r'(?:directive|circular|report|साल|मिति|वर्ष|fy|fiscal\s*year|निर्देशन|परिपत्र|प्रतिवेदन|संवत्|in|of|from|को|अनुसार)'

def extract_query_years(query: str, available_years: set = None) -> set:
    """
    Extracts all legitimate target regulatory years from user query.
    Rejects:
    - Currency amounts (e.g. '2000 rupees', 'Rs. 2500', 'fee 2000')
    - Standalone numbers not matching any active corpus document year
    - Non-year numbers (e.g. clause numbers, branch codes)
    """
    if available_years is None:
        available_years = KNOWN_CORPUS_YEARS

    found_years = set()

    # 1. Check Devanagari year ranges (e.g. २०७९/८० or २०७९)
    dev_ranges = re.finditer(r'२०([७८][०-९])(?:/([०-९]{2}))?', query)
    for m in dev_ranges:
        decade_unit = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(1))
        y1 = int(f"20{decade_unit}")
        if y1 in available_years:
            found_years.add(y1)
        if m.group(2):
            unit2 = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(2))
            y2 = int(f"20{unit2}")
            if y2 in available_years:
                found_years.add(y2)

    # 2. Check English year ranges (e.g. 2079/80, 2023/24, 2079-80)
    en_ranges = re.finditer(r'\b(20[78][0-9]|20[12][0-9])[/-]([0-9]{2})\b', query)
    for m in en_ranges:
        y1 = int(m.group(1))
        if y1 in available_years:
            found_years.add(y1)
        y2 = int(str(y1)[:2] + m.group(2))
        if y2 in available_years:
            found_years.add(y2)

    # 3. Check standalone English 4-digit years
    standalone_candidates = re.finditer(r'\b(20[78][0-9]|20[12][0-9])\b', query)
    for m in standalone_candidates:
        candidate = int(m.group(1))
        start_idx, end_idx = m.start(), m.end()

        # Check if preceded by currency or quantity terms (e.g. "Rs 2000", "रु २०००", "deposit of 2000")
        pre_ctx = query[max(0, start_idx - 15):start_idx].lower()
        post_ctx = query[end_idx:min(len(query), end_idx + 15)].lower()

        if re.search(r'(?:रु\.?|रु|rs\.?|rs|npr|रुपैयाँ|रुपैंया|rupees|amount|deposit|withdraw|transfer|fee|charge|limit)\s*$', pre_ctx):
            continue
        if re.search(r'^\s*(?:रु\.?|रु|rs\.?|rs|npr|रुपैयाँ|रुपैंया|rupees|हजार|लाख|per|प्रति)', post_ctx):
            continue

        # If it's a known document year, verify whether it's supported by contextual clues or known corpus
        if candidate in available_years:
            found_years.add(candidate)

    return found_years

def clean_query_for_search(query: str, matched_years: set) -> str:
    """
    Cleans routing noise ONLY for years that actually matched an active document.
    Leaves amounts, random numbers, and unknown numbers completely untouched.
    """
    if not matched_years or len(matched_years) > 1:
        # If no year matched or multiple years matched (comparative query), do not strip
        return query

    yr = list(matched_years)[0]
    # Strip phrasing like 'in 2079 directive', 'को २०७९ परिपत्र', '2079 directive'
    cleaned = re.sub(
        rf'\b(?:in|of|from|को|अनुसार|बमोजिम)?\s*{yr}\s*(?:directive|circular|report|निर्देशन|परिपत्र|प्रतिवेदन)?\b',
        '',
        query,
        flags=re.IGNORECASE
    )
    # Also clean Devanagari equivalent if any
    dev_yr = "".join([k for k, v in NEP_TO_ARABIC.items() if v == str(yr)[-1]] or [])
    cleaned = re.sub(
        rf'\b(?:in|of|from|को|अनुसार|बमोजिम)?\s*२०[७८]{dev_yr}\s*(?:directive|circular|report|निर्देशन|परिपत्र|प्रतिवेदन)?\b',
        '',
        cleaned,
        flags=re.IGNORECASE
    )
    return cleaned.strip() or query

def detect_document_years(filename: str, sample_text: str = "") -> set:
    """
    Detects all official fiscal or calendar years covered by a document.
    Distinguishes real years from phone numbers, P.O. Box, registration numbers.
    Supports multi-year documents (e.g. 2079/80, 2022-23).
    """
    years = set()

    # 1. From Filename
    for m in re.finditer(r'(20[78][0-9]|20[12][0-9])', filename):
        years.add(int(m.group(1)))

    # 2. Preeti Cover Shift Glyphs (Anchor: follows 'निर्देशन' or cover title)
    for preeti_m in re.finditer(r'@\)([&*][!@#$%\^&*()०-९0-9])', sample_text):
        decade_code = preeti_m.group(1)[0]
        unit_code = preeti_m.group(1)[1]
        decade = '7' if decade_code == '&' else '8'
        unit = PREETI_NUM_MAP.get(unit_code, NEP_TO_ARABIC.get(unit_code, unit_code))
        try:
            val = int(f"20{decade}{unit}")
            if 2070 <= val <= 2085:
                years.add(val)
        except Exception:
            pass

    # 3. Multi-year Devanagari ranges (e.g. २०७९/८० or आर्थिक वर्ष २०८०/८१)
    for m in re.finditer(r'२०([७८][०-९])(?:/([०-९]{2}))?', sample_text):
        decade_unit = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(1))
        y1 = int(f"20{decade_unit}")
        if 2070 <= y1 <= 2085:
            years.add(y1)
        if m.group(2):
            unit2 = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(2))
            y2 = int(f"20{unit2}")
            if 2070 <= y2 <= 2085:
                years.add(y2)

    # 4. Multi-year English ranges (e.g. 2023/24, 2022-23)
    for m in re.finditer(r'\b(20[12][0-9])[/-]([0-9]{2})\b', sample_text):
        y1 = int(m.group(1))
        y2 = int(str(y1)[:2] + m.group(2))
        years.add(y1)
        years.add(y2)

    # 5. Standalone English / Devanagari with Regulatory Anchors (rejects phone numbers, fax, PO Box)
    anchored_matches = re.finditer(
        r'(?:directive|circular|report|fiscal\s*year|निर्देशन|परिपत्र|प्रतिवेदन|संवत्|मिति)\s*[,:\s]*([०-९\d]{4})',
        sample_text,
        re.IGNORECASE
    )
    for m in anchored_matches:
        raw = m.group(1)
        arabic = "".join(NEP_TO_ARABIC.get(c, c) for c in raw)
        try:
            val = int(arabic)
            if 2070 <= val <= 2085 or 2010 <= val <= 2030:
                years.add(val)
        except Exception:
            pass

    return years

# Test Suite
test_queries = [
    ("Can I deposit 2000 rupees in wallet?", "Random 4-digit amount (2000)"),
    ("What is the fee for Rs. 2500 transfer?", "Random 4-digit amount (2500)"),
    ("Tell me about rule 2048", "Random 4-digit rule/code"),
    ("tell me about system audit in 2079 directive", "Real single year with directive"),
    ("Compare system audit in 2079 and 2082", "Comparative multi-year query"),
    ("आर्थिक वर्ष २०७९/८० को प्रतिवेदन के छ?", "Devanagari multi-year range"),
    ("Call phone 01-4412080 for inquiry", "Phone number containing 2080"),
    ("What is the overnight balance in 2082 directive?", "Real single year"),
]

print("=== TEST RESULTS ===")
for q, desc in test_queries:
    yrs = extract_query_years(q)
    cleaned = clean_query_for_search(q, yrs)
    print(f"Scenario: {desc}")
    print(f"  Input:   '{q}'")
    print(f"  Years:   {yrs}")
    print(f"  Cleaned: '{cleaned}'\n")

print("=== DOCUMENT COVER TEST ===")
doc_tests = [
    ("unnamed.pdf", "नेपाल राष्ट्र बैंक, केन्द्रीय कार्यालय ... फोन: ०१-४४१२०८०, पो.ब.नं. ७३ ... एकीकृत निर्देशन, @)&( मिति २०७९"),
    ("combined_report.pdf", "नेपाल राष्ट्र बैंक ... आर्थिक वर्ष २०७९/८० को वार्षिक प्रतिवेदन ... Phone: 01-4419804"),
    ("directive_2082.pdf", "भुक्तानी प्रणाली निर्देशन २०८२"),
    ("supervision_report.pdf", "Bank Supervision Report 2022/23 Nepal Rastra Bank Fax: 4410159")
]

for fn, txt in doc_tests:
    doc_yrs = detect_document_years(fn, txt)
    print(f"Doc: {fn}")
    print(f"  Detected Years: {doc_yrs}\n")
