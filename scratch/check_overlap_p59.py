import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import app

q = "Tell us about the self-declaration system."
kw = app.extract_meaningful_keywords(q)
trans = app.expand_query_crosslingual(q, app.groq_client)
kw_trans = app.extract_meaningful_keywords(trans)
print("Query Keywords:", kw)
print("Translated Keywords:", kw_trans)

# Check BM25 score of directive_2082 page 59
df = app.table.to_pandas()
target = df[(df['source'] == 'directive_2082.pdf') & (df['page'] == 59)]
print("\nTarget chunk in DB:")
for idx, r in target.iterrows():
    print("Page 59 text:", r['text'][:200])
    # check word matches
    words = app.extract_meaningful_keywords(r['text'])
    overlap = (kw | kw_trans).intersection(words)
    print("Overlap with query keywords:", overlap)

