import re, os

def extract_cited_sources(response_text: str, retrieved_candidates: list, full_page_map: dict = None, live_table = None, target_years: set = None, target_doc = None) -> list:
    cited = []
    seen = set()
    full_page_map = full_page_map or {}
    found_matches = []
    matched_spans = []

    # 1. Broad Proximity Search for any known disk document name + Page number in the response
    known_docs = [f for f in os.listdir("File_System") if f.lower().endswith(('.pdf', '.docx', '.txt'))] if os.path.exists("File_System") else []
    # Sort known docs by length descending so longer filenames (e.g. Unified_directive_2082.pdf) are evaluated before shorter sub-names (directive_2082.pdf)
    known_docs.sort(key=len, reverse=True)

    for fname in known_docs:
        base_name = os.path.splitext(fname)[0]
        # Strict boundary: must NOT be preceded or succeeded by letters, numbers, or underscores
        # Prevents 'directive_2082.pdf' from matching inside 'Unified_directive_2082.pdf'
        pat = rf'(?<![a-zA-Z0-9_])(?:{re.escape(fname)}|{re.escape(base_name)})(?![a-zA-Z0-9_])'
        for m in re.finditer(pat, response_text, re.IGNORECASE):
            doc_start = m.start()
            doc_end = m.end()

            # Prevent shorter filename from matching inside an already matched longer filename span
            if any(s <= doc_start and doc_end <= e for s, e in matched_spans):
                continue

            # Look in a window after the doc name (up to 200 chars) for page indicator
            window_after = response_text[doc_end:min(len(response_text), doc_end + 200)]
            pg_match = re.search(r'(?:page|पृष्ठ|p\.?)\s*[:\-–—\s\*\_]*([०-९0-9]+)', window_after, re.IGNORECASE)
            if pg_match:
                nep_map = {'०':'0','१':'1','२':'2','३':'3','४':'4','५':'5','६':'6','७':'7','८':'8','९':'9'}
                pg_str = "".join(nep_map.get(c, c) for c in pg_match.group(1))
                page_num = int(pg_str)
                found_matches.append((doc_start, fname, page_num))
                matched_spans.append((doc_start, doc_end))
            else:
                # Also check window before (e.g. "Page 22 of directive_2082.pdf")
                window_before = response_text[max(0, doc_start - 100):doc_start]
                pg_match_before = re.search(r'(?:page|पृष्ठ|p\.?)\s*[:\-–—\s\*\_]*([०-९0-9]+)', window_before, re.IGNORECASE)
                if pg_match_before:
                    nep_map = {'०':'0','१':'1','२':'2','३':'3','४':'4','५':'5','६':'6','७':'7','८':'8','९':'9'}
                    pg_str = "".join(nep_map.get(c, c) for c in pg_match_before.group(1))
                    page_num = int(pg_str)
                    found_matches.append((doc_start, fname, page_num))
                    matched_spans.append((doc_start, doc_end))

    # 2. Standard Regex Patterns for inline citation blocks with strict word boundaries
    regex_patterns = [
        r'(?<![a-zA-Z0-9_])([a-zA-Z0-9_\-\.]+\.(?:pdf|docx|txt))(?:\s*[\:\|\-\–\—\(\)\[\]\*\_]?\s*|\s+(?:clause|section|दफा|खण्ड)\s*[^\n\r]{0,25}?\s*|\s*\n\s*\-?\s*\*\*?)(?:page|पृष्ठ|p\.?)\s*[:\-]?\s*([०-९0-9]+)',
        r'(?:page|पृष्ठ|p\.?)\s*[:\-]?\s*([०-९0-9]+)(?:\s*[\:\|\-\–\—\(\)\[\]\*\_]?\s*|\s*\n\s*\-?\s*\*\*?)(?<![a-zA-Z0-9_])(([a-zA-Z0-9_\-\.]+\.(?:pdf|docx|txt)))',
        r'\[\s*(?:कागजात|doc|document)?\s*[:\-]?\s*([a-zA-Z0-9_\-\.]+\.(?:pdf|docx|txt))\s*\|\s*(?:पृष्ठ|page)\s*[:\-]?\s*([०-९0-9]+)\s*\]',
        r'(?<![a-zA-Z0-9_])([a-zA-Z0-9_\-]+(?:directive|report)[a-zA-Z0-9_\-]*)(?:\s*[\:\|\-\–\—\(\)\[\]\*\_]?\s*|\s*\n\s*\-?\s*\*\*?)(?:page|पृष्ठ|p\.?)\s*[:\-]?\s*([०-९0-9]+)'
    ]

    nep_map = {'०':'0','१':'1','२':'2','३':'3','४':'4','५':'5','६':'6','७':'7','८':'8','९':'9'}

    for pat in regex_patterns:
        for m in re.finditer(pat, response_text, re.IGNORECASE):
            g1, g2 = m.group(1), m.group(2)
            if re.match(r'^[०-९0-9]+$', g1):
                doc_name = g2
                page_str = "".join(nep_map.get(c, c) for c in g1)
                page_num = int(page_str)
            else:
                doc_name = g1
                page_str = "".join(nep_map.get(c, c) for c in g2)
                page_num = int(page_str)

            if not doc_name.lower().endswith(('.pdf', '.docx', '.txt')):
                if os.path.exists(os.path.join("File_System", f"{doc_name}.pdf")):
                    doc_name = f"{doc_name}.pdf"

            if os.path.exists(os.path.join("File_System", doc_name)):
                if not any(s <= m.start() and m.end() <= e for s, e in matched_spans):
                    found_matches.append((m.start(), doc_name, page_num))
                    matched_spans.append((m.start(), m.end()))

    # Sort matches by character position in the AI's response text
    found_matches.sort(key=lambda x: x[0])

    for pos, doc_name, page_num in found_matches:
        key = (doc_name, page_num)
        if key not in seen:
            seen.add(key)
            snippet = full_page_map.get(key, "")
            cited.append({
                'source': doc_name,
                'page': page_num,
                'text': snippet,
                'pos': pos
            })

    # 3. Match against retrieved candidate chunks ONLY if no citations found yet, with strict word boundary
    if not cited:
        for item in retrieved_candidates:
            src = item['source']
            pg = str(item['page'])
            base_src = src.replace('.pdf', '').replace('.docx', '').replace('.txt', '')
            # Strict word boundary: no partial substring match of Unified_directive as directive
            exact_doc_pat = rf'(?<![a-zA-Z0-9_]){re.escape(base_src)}(?![a-zA-Z0-9_])'
            if re.search(exact_doc_pat, response_text, re.IGNORECASE):
                pg_pattern = rf'(?:page|पृष्ठ|p\.?)\s*[:\-–—\s\*\_]*{pg}\b'
                m_pg = re.search(pg_pattern, response_text, re.IGNORECASE)
                if m_pg:
                    key = (src, item['page'])
                    if key not in seen:
                        seen.add(key)
                        pos = m_pg.start()
                        cited.append({
                            'source': src,
                            'page': item['page'],
                            'text': full_page_map.get(key, item.get('text', '')),
                            'pos': pos
                        })

    # 4. Fallback to top-1 primary search match if no explicit citation was found
    if not cited and retrieved_candidates:
        top_item = retrieved_candidates[0]
        key = (top_item['source'], top_item['page'])
        cited.append({
            'source': top_item['source'],
            'page': top_item['page'],
            'text': full_page_map.get(key, top_item.get('text', '')),
            'pos': 0
        })

    return cited

