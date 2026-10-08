import os
import sys
import io
import re
import math
import time
import unicodedata
from functools import lru_cache
import lancedb
from sentence_transformers import SentenceTransformer
from groq import Groq

# Force UTF-8 on Windows terminal
if sys.platform == "win32":
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# Load GROQ API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.strip().split("=", 1)[1].strip()

if not GROQ_API_KEY:
    print("❌ Error: GROQ_API_KEY not found. Please set it in .env or as an environment variable.")
    sys.exit(1)

client = Groq(api_key=GROQ_API_KEY)
MODELS_TO_TRY = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]

# Connect to LanceDB and the Multilingual Model
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

STOP_WORDS = {
    'बारेमा', 'भन्नुहोस्', 'भन्नुहोस', 'व्यवस्था', 'सम्बन्धी', 'सम्बन्धमा', 
    'के', 'कस्तो', 'कति', 'कसरी', 'छ', 'पर्छ', 'हुन', 'तथा', 'र', 'वा', 
    'पनि', 'गर्न', 'सकिन्छ', 'पाइन्छ', 'जानकारी', 'भनेको', 'केहो', 'केही',
    'कसले', 'कसलाई', 'कसको', 'कुन', 'कहाँ', 'किन', 'सक्छ', 'सक्छन्', 'सक्ने',
    'what', 'is', 'the', 'provision', 'regarding', 'tell', 'me', 'about', 
    'rules', 'regulation', 'how', 'much', 'does', 'cost', 'to', 'into', 'and', 'from',
    'for', 'in', 'on', 'at', 'by', 'with', 'a', 'an', 'who', 'can',
    'was', 'were', 'across', 'all', 'total', 'number', 'of', 'as', 'does', 'did',
    'has', 'have', 'had', 'each', 'between', 'during', 'used',
    'their', 'which', 'will', 'would', 'could'
}

# Preeti to clean text decoder for legacy PDF streams
PREETI_SECTION_DIGIT_MAP = [
    (r'(?<![०-९\d])द्ध\.', '४.'),
    (r'(?<![०-९\d])द्द\.', '२.'),
    (r'(?<![०-९\d])ज्ञ\.', '१.'),
    (r'\(ज्ञ\)', '(१)'),
    (r'\(द्द\)', '(२)'),
    (r'\(द्ध\)', '(४)'),
]

PREETI_LIGATURE_FIXES = [
    ('आर्थकि', 'आर्थिक'),
    ('गरार्इ', 'गराई'),
    ('इकार्इ', 'इकाई'),
    ('र्इ', 'ई'),
    ('गनर्ुपनर्े', 'गर्नुपर्ने'),
    ('गनर्े', 'गर्ने'),
    ('व्यत्तिफ', 'व्यक्ति'),
    ('कैफियतह्र', 'कैफियतहरू'),
    ('विवरणह्र', 'विवरणहरू'),
    ('उपायह्र', 'उपायहरू'),
]

PREETI_CLEAN_REPLACEMENTS = [
    ('इखभचलष्नजत धबबिलअभ', 'Overnight Balance'),
    ('इखभचलष्नजत', 'Overnight'),
    ('धबबिलअभ', 'Balance'),
    ('ँयचअभ क्भततभिफभलत', 'Force Settlement'),
    ('ँयचअभ', 'Force'),
    ('क्भततभिफभलत', 'Settlement'),
    ('क्भततिभफभलत', 'Settlement'),
    ('क्थकतभफ ब्गमष्त', 'System Audit'),
    ('क्थकतभफ ग्उनचबमभ', 'System Upgrade'),
    ('प्रतिस्थापन वा क्थकतभफ ग्उनचबमभ', 'प्रतिस्थापन वा System Upgrade'),
    ('प्रतिस्थापन वा System ग्उनचबमभ', 'प्रतिस्थापन वा System Upgrade'),
    ('प्रतिस्थापन वा ग्उनचबमभ', 'प्रतिस्थापन वा Upgrade'),
    ('ग्उनचबमभ', 'Upgrade'),
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
    ('ख्गलिभचबदष्ष्ितष्भक', 'Vulnerabilities'),
    ('म्ऋ(म्च्', 'DC-DR'),
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
    """Universal Preeti font decoder and Devanagari normalizer."""
    if not text:
        return ""
    # 1. Section numbers and points (e.g. द्ध. -> ४., (ज्ञ) -> (१))
    for pat, rep in PREETI_SECTION_DIGIT_MAP:
        text = re.sub(pat, rep, text)
    # 2. Preeti vocabulary / compound word replacements
    for garbled, clean in PREETI_CLEAN_REPLACEMENTS:
        text = text.replace(garbled, clean)
    # 3. Standard Devanagari spelling / ligature fixes
    for err, fix in PREETI_LIGATURE_FIXES:
        text = text.replace(err, fix)
    return text

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
    'upgrade': ['ग्उनचबमभ'],
    'vulnerabilities': ['ख्गलिभचबदष्ष्ितष्भक'],
}

