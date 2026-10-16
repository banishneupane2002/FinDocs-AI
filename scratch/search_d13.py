import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import lancedb

db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')

df = tbl.search().where("source = 'Unified_directive_2082.pdf' AND page >= 115 AND page <= 125").select(['page', 'text']).to_pandas()
for _, r in df.iterrows():
    txt = r['text']
    for line in txt.split('\n'):
        if any(term in line for term in ['अनिवार्य', 'नगद', 'मौज्दात', 'प्रतिशत', 'SLR', 'CRR', 'वैधानिक']):
            print(f"P{r['page']}: {line.strip()[:100]}")

