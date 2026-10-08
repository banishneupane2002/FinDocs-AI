import os
import sys
import re
import unicodedata
import lancedb
from sentence_transformers import SentenceTransformer
from groq import Groq

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.strip().split("=", 1)[1].strip()

client = Groq(api_key=GROQ_API_KEY)
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

PREETI_CLEAN_REPLACEMENTS = [
    ('इखभचलष्नजत धबबिलअभ', 'Overnight Balance'),
    ('इखभचलष्नजत', 'Overnight'),
    ('धबबिलअभ', 'Balance'),
    ('ँयचअभ क्भततभिफभलत', 'Force Settlement'),
    ('ँयचअभ', 'Force'),
    ('क्भततभिफभलत', 'Settlement'),
    ('क्भततिभफभलत', 'Settlement'),
    ('क्थकतभफ ब्गमष्त', 'System Audit'),
    ('क्थकतभफ', 'System'),
    ('ब्गमष्त', 'Audit'),
    ('ब्गमषत', 'Audit'),
    ('ऋऋत्ख् ऋबफभचब', 'CCTV Camera'),
    ('ऋऋत्ख्', 'CCTV'),
    ('ऋबफभचब', 'Camera'),
    ('ःभफयचथ धबअपगउ', 'Memory Backup'),
    ('ःभफयचथ', 'Memory'),
    ('धबअपगउ', 'Backup'),
    ('द्यबअपगउ', 'Backup'),
    ('क्ष्धँत्', 'IBFT'),
    ('क्ष्द्यँत्', 'IBFT'),
    ('नयब्ःी क्यातधबचभ', 'goAML Software'),
    ('नयब्ःी', 'goAML'),
    ('क्यातधबचभ', 'Software'),
    ('त्जचभकजयमि त्चबलकबअतष्यल च्भउयचतष्लन( त्त्च्०', 'Threshold Transaction Reporting (TTR)'),
    ('त्जचभकजयमि त्चबलकबअतष्यल च्भउयचतष्लन', 'Threshold Transaction Reporting'),
    ('त्जचभकजयमि', 'Threshold'),
    ('त्त्च्', 'TTR'),
    ('क्त्च्', 'STR'),
    ('क्ब्च्', 'SAR'),
    ('ग्क्क्म्', 'USSD'),
    ('प्थ्ऋ', 'KYC'),
    ('ब्त्ः', 'ATM'),
    ('एइक्', 'POS'),
    ('एइत्', 'POT'),
    ('क्ष्ककगभच', 'Issuer'),
    ('ष्ककगभच', 'Issuer'),
    ('ब्अत्रगष्चभच', 'Acquirer'),
    ('९त्ंघ०', '(T+3)'),
    ('९त्ंज्ञ०', '(T+1)'),
    ('९त्ंघण्०', '(T+30)'),
    ('त्ंघ', 'T+3'),
    ('त्ंज्ञ', 'T+1'),
    ('त्ंघण्', 'T+30'),
    ('९ब्ःी०', '(AML)'),
    ('९ऋँत्०', '(CFT)'),
    ('ब्ःीरऋँत्', 'AML/CFT'),
]

def decode_preeti_text(text):
    for garbled, clean in PREETI_CLEAN_REPLACEMENTS:
        text = text.replace(garbled, clean)
    return text

def test_q7_and_q14():
    # 1. Test Q7
    q7 = "In the FY 2024/25 stress testing results, how many Development Banks fail to meet the minimum Capital Adequacy Ratio under Credit Shock C1 (15% performing loans deteriorating into substandard)?"
    
    # Query with specific keywords for C1 DBs
    res7 = table.search("Credit Shock C1 15 percent performing loans Substandard DBs").where("source = 'Annual_Report_2025.pdf'").limit(3).to_pandas()
    print("Q7 target search in Annual_Report_2025.pdf:")
    for _, r in res7.iterrows():
        print(f"  Page {r['page']}: {r['text'][:100].replace('\n', ' ')}")

    p33_records = table.search().where("source = 'Annual_Report_2025.pdf' AND page = 33").to_pandas()
    p33_text = "\n".join(p33_records['text'].tolist())

    prompt7 = f"""Extract the exact stress testing result for Credit Shock C1 for Development Banks:
Context:
{p33_text}

Question: {q7}"""

    res = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt7}],
        temperature=0.1,
        max_tokens=400
    )
    print("\nQ7 LLM Answer:\n", res.choices[0].message.content)

    # 2. Test Q14
    q14 = "Under what conditions must a Threshold Transaction Report (TTR) be submitted to the FIU, and what is the reporting deadline and required platform?"
    
    res14 = table.search("सीमा कारोबार प्रतिवेदन १० लाख १५ दिनभित्र goAML").limit(3).to_pandas()
    print("\nQ14 target search:")
    for _, r in res14.iterrows():
        print(f"  {r['source']} Page {r['page']}: {r['text'][:100].replace('\n', ' ')}")

    p67_records = table.search().where("source = 'directive_3.pdf' AND page = 67").to_pandas()
    p67_text = decode_preeti_text("\n".join(p67_records['text'].tolist()))

    prompt14 = f"""Extract the exact regulatory clause and conditions for Threshold Transaction Report (TTR):
Context:
{p67_text}

Question: {q14}"""

    res2 = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt14}],
        temperature=0.1,
        max_tokens=500
    )
    print("\nQ14 LLM Answer:\n", res2.choices[0].message.content)

if __name__ == "__main__":
    test_q7_and_q14()