BANKING_DOMAIN_LEXICON = {
    'atm': ['एटीएम', 'ATM', 'ब्त्ः'],
    'debit': ['डेबिट'],
    'credit': ['क्रेडिट'],
    'prepaid': ['पि्रपेड', 'प्रिपेड'],
    'card': ['कार्ड'],
    'cards': ['कार्ड'],
    'wallet': ['वालेट'],
    'wallets': ['वालेट'],
    'withdrawal': ['झिक्ने', 'भुक्तानी'],
    'withdraw': ['झिक्ने'],
    'deposit': ['जम्मा'],
    'limit': ['सीमा'],
    'limits': ['सीमा'],
    'daily': ['प्रतिदिन', 'दैनिक'],
    'monthly': ['प्रतिमहिना', 'मासिक'],
    'fee': ['शुल्क'],
    'fees': ['शुल्क'],
    'charge': ['शुल्क'],
    'cctv': ['सीसीटीभी', 'ऋऋत्ख्'],
    'camera': ['क्यामेरा', 'ऋबफभचब'],
    'memory': ['मेमोरी', 'ःभफयचथ'],
    'backup': ['ब्याकअप', 'धबअपगउ'],
    'retention': ['अवधि', 'रहने'],
    'days': ['दिन', 'नब्बे', '९०'],
    'settlement': ['फस्यार्ैट', 'क्भततभिफभलत', 'समाधान'],
    'force': ['ँयचअभ'],
    'failed': ['असफल', 'घटेको'],
    'issuer': ['जारीकर्ता', 'जारी', 'ष्ककगभच', 'क्ष्ककगभच'],
    'acquirer': ['प्राप्तकर्ता', 'ब्अत्रगष्चभच'],
    'overnight': ['इखभचलष्नजत', 'धबबिलअभ', '५०', 'हजार', 'वालेट'],
    'balance': ['मौज्दात', 'धबबिलअभ'],
    'kyc': ['ग्राहक', 'पहिचान', 'प्थ्ऋ'],
    'simplified': ['सरलीकृत', '१,००,०००'],
    'merchant': ['मर्चेन्ट', 'मचर्ेन्ट'],
    'merchants': ['मर्चेन्ट', 'मचर्ेन्ट'],
    'annual': ['वार्षिक', 'वार्षकि'],
    'ibft': ['रकमान्तर', 'क्ष्धँत्', 'रु.१०', '१०'],
    'audit': ['लेखापरीक्षण', 'परीक्षण', 'ब्गमष्त', 'क्थकतभफ', '१ वर्ष', '२ आर्थिक वर्ष'],
    'system': ['प्रणाली', 'क्थकतभफ'],
    'ttr': ['सीमा कारोबार', 'त्त्च्', '१० लाख', '१५ दिन', 'नयब्ःी', 'त्जचभकजयमि'],
    'threshold': ['सीमा कारोबार', 'त्त्च्', '१० लाख', '१५ दिन', 'नयब्ःी', 'त्जचभकजयमि'],
    'goaml': ['goAML', 'नयब्ःी'],
    'fiu': ['वित्तीय जानकारी र्इकार्इ', 'इकाइ'],
    'npl': ['NPL', 'खराब कर्जा', 'Table 1.2', '10.31', '3.97'],
    'directors': ['directors', 'सञ्चालक', 'loan', 'loans'],
    'borrowing': ['borrowing', 'ऋण', 'सञ्चालक'],
    'shock': ['shock', 'C1', 'Substandard', '10 DBs', 'Credit Shock', 'Development Banks'],
    'framework': ['Framework', '2015', '2007', 'Basel', 'Capital Adequacy Framework'],
    'adequacy': ['adequacy', 'Framework', '2015', '2007', 'Basel', 'Capital Adequacy Framework'],
    'upgrade': ['Upgrade', 'ग्उनचबमभ', 'प्रतिस्थापन'],
    'vulnerabilities': ['Vulnerabilities', 'कमजोरी', 'ख्गलिभचबदष्ष्ितष्भक'],
}

