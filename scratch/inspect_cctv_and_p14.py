import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
import lancedb
from ask import decode_preeti_text

db = lancedb.connect('./lancedb_data')
tbl = db.open_table('bank_documents')

# 1. Inspect CCTV in directive_2082 and directive_2080
print("=== CCTV INSPECTION ===")
df_cctv = tbl.search("CCTV क्यामेरा ब्याकअप").limit(5).to_pandas()
for _, r in df_cctv.iterrows():
    decoded = decode_preeti_text(r['text'])
    if 'cctv' in decoded.lower() or 'क्यामेरा' in decoded or 'दिन' in decoded:
        print(f"Source: {r['source']} P{r['page']}")
        for line in decoded.split("\n"):
            if any(w in line.lower() for w in ['cctv', 'क्यामेरा', 'दिन', 'महिना', 'back']):
                print("  ", line.strip())
        print()

# 2. Inspect 2079 Page 14 System audit
print("=== 2079 PAGE 14 SYSTEM AUDIT ===")
p14 = tbl.search().where("source = 'directive_2079.pdf' AND page = 14").to_pandas()
for _, r in p14.iterrows():
    decoded = decode_preeti_text(r['text'])
    print(decoded[:500])
    print("-" * 40)
