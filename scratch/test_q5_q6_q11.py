import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from dotenv import load_dotenv
load_dotenv()
from core.search import expand_query_crosslingual

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

queries = {
    "Q5": "What is the minimum Statutory Liquidity Ratio (SLR) and Cash Reserve Ratio (CRR) required for a 'C' class finance company?",
    "Q6": "When calculating the Capital Adequacy Ratio (CAR), what is the risk weight assigned to loans secured by residential properties?",
    "Q11": "What is the maximum Loan to Value (LTV) ratio allowed for margin lending (share loans)?"
}

for qid, q in queries.items():
    print(f"\n--- {qid} ---")
    print(f"Query: {q}")
    trans = expand_query_crosslingual(q, client)
    print(f"Trans: {trans}")

