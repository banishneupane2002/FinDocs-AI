import sys
import os
sys.path.insert(0, os.path.abspath('.'))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

print("FTS with 'भुक्तानी':")
df1 = t.search("भुक्तानी").where("source = 'directive_2080.pdf' AND page = 18").to_pandas()
print(f"  Matches on page 18: {len(df1)}")

print("FTS with 'भुत्तफानी':")
df2 = t.search("भुत्तफानी").where("source = 'directive_2080.pdf' AND page = 18").to_pandas()
print(f"  Matches on page 18: {len(df2)}")

print("FTS with 'भिफक्ने':")
df3 = t.search("भिफक्ने").where("source = 'directive_2080.pdf' AND page = 18").to_pandas()
print(f"  Matches on page 18: {len(df3)}")

