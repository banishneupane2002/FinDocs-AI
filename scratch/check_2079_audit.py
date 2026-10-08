import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb
db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')
df = table.to_pandas()
d2079 = df[df['source'] == 'directive_2079.pdf']
print('Total chunks in directive_2079.pdf:', len(d2079))

# Check for system audit or audit terms
terms = ['System Audit', 'Audit', 'ब्गमष्त', 'लेखापरीक्षण', 'प्रणाली परीक्षण']
for term in terms:
    m = d2079[d2079['text'].str.contains(term, case=False, na=False)]
    pages = sorted(m['page'].unique().tolist())
    print(f"Term '{term}': {len(m)} chunks on pages {pages}")

print("\n--- Snippets on matching pages ---")
m = d2079[d2079['text'].str.contains('System Audit|ब्गमष्त|प्रणाली परीक्षण', case=False, na=False)]
for idx, r in m.head(10).iterrows():
    print(f"Page {r['page']}: {r['text'][:180].strip()}")
    print("-" * 50)

