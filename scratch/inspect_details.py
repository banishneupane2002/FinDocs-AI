import os, sys
sys.path.insert(0, os.path.abspath("."))
import inspect_context

print("--- Q2: Annual_Report_2024.pdf Page 24 ---")
rec = inspect_context.table.search().where("source = 'Annual_Report_2024.pdf' AND page = 24").to_pandas()
t = "\n".join(rec['text'].tolist())
print(t[:600])

print("\n--- Q6: Annual_Report_2025.pdf Page 45 ---")
rec = inspect_context.table.search().where("source = 'Annual_Report_2025.pdf' AND page = 45").to_pandas()
t = "\n".join(rec['text'].tolist())
for line in t.split("\n"):
    if "loan" in line.lower() or "director" in line.lower() or "5.2" in line:
        print("  ", line)

print("\n--- Q13: directive_3.pdf Page 15 ---")
rec = inspect_context.table.search().where("source = 'directive_3.pdf' AND page = 15").to_pandas()
t = inspect_context.decode_preeti_text("\n".join(rec['text'].tolist()))
for line in t.split("\n"):
    if "audit" in line.lower() or "वर्ष" in line:
        print("  ", line)

print("\n--- Q7: Annual_Report_2025.pdf Page 33 & Page 79 ---")
for pg in [33, 34, 79, 81]:
    rec = inspect_context.table.search().where(f"source = 'Annual_Report_2025.pdf' AND page = {pg}").to_pandas()
    txt = "\n".join(rec['text'].tolist())
    print(f"=== Page {pg} ===")
    for line in txt.split("\n"):
        if any(w in line.lower() for w in ['stress', 'c1', 'shock', '3.24', 'substandard', 'car']):
            print("  ", line[:150])

