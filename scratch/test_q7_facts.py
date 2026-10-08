import os, sys
sys.path.insert(0, os.path.abspath("."))
import inspect_context

rec = inspect_context.table.search().where("source = 'Annual_Report_2025.pdf' AND page = 33").to_pandas()
txt = "\n".join(rec['text'].tolist())

print("Testing exact fact matches on Page 33:")
for f in ["Credit Shock (C1)", "15 percent of performing loans", "6 national", "4 provincial", "substandard"]:
    print(f"'{f}' in txt:", f.lower() in txt.lower())

for line in txt.split("\n"):
    if "credit shock" in line.lower() or "3.24" in line:
        print("MATCHED LINE:", repr(line))