# TEST SUITE
print("--- TEST 1: User's exact prompt from screenshot ---")
resp1 = """Loan classification: When a borrower is placed on the Credit Information Bureau (CIC) blacklist, the loan must be classified in the "खराब (Loss)" category.

Provision required: A 100% provision on the total outstanding amount (principal + accrued interest) is mandatory.

Regulatory source
- Unified_directive_2082.pdf, Directive 2 - Loan Classification & Provisioning, page 14 - the provision matrix lists "खराब (100%)" as the minimum loss-provision for loans in the "Loss" (खराब) class.

Thus, a CIC-blacklisted borrower's loan is treated as a "Loss" loan with a full (100%) provision."""

cand1 = [
    {'source': 'Unified_directive_2082.pdf', 'page': 14},
    {'source': 'directive_2082.pdf', 'page': 14}
]
c1 = extract_cited_sources(resp1, cand1)
print(f"Test 1 Cited Count: {len(c1)} (Expected: 1)")
for c in c1:
    print(f"  -> {c['source']} p.{c['page']}")
assert len(c1) == 1 and c1[0]['source'] == 'Unified_directive_2082.pdf' and c1[0]['page'] == 14

print("\n--- TEST 2: Payment directive query alone (mobile banking) ---")
resp2 = """Mobile Banking Transaction Limit: NPR 300,000 per day.
Citation: directive_2082.pdf, page 21 (Directive 2, clause on mobile limits)."""
cand2 = [
    {'source': 'directive_2082.pdf', 'page': 21},
    {'source': 'Unified_directive_2082.pdf', 'page': 21}
]
c2 = extract_cited_sources(resp2, cand2)
print(f"Test 2 Cited Count: {len(c2)} (Expected: 1)")
for c in c2:
    print(f"  -> {c['source']} p.{c['page']}")
assert len(c2) == 1 and c2[0]['source'] == 'directive_2082.pdf' and c2[0]['page'] == 21

print("\n--- TEST 3: Genuine multi-document citation ---")
resp3 = """Here is the comparison:
1. Unified_directive_2082.pdf | page 14: loan classification matrix.
2. directive_2082.pdf | page 20: cash withdrawal limits."""
cand3 = [
    {'source': 'Unified_directive_2082.pdf', 'page': 14},
    {'source': 'directive_2082.pdf', 'page': 20}
]
c3 = extract_cited_sources(resp3, cand3)
print(f"Test 3 Cited Count: {len(c3)} (Expected: 2)")
for c in c3:
    print(f"  -> {c['source']} p.{c['page']}")
assert len(c3) == 2

print("\n--- TEST 4: Devanagari numerals citation ---")
resp4 = """स्रोत: [कागजात: Unified_directive_2082.pdf | पृष्ठ: १४]"""
cand4 = [{'source': 'Unified_directive_2082.pdf', 'page': 14}]
c4 = extract_cited_sources(resp4, cand4)
print(f"Test 4 Cited Count: {len(c4)} (Expected: 1)")
for c in c4:
    print(f"  -> {c['source']} p.{c['page']}")
assert len(c4) == 1 and c4[0]['page'] == 14

print("\nALL 4 CITATION EXTRACTION TESTS PASSED PERFECTLY!")