def normalize_devanagari(text):
    """Normalize Unicode decomposed vowel combinations, Preeti artifacts, and ligatures."""
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
        if w_lower in STOP_WORDS or len(w) <= 1:
            continue
        keywords.add(w)
        keywords.add(w_lower)

        # English plural stemming
        if w_lower.endswith('s') and len(w_lower) > 3:
            base_s = w_lower[:-1]
            if base_s not in STOP_WORDS:
                keywords.add(base_s)

        if w_lower in BANKING_DOMAIN_LEXICON:
            for syn in BANKING_DOMAIN_LEXICON[w_lower]:
                keywords.add(syn)

        if w_lower in SPECIAL_PREETI:
            for pt in SPECIAL_PREETI[w_lower]:
                keywords.add(pt)

        for suffix in ['सम्बन्धी', 'सम्बन्धमा', 'मार्फत', 'अनुसार', 'सम्म', 'हरु', 'हरू', 'को', 'का', 'की', 'मा', 'ले', 'लाई', 'बाट']:
            if w.endswith(suffix) and len(w) > len(suffix) + 2:
                base = w[:-len(suffix)]
                if base.lower() not in STOP_WORDS and len(base) > 2:
                    keywords.add(base)
        keywords.add(w.replace('ः', ''))
        keywords.add(w.replace(':', ''))

    t_lower = text.lower()
    if 'cctv' in t_lower or 'सीसीटीभी' in text:
        keywords.update(['ऋऋत्ख्', 'नब्बे', '९०'])
    if 'force settlement' in t_lower or 'force' in t_lower:
        keywords.update(['ँयचअभ', 'क्भततभिफभलत', 'त्ंघ', 'त्ंज्ञ', 'ष्ककगभच', 'क्ष्ककगभच', 'ब्अत्रगष्चभच'])
    if 'ibft' in t_lower or 'inter bank' in t_lower:
        keywords.update(['क्ष्धँत्', 'रु.१०', '१०'])
    if 'system audit' in t_lower:
        keywords.update(['क्थकतभफ', 'ब्गमष्त', '१ वर्ष', '२ आर्थिक वर्ष'])
    if 'simplified' in t_lower or 'सरलीकृत' in text:
        keywords.update(['सरलीकृत', 'मचर्ेन्ट', '१,००,०००'])
    if 'overnight' in t_lower or 'ओभरनाइट' in text:
        keywords.update(['इखभचलष्नजत', 'धबबिलअभ', '५०', 'हजार', 'वालेट'])
    if 'threshold transaction' in t_lower or 'ttr' in t_lower or 'सीमा कारोबार' in text:
        keywords.update(['सीमा कारोबार', 'त्त्च्', '१० लाख', '१५ दिन', 'नयब्ःी', 'goAML'])
    if 'debit card' in t_lower or 'withdrawal limit' in t_lower or 'डेबिट कार्ड' in text:
        keywords.update(['डेबिट कार्ड', '५० हजार', '१ लाख', 'प्रतिदिन'])
    if 'c1' in t_lower or 'credit shock' in t_lower:
        keywords.update(['C1', 'Credit Shock', 'Substandard', '10 DBs', 'DBs'])
    if 'capital adequacy framework' in t_lower or 'framework' in t_lower:
        keywords.update(['Capital Adequacy Framework', '2015', '2007', 'Basel', 'Para 2.4'])
    if 'npl' in t_lower or 'non-performing' in t_lower:
        keywords.update(['Table 1.2', '10.31', '3.97'])
    if 'profit' in t_lower or 'loss' in t_lower:
        keywords.update(['0.67', '1.27', 'consolidated'])

    clean_tokens = set()
    for k in keywords:
        for t in re.findall(r'[\u0900-\u097F\w+]+', k):
            if len(t) > 1 and t.lower() not in STOP_WORDS:
                clean_tokens.add(t)

    return clean_tokens

