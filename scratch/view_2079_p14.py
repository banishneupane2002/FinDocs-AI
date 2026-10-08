import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import app
records = app.table.search().where("source = 'directive_2079.pdf' AND page = 14").to_pandas()
raw_text = "\n".join(records['text'].tolist())
print("=== RAW TEXT OF DIRECTIVE 2079 PAGE 14 ===")
print(raw_text)
print("\n=== DECODED PREETI TEXT ===")
print(app.decode_preeti_text(raw_text))

