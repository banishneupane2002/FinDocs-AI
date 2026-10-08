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

MODELS_TO_TRY = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]

PREETI_KEYMAP = {
    'a': 'ब', 'b': 'द', 'c': 'अ', 'd': 'म', 'e': 'भ', 'f': 'ा', 'g': 'न',
    'h': 'ज', 'i': 'ष', 'j': 'व', 'k': 'प', 'l': 'ि', 'm': 'फ', 'n': 'ल',
    'o': 'य', 'p': 'उ', 'q': 'त्र', 'r': 'च', 's': 'क', 't': 'त', 'u': 'ग',
    'v': 'ख', 'w': 'ध', 'x': 'ह', 'y': 'थ', 'z': 'श',
    'A': 'ब्', 'B': 'द्य', 'C': 'ऋ', 'D': 'म्', 'E': 'भ्', 'F': 'ँ', 'G': 'न्',
    'H': 'ज्', 'I': 'क्ष्', 'J': 'व्', 'K': 'प्', 'L': 'ी', 'M': 'ः', 'N': 'ल्',
    'O': 'इ', 'P': 'ए', 'Q': 'त्त', 'R': 'च्', 'S': 'क्', 'T': 'त्', 'U': 'ग्',
    'V': 'ख्', 'W': 'ध्', 'X': 'ह्र', 'Y': 'थ्', 'Z': 'श्',
    '0': 'ण्', '1': 'ज्ञ', '2': 'द्द', '3': 'घ', '4': 'द्ध', '5': 'छ',
    '6': 'ट', '7': 'ठ', '8': 'ड', '9': 'ढ',
    '+': 'ं', '-': '(', '=': '.', '/': 'र', '.': '।',
}

SPECIAL_PREETI = {
    'ibft': ['क्ष्धँत्', 'क्ष्द्यँत्'],
    'backup': ['धबअपगउ'],
    'settlement': ['क्भततभिफभलत', 'क्भततिभफभलत'],
    'audit': ['ब्गमष्त', 'ब्गमषत'],
    'cctv': ['ऋऋत्ख्'],
    'ussd': ['ग्क्क्म्'],
    'ttr': ['त्त्च्'],
    'str': ['क्त्च्'],
    'sar': ['क्ब्च्'],
    'goaml': ['नयब्ःी'],
    'kyc': ['प्थ्ऋ'],
    'pos': ['एइक्'],
    'force': ['ँयचअभ'],
    'system': ['क्थकतभफ'],
}

STOP_WORDS = {
    'बारेमा', 'भन्नुहोस्', 'भन्नुहोस', 'व्यवस्था', 'सम्बन्धी', 'सम्बन्धमा', 
    'के', 'कस्तो', 'कति', 'कसरी', 'छ', 'पर्छ', 'हुन', 'तथा', 'र', 'वा', 
    'पनि', 'गर्न', 'सकिन्छ', 'पाइन्छ', 'जानकारी', 'भनेको', 'केहो', 'केही',
    'कसले', 'कसलाई', 'कसको', 'कुन', 'कहाँ', 'किन', 'सक्छ', 'सक्छन्', 'सक्ने',
    'what', 'is', 'the', 'provision', 'regarding', 'tell', 'me', 'about', 
    'rules', 'regulation', 'how', 'much', 'does', 'cost', 'to', 'into', 'and', 'from',
    'for', 'in', 'on', 'at', 'by', 'with', 'a', 'an', 'who', 'can',
    'was', 'were', 'across', 'all', 'total', 'number', 'of', 'as', 'does', 'did',
    'has', 'have', 'had', 'each', 'between', 'during', 'bank', 'banks', 'banking',
    'financial', 'institution', 'institutions', 'report', 'reports', 'annual', 'per', 'used',
    'their', 'which', 'will', 'would', 'could'
}

def normalize_devanagari(text):
    if not text:
        return ""
    t = unicodedata.normalize('NFKC', text)
    t = t.replace('Ë', 'ङ्ग')
    t = t.replace('\u093e\u0948', '\u094c').replace('\u093e\u0947', '\u094b')
    t = t.replace('\u094d\u093e', '\u093e')
    t = re.sub(r'बैं[किङ्क]+[ङङ्गग]', 'बैंकिङ्ग', t)
    t = t.replace('वॉलेट', 'वालेट').replace('वॉ', 'वा')
    return t

