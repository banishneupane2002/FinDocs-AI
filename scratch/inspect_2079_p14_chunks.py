import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app
df = app.table.to_pandas()
p14 = df[(df['source'] == 'directive_2079.pdf') & (df['page'] == 14)]
print("Total chunks on page 14:", len(p14))
for idx, r in p14.iterrows():
    print("Chunk text:\n", r['text'][:300])
    print("="*50)
