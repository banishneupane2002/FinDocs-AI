"""
Fiscal year detection, multi-year query parsing, and document auto-routing engine.
"""

import re

PREETI_NUM_MAP = {'!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0'}
NEP_TO_ARABIC = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
ARABIC_TO_NEP = {v: k for k, v in NEP_TO_ARABIC.items()}

NEPALI_MONTHS_MAP = {
    'बैशाख': 1, 'वैशाख': 1, 'baisakh': 1, 'baishakh': 1,
    'जेठ': 2, 'ज्येष्ठ': 2, 'jestha': 2, 'jeth': 2,
    'असार': 3, 'आषाढ': 3, 'ashad': 3, 'asar': 3,
    'साउन': 4, 'श्रावण': 4, 'shrawan': 4, 'saun': 4,
    'भदौ': 5, 'भाद्र': 5, 'bhadra': 5, 'bhadau': 5,
    'असोज': 6, 'आश्विन': 6, 'asoj': 6, 'ashwin': 6,
    'कात्तिक': 7, 'कार्तिक': 7, 'kartik': 7,
    'मंसिर': 8, 'मङ्सिर': 8, 'मार्ग': 8, 'mangsir': 8,
    'पुस': 9, 'पौष': 9, 'poush': 9, 'pus': 9,
    'माघ': 10, 'magh': 10,
    'फागुन': 11, 'फाल्गुन': 11, 'falgun': 11, 'fagun': 11,
    'चैत': 12, 'चैत्र': 12, 'chaitra': 12, 'chait': 12
}

def parse_nepali_date(query: str):
    """Parses Bikram Sambat dates in numeric YYYY/MM/DD or textual YYYY Month DD format."""
    q = query.lower()
    norm_q = "".join(NEP_TO_ARABIC.get(c, c) for c in q)
    m1 = re.search(r'\b(20[5-9][0-9])[/-](0?[1-9]|1[0-2])[/-](0?[1-9]|[12][0-9]|3[0-2])\b', norm_q)
    if m1:
        return int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
    for mname, mnum in NEPALI_MONTHS_MAP.items():
        pat = rf'\b(20[5-9][0-9])\s+{re.escape(mname)}\s+(0?[1-9]|[12][0-9]|3[0-2])\b'
        m2 = re.search(pat, norm_q)
        if m2:
            return int(m2.group(1)), mnum, int(m2.group(2))
    return None

def extract_target_directive_number(query: str) -> int | None:
    """Extracts explicit directive number requested by the user, e.g. Directive 2, निर्देशन नं. २, Directive 17."""
    m = re.search(r'\b(?:directive|निर्देशन|lgb\]\{zg)\s*(?:नं\.?|no\.?|number)?\s*([०-९0-9]+)\b', query, re.IGNORECASE)
    if m:
        num_str = "".join(NEP_TO_ARABIC.get(ch, ch) for ch in m.group(1))
        try:
            val = int(num_str)
            if 1 <= val <= 30:
                return val
        except Exception:
            pass
    return None

UNIFIED_DIRECTIVE_PAGE_RANGES_2082 = {
    1: (5, 6),       # Capital Adequacy
    2: (7, 35),      # Loan Classification & Provisioning
    3: (36, 42),     # Single Obligor Limit
    4: (43, 48),     # Accounting Policies & Financial Reporting
    5: (49, 56),     # Risk Management
    6: (57, 77),     # Corporate Governance
    7: (78, 80),     # Supervisory Implementation Schedule
    8: (81, 87),     # Investment & Subsidiaries
    9: (88, 88),     # Statistical Reporting
    10: (89, 98),    # Promoter Shares transfer & Non-Banking Assets
    11: (99, 103),   # Consortium Lending
    12: (104, 117),  # Credit Information & Blacklisting
    13: (118, 121),  # CRR & SLR
    14: (122, 131),  # Branch Network
    15: (132, 137),  # Interest Rates, Spread & Fees
    16: (138, 145),  # Financial Resources & Deposits
    17: (146, 154),  # Deprived Sector & Specified Sector Lending
    18: (155, 161),  # Upgradation & Mergers
    19: (162, 177),  # AML / CFT & KYC
    20: (178, 183),  # Consumer Protection & Financial Literacy
    21: (184, 198),  # Miscellaneous
}

