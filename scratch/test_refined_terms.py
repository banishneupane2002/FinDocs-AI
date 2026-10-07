import sys
sys.path.insert(0, '.')
import ask

sys.stdout.reconfigure(encoding='utf-8')

q = "What agreement must a bank make with a customer for branchless banking?"
terms = "शाखारहित बैंकिङ्ग, सम्झौता, ग्राहक"
results = ask.hybrid_search(q, ask.table, ask.embedding_model, translated_terms=terms, top_k=4)
for i, r in enumerate(results, 1):
    src = r['source']
    page = r['page']
    score = r['score']
    text = r['text'][:110].replace('\n', ' ')
    print(f"{i}. [{src} - Page {page}] Score: {score:.3f} | {text}")

