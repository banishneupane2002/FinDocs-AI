import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
import ask

q = "एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?"
terms = ask.expand_query_crosslingual(q, ask.client)
print("Terms:", terms)

q_vec = ask.embedding_model.encode(q).tolist()
res = ask.table.search(q_vec).limit(35).to_pandas()
print("\nTop 10 vector candidates from LanceDB:")
found = False
for i, r in res.head(15).iterrows():
    is_p22 = (r['source'] == 'directive_1.pdf' and r['page'] == 22)
    print(f" {i+1}. [{r['source']} P{r['page']}] dist={r['_distance']:.3f} | {r['text'][:60].replace(chr(10), ' ')}")
    if is_p22:
        found = True

print("Was directive_1.pdf P22 in top 15 vector candidates?", found)

