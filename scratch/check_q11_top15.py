import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scratch.test_clean_fixes import clean_hybrid_search, table, model

q11 = "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?"
t11 = "मार्जिन कर्जा, शेयर धितो कर्जा, ७० प्रतिशत, १८० दिन"

results = clean_hybrid_search(q11, table, model, translated_terms=t11, top_k=15)
for idx, r in enumerate(results, 1):
    p23 = " *** TARGET PAGE 23 ***" if r['page'] == 23 and '2082' in r['source'] else ""
    print(f"  {idx}: {r['source']} P{r['page']}{p23}")

