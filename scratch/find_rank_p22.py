import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
import ask

q = "एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?"
q_vec = ask.embedding_model.encode(q).tolist()

# Find rank and distance of page 22 in full vector search
res = ask.table.search(q_vec).limit(200).to_pandas()
for rank, (i, r) in enumerate(res.iterrows(), 1):
    if r['source'] == 'directive_1.pdf' and r['page'] == 22:
        print(f"Directive 1 P22 is at RANK {rank}: dist={r['_distance']:.3f} | {r['text'][:70].replace(chr(10), ' ')}")
    if r['source'] == 'directive_2.pdf' and r['page'] == 22:
        print(f"Directive 2 P22 is at RANK {rank}: dist={r['_distance']:.3f} | {r['text'][:70].replace(chr(10), ' ')}")

