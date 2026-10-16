"""
Fiscal year detection, multi-year query parsing, and document auto-routing engine.
"""

import re

PREETI_NUM_MAP = {'!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0'}
NEP_TO_ARABIC = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
ARABIC_TO_NEP = {v: k for k, v in NEP_TO_ARABIC.items()}

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

def extract_query_years(query: str, available_years: set = None) -> set:
    """
    Extracts all legitimate target regulatory years from user query.
    Rejects:
    - Currency amounts (e.g. '2000 rupees', 'Rs. 2500', 'fee 2000')
    - Standalone numbers not matching any active corpus document year
    - Non-year numbers (e.g. clause numbers, branch codes)
    """
    if not query:
        return set()

    if available_years is None:
        available_years = {2079, 2080, 2081, 2082, 2023, 2024}

    found_years = set()

    # 1. Check Devanagari year ranges (e.g. २०७९/८०, २०८०, or Gregorian २०२४, २०२५)
    dev_ranges = re.finditer(r'२०([०-९]{2})(?:/([०-९]{2}))?', query)
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

        if re.search(r'(?:रु\.?|रु|rs\.?|rs|npr|रुपैयाँ|रुपैंया|rupees)\s*$', pre_ctx):
            continue
        if re.search(r'^\s*(?:रु\.?|रु|rs\.?|rs|npr|रुपैयाँ|रुपैंया|rupees|हजार|लाख)', post_ctx):
            continue

        # If it's a known document year in the corpus, add it
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
    cleaned = re.sub(
        rf'\b(?:in|of|from|को|अनुसार|बमोजिम)?\s*{yr}\s*(?:directive|circular|report|निर्देशन|परिपत्र|प्रतिवेदन)?\b',
        '',
        query,
        flags=re.IGNORECASE
    )
    dev_yr_full = "".join(ARABIC_TO_NEP.get(c, c) for c in str(yr))
    cleaned = re.sub(
        rf'\b(?:in|of|from|को|अनुसार|बमोजिम)?\s*{dev_yr_full}\s*(?:directive|circular|report|निर्देशन|परिपत्र|प्रतिवेदन)?\b',
        '',
        cleaned,
        flags=re.IGNORECASE
    )
    return cleaned.strip() or query

def prioritize_matching_document(target_yr: int, matching_docs: list) -> str:
    """
    Selects the best document when multiple reports cover the target year.
    Prioritizes:
    1. Document with target_yr in filename (e.g. Annual_Report_2024.pdf for 2024)
    2. Primary reporting period over comparative retrospective years.
    """
    if not matching_docs:
        return None
    for doc in matching_docs:
        if str(target_yr) in doc:
            return doc
    return matching_docs[0]

_DOC_YEAR_CACHE = {}

def build_document_year_map(table) -> dict:
    """Builds a cached map of document name -> set of detected fiscal/calendar years."""
    global _DOC_YEAR_CACHE
    if _DOC_YEAR_CACHE:
        return _DOC_YEAR_CACHE
    doc_map = {}
    try:
        df = table.search().where("page <= 3").select(["source", "page", "text"]).to_pandas()
        for s in df['source'].unique():
            p1_records = df[df['source'] == s]
            sample_text = " ".join(p1_records['text'].tolist())
            doc_map[s] = detect_document_years(s, sample_text)
        _DOC_YEAR_CACHE = doc_map
    except Exception:
        pass
    return doc_map

