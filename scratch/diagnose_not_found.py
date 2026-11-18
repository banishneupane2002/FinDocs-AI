import sys, os
sys.path.insert(0, os.path.abspath('.'))
import fitz

print("--- Searching PDFs for compliance officer qualification ---")
doc = fitz.open("File_System/Unified_directive_2082.pdf")
print("Total pages in Unified_directive_2082.pdf:", len(doc))

comp_hits = []
for pno in range(len(doc)):
    text = doc[pno].get_text()
    if "कम्प्लायन्स" in text or "compliance" in text.lower():
        if "अधिकृत" in text or "officer" in text.lower() or "योग्यता" in text or "qualification" in text.lower():
            comp_hits.append(pno + 1)
print("Pages with compliance officer & qualification in Unified_directive_2082.pdf:", comp_hits)

for p in comp_hits[:5]:
    print(f"\n--- Snippet from page {p} ---")
    lines = doc[p - 1].get_text().split("\n")
    for l in lines:
        if any(w in l.lower() for w in ["कम्प्लायन्स", "compliance", "अधिकृत", "योग्यता"]):
            print("  ", l.strip())

print("\n--- Searching PDFs for Directors' Meeting Allowance (सञ्चालकको बैठक भत्ता) ---")
allowance_hits = []
for pno in range(len(doc)):
    text = doc[pno].get_text()
    if "बैठक भत्ता" in text or "meeting allowance" in text.lower() or ("भत्ता" in text and "सञ्चालक" in text):
        allowance_hits.append(pno + 1)
print("Pages with बैठक भत्ता in Unified_directive_2082.pdf:", allowance_hits)

for p in allowance_hits[:5]:
    print(f"\n--- Snippet from page {p} ---")
    lines = doc[p - 1].get_text().split("\n")
    for l in lines:
        if any(w in l.lower() for w in ["बैठक भत्ता", "भत्ता", "सञ्चालक"]):
            print("  ", l.strip())
