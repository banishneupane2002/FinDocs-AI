import sys
if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
import os
from groq import Groq
from ask import expand_query_crosslingual

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.strip().split("=", 1)[1].strip()

client = Groq(api_key=GROQ_API_KEY)

q = "मलाई जुलाई २०२५ को विकास बैंकहरूको एकीकृत वित्तीय स्थितिको विवरण देखाउनुहोस्।"
terms = expand_query_crosslingual(q, client)
print("Query:", q)
print("Cross-lingual translation terms:", terms)
