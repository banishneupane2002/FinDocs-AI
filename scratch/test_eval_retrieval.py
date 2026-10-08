import os
import sys
import lancedb
from sentence_transformers import SentenceTransformer
from groq import Groq

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))

# Load GROQ API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.strip().split("=", 1)[1].strip()

client = Groq(api_key=GROQ_API_KEY)
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Import functions from ask
from ask import extract_meaningful_keywords, hybrid_search, expand_query_crosslingual

questions = [
    # Category 1
    ("Q1", "When was Nepal Bank Limited (NBL) established as the first commercial bank, and in which year was Nepal Rastra Bank (NRB) established?"),
    ("Q2", "What were the top three asset components and their respective shares for Development Banks (DBs) as of Mid-July 2024?"),
    ("Q3", "What was the Non-Performing Loan (NPL) ratio of Development Banks (B-class) versus Finance Companies (C-class) as of Mid-July 2024 compared to Mid-July 2023?"),
    ("Q4", "Under NRB regulations, which Capital Adequacy Framework applies to national-level Development Banks versus regional-level Development Banks and Finance Companies?"),
    ("Q5", "Did Finance Companies post a consolidated net profit or loss in FY 2024/25, and how did it compare to FY 2023/24?"),
    ("Q6", "According to the onsite supervision observations in FY 2024/25, which specific loan types are board members of financial institutions permitted to obtain under the Unified Directives?"),
    ("Q7", "In the FY 2024/25 stress testing results, how many Development Banks fail to meet the minimum Capital Adequacy Ratio under Credit Shock C1 (15% performing loans deteriorating into substandard)?"),
    # Category 2
    ("Q8", "How long (in days) must banks and financial institutions retain the CCTV camera memory backup at ATM kiosks?"),
    ("Q9", "What is the required timeline for Force Settlement when an electronic transaction fails (account debited but cash not dispensed / transaction not completed) and both Issuer and Acquirer are different Nepali institutions?"),
    ("Q10", "What is the maximum overnight balance allowed in a natural person's digital wallet, and where must the excess balance be transferred?"),
    ("Q11", "Under the AML/CFT payment directives, what is the maximum annual transaction limit for merchants eligible for Simplified Customer Due Diligence (Simplified KYC)?"),
    ("Q12", "What is the maximum fee service providers can charge individual customers per transaction for Inter Bank Fund Transfer (IBFT) through Mobile App or Internet Banking?"),
    ("Q13", "When must a licensed non-bank Payment Service Provider conduct its first System Audit, and how often must it be conducted thereafter if the system is not replaced or upgraded?"),
    ("Q14", "Under what conditions must a Threshold Transaction Report (TTR) be submitted to the FIU, and what is the reporting deadline and required platform?"),
    ("Q15", "What is the daily ATM cash withdrawal limit on debit cards issued by banks and financial institutions in the 2081 directive versus the updated 2082 directive?")
]

print("Running baseline retrieval test...")
for q_id, q_text in questions:
    trans = expand_query_crosslingual(q_text, client)
    kw = extract_meaningful_keywords(q_text)
    res = hybrid_search(q_text, table, model, translated_terms=trans, top_k=3)
    top_sources = [f"{r['source']} p.{r['page']}" for r in res]
    print(f"{q_id}: trans='{trans}' -> top 3: {top_sources}")