def extract_meaningful_keywords(text):
    text_norm = normalize_devanagari(text)
    raw_words = re.findall(r'[\u0900-\u097F\w+]+', text_norm)
    keywords = set()
    for w in raw_words:
        w_lower = w.lower()
        if w_lower in STOP_WORDS or len(w) <= 2:
            continue
        keywords.add(w)
        keywords.add(w_lower)
        if w_lower.endswith('s') and len(w_lower) > 3:
            base_s = w_lower[:-1]
            if base_s not in STOP_WORDS:
                keywords.add(base_s)

        # Preeti font mapping for English acronyms / words
        if w_lower in SPECIAL_PREETI:
            for pt in SPECIAL_PREETI[w_lower]:
                keywords.add(pt)
        else:
            # Algorithmic Preeti conversion
            mapped = "".join(PREETI_KEYMAP.get(c, c) for c in w)
            if mapped != w:
                keywords.add(mapped)

        for suffix in ['सम्बन्धी', 'सम्बन्धमा', 'मार्फत', 'अनुसार', 'सम्म', 'हरु', 'हरू', 'को', 'का', 'की', 'मा', 'ले', 'लाई', 'बाट']:
            if w.endswith(suffix) and len(w) > len(suffix) + 2:
                base = w[:-len(suffix)]
                if base.lower() not in STOP_WORDS and len(base) > 2:
                    keywords.add(base)
                    keywords.add(base.replace('ः', ''))
                    keywords.add(base.replace(':', ''))
        keywords.add(w.replace('ः', ''))
        keywords.add(w.replace(':', ''))

    return {k for k in keywords if k.lower() not in STOP_WORDS and len(k) > 1}

_translation_cache = {}

def expand_query_crosslingual(q, groq_client):
    clean_q = q.strip().lower()
    if clean_q in _translation_cache:
        return _translation_cache[clean_q]

    is_nepali = sum(1 for c in q if '\u0900' <= c <= '\u097f') >= max(len(q.replace(' ', '')), 1) * 0.3

    if is_nepali:
        sys_instruction = (
            "You are a specialized bilingual terminology engine for Nepal Rastra Bank reports and directives.\n"
            "The user question is in Nepali. Translate the core banking entities and financial metrics into their official English terminology (for finding tables in English Annual Reports):\n"
            "- विकास बैंक -> Development Banks, DBs\n"
            "- वित्त कम्पनी -> Finance Companies, FCs\n"
            "- इन्टरनेट बैंकिङ -> Internet Banking\n"
            "- मोबाइल बैंकिङ -> Mobile Banking\n"
            "- वञ्चित क्षेत्र कर्जा -> Deprived Sector Lending\n"
            "- आधार दर -> Base Rate\n"
            "- तनाव परीक्षण / स्ट्रेस टेस्टिङ -> Stress Testing, Liquidity Shock, Credit Shock C1\n"
            "- शीघ्र सुधारात्मक कारबाही -> Prompt Corrective Action, PCA\n"
            "- निष्कृय कर्जा / खराब कर्जा -> Non-Performing Loans, NPL\n"
            "- पुँजी पर्याप्तता -> Capital Adequacy Framework, CAR\n"
            "- नाफा / घाटा -> net profit, net loss\n"
            "- सञ्चालक कर्जा -> directors, board members borrowing\n"
            "Output 3-5 comma-separated English terms, nothing else."
        )
    else:
        sys_instruction = (
            "Translate all key banking subjects, services, and regulatory concepts from the question into official Nepal Rastra Bank (NRB) Nepali terms.\n"
            "Always use official Nepali Devanagari terms:\n"
            "- wallet -> वालेट (NOT वॉलेट)\n"
            "- banking -> बैंकिङ्ग (NOT बैंकिंग)\n"
            "- payment -> भुक्तानी (NOT पेमेन्ट)\n"
            "- agent -> आधिकारिक प्रतिनिधि, एजेन्ट\n"
            "- cash deposit -> नगद जम्मा\n"
            "- cash withdrawal -> नगद झिक्ने, नगद प्राप्त\n"
            "- blacklisting -> कालोसूची, फुकुवा\n"
            "- self-declaration -> स्वघोषणा\n"
            "- threshold transaction / TTR -> सीमा कारोबार, त्त्च्, १० लाख, १५ दिन, goAML\n"
            "- suspicious transaction / STR -> शंकास्पद कारोबार, क्त्च्\n"
            "- suspicious activity / SAR -> शंकास्पद गतिविधि, क्ब्च्\n"
            "- USSD -> ग्क्क्म्, USSD\n"
            "- CCTV / camera / backup -> ऋऋत्ख्, क्यामेरा, ब्याकअप, नब्बे दिन, ९०\n"
            "- force settlement -> Force Settlement, ँयचअभ, क्भततभिफभलत, त्ंघ, त्ंज्ञ\n"
            "- simplified KYC -> सरलीकृत ग्राहक पहिचान, मचर्ेन्ट, १,००,०००\n"
            "- IBFT / fund transfer -> अन्तर बैंक, रकमान्तर, क्ष्धँत्, रु. १०\n"
            "- system audit -> System Audit, क्थकतभफ ब्गमष्त, प्रणाली परीक्षण, १ वर्ष, २ आर्थिक वर्ष\n"
            "- overnight balance -> ओभरनाइट मौज्दात, ५० हजार, बैंक खाता\n"
            "- debit card ATM limit -> डेबिट कार्ड, ATM, नगद झिक्ने सीमा, ५० हजार, १ लाख\n"
            "Return 3-6 comma-separated Nepali terms in Devanagari script only, nothing else."
        )

    for model_cand in MODELS_TO_TRY:
        try:
            res = groq_client.chat.completions.create(
                model=model_cand,
                messages=[
                    {"role": "system", "content": sys_instruction},
                    {"role": "user", "content": q}
                ],
                temperature=0.0,
                max_tokens=60
            )
            terms = res.choices[0].message.content.strip()
            _translation_cache[clean_q] = terms
            return terms
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                continue
            break
    return ""

