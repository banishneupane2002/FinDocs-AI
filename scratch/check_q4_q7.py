import sys, os
sys.path.insert(0, os.path.abspath("."))
import ask

print("--- Checking Q4 in Annual_Report_2024.pdf p.16 and Annual_Report_2025.pdf p.17 & 53 ---")
for src, pg in [("Annual_Report_2024.pdf", 16), ("Annual_Report_2025.pdf", 17), ("Annual_Report_2025.pdf", 53)]:
    rec = ask.table.search().where(f"source = '{src}' AND page = {pg}").to_pandas()
    txt = "\n".join(rec['text'].tolist())
    print(f"\n[{src} p.{pg}]:")
    for line in txt.split("\n"):
        if any(w in line.lower() for w in ["capital adequacy framework", "basel", "national level", "regional level"]):
            print("  ", line[:150])

print("\n--- Checking Q7: Credit Shock C1 in Annual_Report_2025.pdf ---")
rec_all = ask.table.search("Credit Shock C1 15% performing loans").where("source = 'Annual_Report_2025.pdf'").limit(10).to_pandas()
for _, r in rec_all.iterrows():
    print(f"Page {r['page']}: {r['text'][:200]}...\n")
