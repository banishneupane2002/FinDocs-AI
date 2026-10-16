import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import lancedb

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')

print("--- Q17: Where is 10 Lakh blacklisting threshold in Directive 12? ---")
df12 = table.search().where("source = 'Unified_directive_2082.pdf' AND page >= 100 AND page <= 115").select(['page', 'text']).to_pandas()
for _, r in df12.iterrows():
    if '१० लाख' in r['text'] or '10 लाख' in r['text'] or '१०,००,०००' in r['text']:
        print(f"Page {r['page']}: {r['text'][:150]}...")

print("\n--- Q3: Directive 2 classification for CIC blacklisted borrower ---")
df2 = table.search().where("source = 'Unified_directive_2082.pdf' AND page >= 7 AND page <= 16").select(['page', 'text']).to_pandas()
for _, r in df2.iterrows():
    if 'कालोसूची' in r['text']:
        print(f"Page {r['page']}: {r['text'][:150]}...")

print("\n--- Q5: CRR 4% on Page 118 ---")
df13 = table.search().where("source = 'Unified_directive_2082.pdf' AND page >= 118 AND page <= 122").select(['page', 'text']).to_pandas()
for _, r in df13.iterrows():
    if '४' in r['text'] and 'अनिवार्य' in r['text']:
        print(f"Page {r['page']}: {r['text'][:150]}...")

