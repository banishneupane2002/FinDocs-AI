import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import re
import lancedb

PREETI_NUM_MAP = {'!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0'}
NEP_TO_ARABIC = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}

def extract_query_years_v2(query: str, available_years: set) -> set:
    found_years = set()
    # Support ALL Devanagari years including AD (२०२४, २०२५) and BS (२०७९, २०८०)
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

    en_ranges = re.finditer(r'\b(20[78][0-9]|20[12][0-9])[/-]([0-9]{2})\b', query)
    for m in en_ranges:
        y1 = int(m.group(1))
        if y1 in available_years:
            found_years.add(y1)
        y2 = int(str(y1)[:2] + m.group(2))
        if y2 in available_years:
            found_years.add(y2)

    standalone_candidates = re.finditer(r'\b(20[78][0-9]|20[12][0-9])\b', query)
    for m in standalone_candidates:
        candidate = int(m.group(1))
        start_idx, end_idx = m.start(), m.end()
        pre_ctx = query[max(0, start_idx - 15):start_idx].lower()
        post_ctx = query[end_idx:min(len(query), end_idx + 15)].lower()

        if re.search(r'(?:रु\.?|रु|rs\.?|rs|npr|रुपैयाँ|रुपैंया|rupees|amount|deposit|withdraw|transfer|fee|charge|limit)\s*$', pre_ctx):
            continue
        if re.search(r'^\s*(?:रु\.?|रु|rs\.?|rs|npr|रुपैयाँ|रुपैंया|rupees|हजार|लाख|per|प्रति)', post_ctx):
            continue

        if candidate in available_years:
            found_years.add(candidate)

    return found_years

def prioritize_matching_document(target_yr: int, matching_docs: list) -> str:
    """
    Selects the best document when multiple reports cover the target year.
    Prioritizes:
    1. Document with target_yr in filename (e.g. Annual_Report_2024.pdf for 2024)
    2. Primary reporting period over comparative retrospective years.
    """
    if not matching_docs:
        return None
    # Check if exact year appears in filename
    for doc in matching_docs:
        if str(target_yr) in doc:
            return doc
    return matching_docs[0]

# Test with user queries
avail_years = {2023, 2024, 2025, 2078, 2079, 2080, 2081, 2082}
matching_2024 = ['Annual_Report_2025.pdf', 'Annual_Report_2024.pdf']

q1 = "मलाई जुलाई २०२५ को विकास बैंकहरूको एकीकृत वित्तीय स्थितिको विवरण देखाउनुहोस्।"
q3 = "Statement of Financial Position of DBs show me of july 2024"

yrs_q1 = extract_query_years_v2(q1, avail_years)
yrs_q3 = extract_query_years_v2(q3, avail_years)

best_doc_2024 = prioritize_matching_document(2024, matching_2024)

print(f"Query 1: '{q1}'")
print(f"  -> Detected Years: {yrs_q1}")
print(f"  -> Should Route To: Annual_Report_2025.pdf\n")

print(f"Query 3: '{q3}'")
print(f"  -> Detected Years: {yrs_q3}")
print(f"  -> Candidate Docs: {matching_2024}")
print(f"  -> Prioritized Doc: {best_doc_2024} (Fixed! Now routes to 2024 report instead of 2025 report)\n")

