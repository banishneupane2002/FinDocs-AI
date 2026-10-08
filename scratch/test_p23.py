import os, sys
sys.path.insert(0, os.path.abspath("."))
import inspect_context

rec = inspect_context.table.search().where("source = 'Annual_Report_2024.pdf' AND page = 23").to_pandas()
print("=== Page 23 ===")
txt = "\n".join(rec['text'].tolist())
print(txt[:1000])

