import os, sys, re, pypdf
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

PREETI_NUM_MAP = {'!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0'}
NEP_TO_ARABIC = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}

def detect_document_year(filename: str, sample_text: str = "") -> int:
    # 1. Filename match
    fn_m = re.search(r'(20[5-9][0-9]|20[0-4][0-9])', filename)
    if fn_m:
        return int(fn_m.group(1))

    # 2. Text check: Preeti encoded years e.g. @)&( or @)*@
    # Preeti: @ is 2, ) is 0, & is 7, * is 8
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

    # 3. Devanagari Unicode
    dev_m = re.search(r'२०([७८][०-९])', sample_text)
    if dev_m:
        decade_unit = "".join(NEP_TO_ARABIC.get(c, c) for c in dev_m.group(1))
        return int(f"20{decade_unit}")

    # 4. Standard ASCII
    ascii_m = re.search(r'\b(20[78][0-9]|20[12][0-9])\b', sample_text)
    if ascii_m:
        return int(ascii_m.group(1))

    return 0

WATCH_FOLDER = "File_System"
for f in os.listdir(WATCH_FOLDER):
    if not f.endswith(".pdf"): continue
    path = os.path.join(WATCH_FOLDER, f)
    reader = pypdf.PdfReader(path)
    sample_text = ""
    for p in reader.pages[:4]:
        sample_text += " " + (p.extract_text() or "")
    
    # Test WITHOUT filename (simulate filename having NO year e.g. 'unnamed.pdf')
    detected_without_filename = detect_document_year("unnamed.pdf", sample_text)
    detected_with_filename = detect_document_year(f, sample_text)
    print(f"File: {f:<25} -> From Text: {detected_without_filename} | Full: {detected_with_filename}")

