import os, sys
sys.path.insert(0, os.path.abspath("."))
import ask

rec = ask.table.search().where("source = 'directive_1.pdf' AND page = 15").to_pandas()
txt = "\n".join(rec['text'].tolist())
print("directive_1.pdf Page 15:")
print(txt[:600])

