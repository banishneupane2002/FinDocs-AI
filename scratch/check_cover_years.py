import os, sys, re, pypdf
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

WATCH_FOLDER = "File_System"
for f in os.listdir(WATCH_FOLDER):
    if not f.endswith(".pdf"): continue
    path = os.path.join(WATCH_FOLDER, f)
    reader = pypdf.PdfReader(path)
    sample_text = ""
    for p in reader.pages[:2]:
        t = p.extract_text() or ""
        sample_text += " " + t
    
    # Look for Bikram Sambat years 2070-2090 or Gregorian years 2010-2030
    bs_years = re.findall(r'(?:२०[७८९][०-९]|20[789][0-9])', sample_text)
    ad_years = re.findall(r'(?:20[123][0-9])', sample_text)
    
    print(f"\n--- File: {f} ---")
    print(f"Detected BS years in first 2 pages: {set(bs_years[:5])}")
    print(f"Detected AD years in first 2 pages: {set(ad_years[:5])}")

