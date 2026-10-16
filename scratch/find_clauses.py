import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')

print("=== 1. CRR on Page 118-120 of Unified_directive_2082.pdf ===")
df_p118 = tbl.search().where("source = 'Unified_directive_2082.pdf' AND page >= 118 AND page <= 120").select(['page', 'text']).to_pandas()
for _, r in df_p118.iterrows():
    print(f"\n--- Page {r['page']} ---")
    print(r['text'])

print("\n=== 2. Margin Lending in ALL docs ===")
df_all = tbl.search().select(['source', 'page', 'text']).to_pandas()
for _, r in df_all.iterrows():
    txt = r['text']
    if ('margin' in txt.lower() or 'मार्जिन' in txt or 'मार्जिन प्रकृतिको' in txt) and ('70%' in txt or '७०%' in txt or '७० प्रतिशत' in txt or '70 percent' in txt.lower() or '180' in txt or '१८०' in txt):
        print(f"[{r['source']} Page {r['page']}]: {txt[:200]}...\n")

print("\n=== 3. Residential Property Risk Weight 60% in Unified_directive_2082.pdf ===")
df_car = tbl.search().where("source = 'Unified_directive_2082.pdf' AND page >= 220 AND page <= 230").select(['page', 'text']).to_pandas()
for _, r in df_car.iterrows():
    txt = r['text']
    if 'residential' in txt.lower():
        print(f"--- Page {r['page']} ---")
        for line in txt.split('\n'):
            if 'residential' in line.lower() or '60%' in line or 'risk' in line.lower():
                print(f"  {line}")