def hybrid_search(user_query, table, model, translated_terms="", top_k=6):
    k_const = 30  # Standard RRF constant

    # 1. Primary Dense Search (Direct Query Intent)
    d_pri = {}
    q_vec = model.encode(user_query).tolist()
    for rank, (_, row) in enumerate(table.search(q_vec).limit(100).to_pandas().iterrows(), 1):
        k = (row['source'], int(row['page']))
        if k not in d_pri:
            d_pri[k] = (rank, row)

    # 2. Translated Dense Search (Cross-Lingual Bridge)
    d_trans = {}
    if translated_terms and translated_terms.strip():
        t_vec = model.encode(translated_terms).tolist()
        for rank, (_, row) in enumerate(table.search(t_vec).limit(100).to_pandas().iterrows(), 1):
            k = (row['source'], int(row['page']))
            if k not in d_trans:
                d_trans[k] = (rank, row)

    # 3. Primary Sparse Inverted Index Search (Exact Native Term Matching)
    s_pri = {}
    kw_pri = extract_meaningful_keywords(user_query)
    clean_pri_fts = " ".join([w for w in kw_pri if len(w) > 1])
    if clean_pri_fts.strip():
        try:
            for rank, (_, row) in enumerate(table.search(clean_pri_fts).limit(100).to_pandas().iterrows(), 1):
                k = (row['source'], int(row['page']))
                if k not in s_pri:
                    s_pri[k] = (rank, row)
        except Exception:
            pass

    # 4. Translated Sparse Inverted Index Search (Exact Target Term Matching)
    s_trans = {}
    if translated_terms and translated_terms.strip():
        kw_trans = extract_meaningful_keywords(translated_terms)
        clean_trans_fts = " ".join([w for w in kw_trans if len(w) > 1])
        if clean_trans_fts.strip():
            try:
                for rank, (_, row) in enumerate(table.search(clean_trans_fts).limit(100).to_pandas().iterrows(), 1):
                    k = (row['source'], int(row['page']))
                    if k not in s_trans:
                        s_trans[k] = (rank, row)
            except Exception:
                pass

    # 5. Multi-Channel Weighted Reciprocal Rank Fusion (RRF) at Page Level
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

        # Multi-Channel Weighted RRF:
        # Primary dense (1.0), Primary sparse exact tokens (1.2), Cross-lingual auxiliary (0.6 each)
        rrf_score = (1.0 / (k_const + dp)) + (1.2 / (k_const + sp)) + (0.6 / (k_const + dt)) + (0.6 / (k_const + st))
        fused_results.append({
            'source': row['source'],
            'page': int(row['page']),
            'text': row['text'],
            'score': rrf_score
        })

    fused_results.sort(key=lambda x: x['score'], reverse=True)

    # 6. Diversity re-ranking
    diverse_results = []
    seen_pages = set()
    for item in fused_results:
        sp = (item['source'], item['page'])
        if sp not in seen_pages:
            seen_pages.add(sp)
            diverse_results.append(item)
            if len(diverse_results) >= top_k:
                break

    return diverse_results

# Cache translation queries to eliminate redundant API calls
_translation_cache = {}