def detect_document_years(filename: str, sample_text: str = "") -> set:
    """
    Detects all official fiscal or calendar years covered by a document.
    Distinguishes real years from phone numbers, P.O. Box, registration numbers.
    Supports multi-year documents (e.g. 2079/80, 2022-23).
    """
    years = set()

    # 1. From Filename
    for m in re.finditer(r'(20[5-9][0-9]|20[0-4][0-9])', filename):
        years.add(int(m.group(1)))

    # 2. Preeti Cover Shift Glyphs (Anchor: follows 'निर्देशन' or cover title)
    for preeti_m in re.finditer(r'@\)([&*][!@#$%\^&*()०-९0-9])', sample_text):
        decade_code = preeti_m.group(1)[0]
        unit_code = preeti_m.group(1)[1]
        decade = '7' if decade_code == '&' else '8'
        unit = PREETI_NUM_MAP.get(unit_code, NEP_TO_ARABIC.get(unit_code, unit_code))
        try:
            val = int(f"20{decade}{unit}")
            if 2050 <= val <= 2100:
                years.add(val)
        except Exception:
            pass

    # 3. Multi-year Devanagari ranges (e.g. २०७९/८० or आर्थिक वर्ष २०८०/८१)
    for m in re.finditer(r'२०([७८][०-९])(?:/([०-९]{2}))?', sample_text):
        decade_unit = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(1))
        y1 = int(f"20{decade_unit}")
        if 2050 <= y1 <= 2100:
            years.add(y1)
        if m.group(2):
            unit2 = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(2))
            y2 = int(f"20{unit2}")
            if 2050 <= y2 <= 2100:
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
            if 2050 <= val <= 2100 or 1990 <= val <= 2050:
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

    import os
    if available_years is None or not available_years:
        available_years = set()
        if os.path.exists("File_System"):
            for f in os.listdir("File_System"):
                for m in re.finditer(r'(20[5-9][0-9]|20[0-4][0-9])', f):
                    available_years.add(int(m.group(1)))
        if not available_years:
            available_years = {int(m.group(1)) for m in re.finditer(r'\b(20[5-9][0-9]|20[0-4][0-9])\b', query)}

    found_years = set()

    # 0. Check Specific Nepali Date Formats (e.g. 2082/2/12, 2082-02-12, or 2082 jestha 12)
    dt = parse_nepali_date(query)
    if dt:
        yr = dt[0]
        if yr in available_years:
            found_years.add(yr)

    # 1. Check Devanagari year ranges (e.g. २०७९/८०, २०८०, or Gregorian २०२४, २०२५)
    dev_ranges = re.finditer(r'२०([०-९]{2})(?:/([०-९]{2}))?(?![/-][०-९])', query)
    for m in dev_ranges:
        decade_unit = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(1))
        y1 = int(f"20{decade_unit}")
        if m.group(2):
            unit2 = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(2))
            y2 = int(f"20{unit2}")
            # Slash range YYYY/YY always targets the closing publication year y2
            if y2 in available_years:
                found_years.add(y2)
            elif y1 in available_years:
                found_years.add(y1)
        else:
            if y1 in available_years:
                found_years.add(y1)

    # 2. Check English year ranges (e.g. 2079/80, 2023/24, 2024/25)
    en_ranges = re.finditer(r'\b(20[5-9][0-9]|20[0-4][0-9])[/-]([0-9]{2})\b(?![/-]\d)', query)
    for m in en_ranges:
        y1 = int(m.group(1))
        y2 = int(str(y1)[:2] + m.group(2))
        # Slash range YYYY/YY always targets the closing publication year y2
        if y2 in available_years:
            found_years.add(y2)
        elif y1 in available_years:
            found_years.add(y1)

    # 3. Check standalone English 4-digit years
    standalone_candidates = re.finditer(r'\b(20[5-9][0-9]|20[0-4][0-9])\b', query)
    for m in standalone_candidates:
        start_idx, end_idx = m.start(), m.end()

        # Reject if adjacent to '/' or '-' (which means it's part of a fiscal year range e.g. 2024/25)
        if (start_idx > 0 and query[start_idx-1] in ['/', '-']) or (end_idx < len(query) and query[end_idx] in ['/', '-']):
            continue

        candidate = int(m.group(1))

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
        return query

    # If the query contains a specific date (e.g. 2082/2/12 or 2082 jestha 12), preserve the date intact!
    if re.search(r'\b20[5-9][0-9][/-]\d{1,2}[/-]\d{1,2}\b', query) or any(m in query.lower() for m in NEPALI_MONTHS_MAP):
        return query

    yr = list(matched_years)[0]
    yr_short = str(yr)[2:]
    cleaned = re.sub(
        rf'\b(?:in(?:\s+the)?|of(?:\s+the)?|from|को|अनुसार|बमोजिम)?\s*(?:(?:20\d{{2}}|२०[०-९]{{2}})[/-])?(?:{yr}|{yr_short})\s*(?:directive|circular|report|supervision\s*report|सुपरीवेक्षण\s*प्रतिवेदन|निर्देशन|परिपत्र|प्रतिवेदन)?\b',
        ' ',
        query,
        flags=re.IGNORECASE
    )
    dev_yr_full = "".join(ARABIC_TO_NEP.get(c, c) for c in str(yr))
    dev_yr_short = "".join(ARABIC_TO_NEP.get(c, c) for c in yr_short)
    cleaned = re.sub(
        rf'\b(?:in(?:\s+the)?|of(?:\s+the)?|from|को|अनुसार|बमोजिम)?\s*(?:(?:20\d{{2}}|२०[०-९]{{2}})[/-])?(?:{dev_yr_full}|{dev_yr_short})\s*(?:directive|circular|report|supervision\s*report|सुपरीवेक्षण\s*प्रतिवेदन|निर्देशन|परिपत्र|प्रतिवेदन)?\b',
        ' ',
        cleaned,
        flags=re.IGNORECASE
    )
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned or query

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