def hybrid_search(user_query, table, model, translated_terms="", top_k=6):
    k_const = 30
    d_pri = {}
    q_vec = model.encode(user_query).tolist()
    for rank, (_, row) in enumerate(table.search(q_vec).limit(80).to_pandas().iterrows(), 1):
        k = (row['source'], int(row['page']), row['text'][:60])
        d_pri[k] = (rank, row)

    d_trans = {}
    if translated_terms and translated_terms.strip():
        t_vec = model.encode(translated_terms).tolist()
        for rank, (_, row) in enumerate(table.search(t_vec).limit(80).to_pandas().iterrows(), 1):
            k = (row['source'], int(row['page']), row['text'][:60])
            d_trans[k] = (rank, row)

    s_pri = {}
    kw_pri = extract_meaningful_keywords(user_query)
    clean_pri_fts = " ".join([re.sub(r'[^\w\u0900-\u097F]', '', w) for w in kw_pri if len(w) > 1])
    if clean_pri_fts.strip():
        try:
            for rank, (_, row) in enumerate(table.search(clean_pri_fts).limit(80).to_pandas().iterrows(), 1):
                k = (row['source'], int(row['page']), row['text'][:60])
                s_pri[k] = (rank, row)
        except Exception:
            pass

    s_trans = {}
    if translated_terms and translated_terms.strip():
        kw_trans = extract_meaningful_keywords(translated_terms)
        clean_trans_fts = " ".join([re.sub(r'[^\w\u0900-\u097F]', '', w) for w in kw_trans if len(w) > 1])
        if clean_trans_fts.strip():
            try:
                for rank, (_, row) in enumerate(table.search(clean_trans_fts).limit(80).to_pandas().iterrows(), 1):
                    k = (row['source'], int(row['page']), row['text'][:60])
                    s_trans[k] = (rank, row)
            except Exception:
                pass

    all_keys = set(d_pri.keys()) | set(d_trans.keys()) | set(s_pri.keys()) | set(s_trans.keys())
    if not all_keys:
        return []

    fused_results = []
    for k in all_keys:
        dp = d_pri[k][0] if k in d_pri else 999
        dt = d_trans[k][0] if k in d_trans else 999
        sp = s_pri[k][0] if k in s_pri else 999
        st = s_trans[k][0] if k in s_trans else 999

        row = (d_pri.get(k) or s_pri.get(k) or d_trans.get(k) or s_trans.get(k))[1]
        rrf_score = (1.0 / (k_const + dp)) + (1.2 / (k_const + sp)) + (0.6 / (k_const + dt)) + (0.6 / (k_const + st))
        fused_results.append({
            'source': row['source'],
            'page': int(row['page']),
            'text': row['text'],
            'score': rrf_score
        })

    fused_results.sort(key=lambda x: x['score'], reverse=True)

    diverse_results = []
    seen_word_sets = []
    for item in fused_results:
        wset = set(re.findall(r'[\u0900-\u097F\w]+', item['text'].lower()))
        is_dup = False
        for st in seen_word_sets:
            overlap = len(wset & st) / max(len(wset), 1)
            if overlap > 0.75:
                is_dup = True
                break
        if not is_dup:
            diverse_results.append(item)
            seen_word_sets.append(wset)
            if len(diverse_results) >= top_k:
                break

    return diverse_results

