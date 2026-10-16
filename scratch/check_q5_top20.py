import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scratch.test_clean_fixes import clean_hybrid_search, table, model

q5 = "What is the minimum Statutory Liquidity Ratio (SLR) and Cash Reserve Ratio (CRR) required for a 'C' class finance company?"
t5 = "वैधानिक तरलता अनुपात, अनिवार्य नगद मौज्दात, १० प्रतिशत, ४ प्रतिशत"

results = clean_hybrid_search(q5, table, model, translated_terms=t5, top_k=20)
print("Q5 results top 20:")
for idx, r in enumerate(results, 1):
    target = " *** TARGET P118 ***" if r['page'] == 118 and '2082' in r['source'] else ""
    target2 = " *** TARGET P120 ***" if r['page'] == 120 and '2082' in r['source'] else ""
    print(f"  {idx}: {r['source']} P{r['page']}{target}{target2}")