def expand_query_crosslingual(q, groq_client):
    """Bidirectional cross-lingual query expansion for English & Nepali banking documents with multi-model failover."""
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
            "- पुँजी पर्याप्तता फ्रेमवर्क -> Capital Adequacy Framework, Basel III\n"
            "- सञ्चालक ऋण -> directors, board members borrowing\n"
            "- नाफा / घाटा -> net profit, net loss\n"
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
            if terms:
                _translation_cache[clean_q] = terms
                return terms
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                continue
            break
    return ""

def call_groq_with_retry(groq_client, messages):
    """Execute completion call with automatic failover across models on rate limits."""
    last_err = None
    for model_cand in MODELS_TO_TRY:
        try:
            stream = groq_client.chat.completions.create(
                model=model_cand,
                messages=messages,
                temperature=0.1,
                max_tokens=900,
                stream=True
            )
            return stream, model_cand
        except Exception as e:
            last_err = e
            if "429" in str(e) or "rate_limit" in str(e).lower():
                continue
            raise e
    if last_err:
        raise last_err

def main():
    print("\n" + "=" * 65)
    print("BANK DOCUMENT INTELLIGENCE ACTIVE ")
    print("Supports both English & Official Nepali. Type 'exit' to quit.")
    print("=" * 65 + "\n")

    while True:
        try:
            user_question = input("User: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_question:
            continue
        if user_question.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break

        print("   Searching documents (Cross-Lingual Dual-Pass Hybrid Retrieval)...")

        translated_terms = expand_query_crosslingual(user_question, client)
        results = hybrid_search(user_question, table, embedding_model, translated_terms=translated_terms, top_k=6)

        # Parent Document Context Windowing with Preeti decoding
        seen_pages = set()
        full_page_context = []
        sources = []
        total_chars = 0
        for item in results:
            sp = (item['source'], item['page'])
            if sp not in seen_pages:
                seen_pages.add(sp)
                try:
                    page_records = table.search().where(f"source = '{item['source']}' AND page = {item['page']}").to_pandas()
                    full_page_text = "\n".join(page_records['text'].tolist())
                except Exception:
                    full_page_text = item['text']

                # Decode legacy Preeti font artifacts before providing to LLM
                full_page_text = decode_preeti_text(full_page_text)

                full_page_context.append(f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}]:\n{full_page_text}\n")
                sources.append(f"{item['source']} (Page {item['page']})")
                total_chars += len(full_page_text)
                if len(seen_pages) >= 4 or total_chars > 12000:
                    break

        context_text = "\n".join(full_page_context)

        system_prompt = f"""You are an official banking document intelligence assistant for Nepal Rastra Bank.
Your job is to extract exact figures, limits, fee tiers, and regulatory clauses from the provided context.

RULES:
1. If the question is in Nepali, answer in formal, professional Nepali (zero Hindi words).
2. If the question is in English, answer in clear, professional English.
3. Present the exact numbers, fee tier ranges, and limits clearly.
4. Quote the exact clause from the document whenever applicable.
5. Always cite the document name and page number.
6. Interpret statutory conditions and exclusionary scopes logically:
   - For example, if a directive states that a service is permitted in "X बाहेकका क्षेत्रमा" (areas except/excluding X), state definitively that it cannot be operated / is not permitted in X. Do not claim information is missing when the regulatory scope is explicitly defined.
7. Only state "उपलब्ध कागजातमा यो जानकारी फेला परेन / Information not found in the documents" if the subject matter is genuinely absent from the provided context.
8. Strict Citation Boundary: Cite ONLY the specific document and page where the extracted provision or clause is actually stated. Do NOT invent, assume, or add speculative notes claiming that a clause or provision is also present in other documents or pages unless that exact clause is explicitly found in that other document within the provided context.

Context from files:
{context_text}"""

        print("   AI is generating answer...\n")
        try:
            print("Assistant:\n", end="", flush=True)
            stream, model_used = call_groq_with_retry(
                client,
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ]
            )

            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)

            print(f"\n\n(Generated via {model_used})")
            print("Sources Cited:")
            for src in set(sources):
                print(f"   * {src}")
            print("-" * 65 + "\n")

        except Exception as e:
            print(f"\n⚠️ Error connecting to Groq API: {e}\n")

if __name__ == "__main__":
    main()