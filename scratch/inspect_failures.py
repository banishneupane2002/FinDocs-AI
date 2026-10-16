import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')

print("--- 1. CRR / SLR in Unified_directive_2082.pdf ---")
df_crr = tbl.search().where("source = 'Unified_directive_2082.pdf'").select(['page', 'text']).to_pandas()
for _, r in df_crr.iterrows():
    txt = r['text']
    if 'अनिवार्य नगद' in txt or 'नगद मौज्दात' in txt or 'CRR' in txt or 'Cash Reserve' in txt:
        print(f"Page {r['page']}: {txt[:120]}...")

print("\n--- 2. Margin Lending / LTV in Unified_directive_2082.pdf ---")
for _, r in df_crr.iterrows():
    txt = r['text']
    if ('मार्जिन' in txt or 'Margin Lending' in txt) and ('७०' in txt or '70' in txt):
        print(f"Page {r['page']}: {txt[:120]}...")

print("\n--- 3. Residential Property CAR Risk Weight in Unified_directive_2082.pdf ---")
for _, r in df_crr.iterrows():
    txt = r['text']
    if ('residential' in txt.lower() or 'आवासीय' in txt) and ('60%' in txt or '६०' in txt or 'risk' in txt.lower()):
        print(f"Page {r['page']}: {txt[:120]}...")

