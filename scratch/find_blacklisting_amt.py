import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import lancedb

db = lancedb.connect(os.path.join(PROJECT_ROOT, 'lancedb_data'))
table = db.open_table('bank_documents')

print("--- Searching 'कालोसूची' and numeric threshold in ALL docs ---")
df = table.search().select(['source', 'page', 'text']).to_pandas()
for _, r in df.iterrows():
    txt = r['text']
    if 'कालोसूची' in txt and any(term in txt for term in ['१० लाख', '10 लाख', '५० लाख', '२५ लाख', '५ लाख']):
        print(f"[{r['source']} P{r['page']}]: {txt[:160]}...\n")

