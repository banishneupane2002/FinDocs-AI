import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

import lancedb
from core.preeti import decode_preeti_text

db = lancedb.connect('lancedb_data')
t = db.open_table('bank_documents')

for pg in range(104, 114):
    df = t.search().where(f"source = 'Unified_directive_2082.pdf' AND page = {pg}").to_pandas()
    if len(df) > 0:
        txt = decode_preeti_text("\n".join(df['text'].tolist()))
        m1 = '१० लाख' in txt or 'दश लाख' in txt or '१०,००,०००' in txt
        m2 = '९० दिन' in txt or 'नब्बे दिन' in txt
        m3 = 'कालोसूची' in txt
        if m1 or m2 or m3:
            print(f"Page {pg}: 10 Lakh={m1}, 90 Days={m2}, Blacklist={m3}")
            if m1 and m2:
                print(f"--> Found both on Page {pg}!")
                # Print lines containing both
                for line in txt.split('\n'):
                    if 'लाख' in line or 'दिन' in line:
                        print("   ", line.strip())

