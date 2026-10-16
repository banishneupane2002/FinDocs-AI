import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from dotenv import load_dotenv
load_dotenv()
from core.search import MODELS_TO_TRY

client = Groq(api_key=os.getenv('GROQ_API_KEY'))
q = "When calculating the Capital Adequacy Ratio (CAR), what is the risk weight assigned to loans secured by residential properties?"

is_nepali = sum(1 for c in q if '\u0900' <= c <= '\u097f') >= max(len(q.replace(' ', '')), 1) * 0.3
print("is_nepali:", is_nepali)

for m in MODELS_TO_TRY:
    try:
        res = client.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": "Translate banking concepts into official NRB terms."},
                {"role": "user", "content": q}
            ],
            max_tokens=450 if "gpt-oss" in m else 100
        )
        print(f"Model {m} succeeded: {res.choices[0].message.content[:100]}")
        break
    except Exception as e:
        print(f"Model {m} failed: {e}")