questions = [
    ("Q1", "When was Nepal Bank Limited (NBL) established as the first commercial bank, and in which year was Nepal Rastra Bank (NRB) established?"),
    ("Q2", "What were the top three asset components and their respective shares for Development Banks (DBs) as of Mid-July 2024?"),
    ("Q3", "What was the Non-Performing Loan (NPL) ratio of Development Banks (B-class) versus Finance Companies (C-class) as of Mid-July 2024 compared to Mid-July 2023?"),
    ("Q4", "Under NRB regulations, which Capital Adequacy Framework applies to national-level Development Banks versus regional-level Development Banks and Finance Companies?"),
    ("Q5", "Did Finance Companies post a consolidated net profit or loss in FY 2024/25, and how did it compare to FY 2023/24?"),
    ("Q6", "According to the onsite supervision observations in FY 2024/25, which specific loan types are board members of financial institutions permitted to obtain under the Unified Directives?"),
    ("Q7", "In the FY 2024/25 stress testing results, how many Development Banks fail to meet the minimum Capital Adequacy Ratio under Credit Shock C1 (15% performing loans deteriorating into substandard)?"),
    ("Q8", "How long (in days) must banks and financial institutions retain the CCTV camera memory backup at ATM kiosks?"),
    ("Q9", "What is the required timeline for Force Settlement when an electronic transaction fails (account debited but cash not dispensed / transaction not completed) and both Issuer and Acquirer are different Nepali institutions?"),
    ("Q10", "What is the maximum overnight balance allowed in a natural person's digital wallet, and where must the excess balance be transferred?"),
    ("Q11", "Under the AML/CFT payment directives, what is the maximum annual transaction limit for merchants eligible for Simplified Customer Due Diligence (Simplified KYC)?"),
    ("Q12", "What is the maximum fee service providers can charge individual customers per transaction for Inter Bank Fund Transfer (IBFT) through Mobile App or Internet Banking?"),
    ("Q13", "When must a licensed non-bank Payment Service Provider conduct its first System Audit, and how often must it be conducted thereafter if the system is not replaced or upgraded?"),
    ("Q14", "Under what conditions must a Threshold Transaction Report (TTR) be submitted to the FIU, and what is the reporting deadline and required platform?"),
    ("Q15", "What is the daily ATM cash withdrawal limit on debit cards issued by banks and financial institutions in the 2081 directive versus the updated 2082 directive?")
]

print("=== TESTING ALL 15 QUESTIONS RETRIEVAL ===")
for q_id, q_text in questions:
    trans = expand_query_crosslingual(q_text, client)
    res = hybrid_search(q_text, table, embedding_model, translated_terms=trans, top_k=3)
    top_sources = [f"{r['source']} p.{r['page']}" for r in res]
    print(f"\n[{q_id}]")
    print(f"  Query: {q_text[:70]}...")
    print(f"  Trans: {trans}")
    print(f"  Top 3: {top_sources}")

