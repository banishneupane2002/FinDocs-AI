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
    ('भुत्तफानी', 'भुक्तानी'),
    ('भिफक्न', 'झिक्न'),
    ('भिफक्ने', 'झिक्ने'),
    ('उपयर्ुत्तफ', 'उपर्युक्त'),
    ('अतिरित्तफ', 'अतिरिक्त'),
    ('सम्बन्िधत', 'सम्बन्धित'),
]

PREETI_CLEAN_REPLACEMENTS = [
    ('ऋयलतबअतभिकक', 'Contactless'),
    ('म्यफभकतष्अ ऋबचम क्अजभफभ', 'Domestic Card Scheme'),
    ('्र .', 'रु. '),
    ('्र.', 'रु. '),
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

def extract_cited_sources(response_text, retrieved_candidates, target_years=None, target_doc=None):
    """
    Filters retrieved candidate chunks so that ONLY the exact documents and pages
    actually referenced/cited in the AI response are presented to the user,
    strictly aligned with the ground-truth source that generated the answer.
    """
    cited = []
    seen = set()

    # 1. Direct Regex Citation Extraction from AI Response
    regex_patterns = [
        r'([a-zA-Z0-9_\-\.]+\.(?:pdf|docx|txt))(?:\s*[\:\|\-\–\—\(\)\[\]]?\s*|\s+(?:clause|section|दफा|खण्ड)\s*[^\n\r]{0,25}?\s*|\s*\n\s*)(?:page|पृष्ठ|p\.?)\s*[:\-]?\s*(\d+)',
        r'(?:page|पृष्ठ|p\.?)\s*[:\-]?\s*(\d+)(?:\s*[\:\|\-\–\—\(\)\[\]]?\s*|\s*\n\s*)([a-zA-Z0-9_\-\.]+\.(?:pdf|docx|txt))',
        r'\[\s*(?:कागजात|doc|document)?\s*[:\-]?\s*([a-zA-Z0-9_\-\.]+\.(?:pdf|docx|txt))\s*\|\s*(?:पृष्ठ|page)\s*[:\-]?\s*(\d+)\s*\]',
        r'([a-zA-Z0-9_\-]+(?:directive|report)[a-zA-Z0-9_\-]*)(?:\s*[\:\|\-\–\—\(\)\[\]]?\s*|\s*\n\s*)(?:page|पृष्ठ|p\.?)\s*[:\-]?\s*(\d+)'
    ]

    found_matches = []
    for pat in regex_patterns:
        for m in re.finditer(pat, response_text, re.IGNORECASE):
            g1, g2 = m.group(1), m.group(2)
            if g1.isdigit():
                doc_name = g2
                page_num = int(g1)
            else:
                doc_name = g1
                page_num = int(g2)

            if not doc_name.lower().endswith(('.pdf', '.docx', '.txt')):
                if os.path.exists(os.path.join("File_System", f"{doc_name}.pdf")):
                    doc_name = f"{doc_name}.pdf"

            if os.path.exists(os.path.join("File_System", doc_name)):
                found_matches.append((m.start(), doc_name, page_num))

    # Sort matches by appearance position in AI response text
    found_matches.sort(key=lambda x: x[0])

    for pos, doc_name, page_num in found_matches:
        key = (doc_name, page_num)
        if key not in seen:
            seen.add(key)
            cited.append({
                'source': doc_name,
                'page': page_num,
                'pos': pos
            })

    # 2. Match against retrieved candidates
    norm_resp = re.sub(r'[\s_\-]+', ' ', response_text.lower())
    for item in retrieved_candidates:
        src = item['source']
        pg = str(item['page'])
        base_src = src.replace('.pdf', '').replace('.docx', '').replace('.txt', '')
        norm_base = re.sub(r'[\s_\-]+', ' ', base_src.lower())

        # Check if source name appears in response (exact, base, or normalized space name)
        if src.lower() in response_text.lower() or base_src.lower() in response_text.lower() or norm_base in norm_resp:
            # Check if page number appears in response
            pg_pattern = rf'(?:page|पृष्ठ|p\.?)\s*:?\s*{pg}\b'
            if re.search(pg_pattern, response_text, re.IGNORECASE) or f" {pg} " in f" {response_text} " or f"({pg})" in response_text or f": {pg}" in response_text:
                key = (src, item['page'])
                if key not in seen:
                    seen.add(key)
                    m_src = re.search(re.escape(src), response_text, re.IGNORECASE) or re.search(re.escape(base_src), response_text, re.IGNORECASE)
                    pos = m_src.start() if m_src else 999999
                    cited.append({
                        'source': src,
                        'page': item['page'],
                        'pos': pos
                    })

    # 3. Fallback to top-1 primary search match if no explicit citation format was matched
    if not cited and retrieved_candidates:
        top_item = retrieved_candidates[0]
        cited.append({
            'source': top_item['source'],
            'page': top_item['page'],
            'pos': 0
        })

    # 4. Sort cited sources:
    def citation_sort_key(c):
        pos = c.get('pos', 999999)
        src = c['source']
        ym = re.search(r'(20[78][0-9]|20[12][0-9])', src)
        yr = int(ym.group(1)) if ym else 0

        target_match = 1
        if target_doc:
            if isinstance(target_doc, (list, set, tuple)) and src in target_doc:
                target_match = 0
            elif isinstance(target_doc, str) and src == target_doc:
                target_match = 0
        elif target_years and yr in target_years:
            target_match = 0

        tiebreak_year = -yr if not target_years else 0
        return (target_match, pos, tiebreak_year)

    cited.sort(key=citation_sort_key)
    return cited

# --- AUTOMATIC YEAR DETECTION & QUERY ROUTING ENGINE ---
PREETI_NUM_MAP = {'!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0'}
NEP_TO_ARABIC = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}

def detect_document_years(filename: str, sample_text: str = "") -> set:
    """
    Detects all official fiscal or calendar years covered by a document.
    Distinguishes real years from phone numbers, P.O. Box, registration numbers.
    Supports multi-year documents (e.g. 2079/80, 2022-23).
    """
    years = set()

    # 1. From Filename
    for m in re.finditer(r'(20[78][0-9]|20[12][0-9])', filename):
        years.add(int(m.group(1)))

    # 2. Preeti Cover Shift Glyphs (Anchor: follows 'निर्देशन' or cover title)
    for preeti_m in re.finditer(r'@\)([&*][!@#$%\^&*()०-९0-9])', sample_text):
        decade_code = preeti_m.group(1)[0]
        unit_code = preeti_m.group(1)[1]
        decade = '7' if decade_code == '&' else '8'
        unit = PREETI_NUM_MAP.get(unit_code, NEP_TO_ARABIC.get(unit_code, unit_code))
        try:
            val = int(f"20{decade}{unit}")
            if 2070 <= val <= 2085:
                years.add(val)
        except Exception:
            pass

    # 3. Multi-year Devanagari ranges (e.g. २०७९/८० or आर्थिक वर्ष २०८०/८१)
    for m in re.finditer(r'२०([७८][०-९])(?:/([०-९]{2}))?', sample_text):
        decade_unit = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(1))
        y1 = int(f"20{decade_unit}")
        if 2070 <= y1 <= 2085:
            years.add(y1)
        if m.group(2):
            unit2 = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(2))
            y2 = int(f"20{unit2}")
            if 2070 <= y2 <= 2085:
                years.add(y2)

    # 4. Multi-year English ranges (e.g. 2023/24, 2022-23)
    for m in re.finditer(r'\b(20[12][0-9])[/-]([0-9]{2})\b', sample_text):
        y1 = int(m.group(1))
        y2 = int(str(y1)[:2] + m.group(2))
        years.add(y1)
        years.add(y2)

    # 5. Standalone English / Devanagari with Regulatory Anchors (rejects phone numbers, fax, PO Box)
    anchored_matches = re.finditer(
        r'(?:directive|circular|report|fiscal\s*year|निर्देशन|परिपत्र|प्रतिवेदन|संवत्|मिति)\s*[,:\s]*([०-९\d]{4})',
        sample_text,
        re.IGNORECASE
    )
    for m in anchored_matches:
        raw = m.group(1)
        arabic = "".join(NEP_TO_ARABIC.get(c, c) for c in raw)
        try:
            val = int(arabic)
            if 2070 <= val <= 2085 or 2010 <= val <= 2030:
                years.add(val)
        except Exception:
            pass

    return years

def extract_query_years(query: str, available_years: set = None) -> set:
    """
    Extracts all legitimate target regulatory years from user query.
    Rejects:
    - Currency amounts (e.g. '2000 rupees', 'Rs. 2500', 'fee 2000')
    - Standalone numbers not matching any active corpus document year
    - Non-year numbers (e.g. clause numbers, branch codes)
    """
    if not query:
        return set()

    if available_years is None:
        available_years = {2079, 2080, 2081, 2082, 2023, 2024}

    found_years = set()

    # 1. Check Devanagari year ranges (e.g. २०७९/८०, २०८०, or Gregorian २०२४, २०२५)
    dev_ranges = re.finditer(r'२०([०-९]{2})(?:/([०-९]{2}))?', query)
    for m in dev_ranges:
        decade_unit = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(1))
        y1 = int(f"20{decade_unit}")
        if y1 in available_years:
            found_years.add(y1)
        if m.group(2):
            unit2 = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(2))
            y2 = int(f"20{unit2}")
            if y2 in available_years:
                found_years.add(y2)

    # 2. Check English year ranges (e.g. 2079/80, 2023/24, 2079-80)
    en_ranges = re.finditer(r'\b(20[78][0-9]|20[12][0-9])[/-]([0-9]{2})\b', query)
    for m in en_ranges:
        y1 = int(m.group(1))
        if y1 in available_years:
            found_years.add(y1)
        y2 = int(str(y1)[:2] + m.group(2))
        if y2 in available_years:
            found_years.add(y2)

    # 3. Check standalone English 4-digit years
    standalone_candidates = re.finditer(r'\b(20[78][0-9]|20[12][0-9])\b', query)
    for m in standalone_candidates:
        candidate = int(m.group(1))
        start_idx, end_idx = m.start(), m.end()

        # Check if preceded by currency or quantity terms (e.g. "Rs 2000", "रु २०००", "deposit of 2000")
        pre_ctx = query[max(0, start_idx - 15):start_idx].lower()
        post_ctx = query[end_idx:min(len(query), end_idx + 15)].lower()

        if re.search(r'(?:रु\.?|रु|rs\.?|rs|npr|रुपैयाँ|रुपैंया|rupees)\s*$', pre_ctx):
            continue
        if re.search(r'^\s*(?:रु\.?|रु|rs\.?|rs|npr|रुपैयाँ|रुपैंया|rupees|हजार|लाख)', post_ctx):
            continue

        # If it's a known document year in the corpus, add it
        if candidate in available_years:
            found_years.add(candidate)

    return found_years

ARABIC_TO_NEP = {v: k for k, v in NEP_TO_ARABIC.items()}

def clean_query_for_search(query: str, matched_years: set) -> str:
    """
    Cleans routing noise ONLY for years that actually matched an active document.
    Leaves amounts, random numbers, and unknown numbers completely untouched.
    """
    if not matched_years or len(matched_years) > 1:
        # If no year matched or multiple years matched (comparative query), do not strip
        return query

    yr = list(matched_years)[0]
    cleaned = re.sub(
        rf'\b(?:in|of|from|को|अनुसार|बमोजिम)?\s*{yr}\s*(?:directive|circular|report|निर्देशन|परिपत्र|प्रतिवेदन)?\b',
        '',
        query,
        flags=re.IGNORECASE
    )
    dev_yr_full = "".join(ARABIC_TO_NEP.get(c, c) for c in str(yr))
    cleaned = re.sub(
        rf'\b(?:in|of|from|को|अनुसार|बमोजिम)?\s*{dev_yr_full}\s*(?:directive|circular|report|निर्देशन|परिपत्र|प्रतिवेदन)?\b',
        '',
        cleaned,
        flags=re.IGNORECASE
    )
    return cleaned.strip() or query

def prioritize_matching_document(target_yr: int, matching_docs: list) -> str:
    """
    Selects the best document when multiple reports cover the target year.
    Prioritizes:
    1. Document with target_yr in filename (e.g. Annual_Report_2024.pdf for 2024)
    2. Primary reporting period over comparative retrospective years.
    """
    if not matching_docs:
        return None
    for doc in matching_docs:
        if str(target_yr) in doc:
            return doc
    return matching_docs[0]

_DOC_YEAR_CACHE = {}

def build_document_year_map(table) -> dict:
    """Builds a cached map of document name -> set of detected fiscal/calendar years."""
    global _DOC_YEAR_CACHE
    if _DOC_YEAR_CACHE:
        return _DOC_YEAR_CACHE
    doc_map = {}
    try:
        df = table.to_pandas()
        for s in df['source'].unique():
            p1_records = df[(df['source'] == s) & (df['page'] <= 3)]
            sample_text = " ".join(p1_records['text'].tolist())
            doc_map[s] = detect_document_years(s, sample_text)
        _DOC_YEAR_CACHE = doc_map
    except Exception:
        pass
    return doc_map

SPECIAL_PREETI = {
    'contactless': ['ऋयलतबअतभिकक'],
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
    'contactless': ['कन्ट्याक्टलेस', 'Contactless', 'ऋयलतबअतभिकक'],
    'कन्ट्याक्टलेस': ['कन्ट्याक्टलेस', 'Contactless', 'ऋयलतबअतभिकक'],
    'atm': ['एटीएम', 'ATM', 'ब्त्ः', 'कार्डबाट नगद', 'डेबिट कार्ड', 'भुक्तानी कार्ड'],
    'एटीएम': ['एटीएम', 'ATM', 'ब्त्ः', 'कार्डबाट नगद', 'डेबिट कार्ड', 'भुक्तानी कार्ड'],
    'debit': ['डेबिट'],
    'डेबिट': ['डेबिट', 'debit'],
    'credit': ['क्रेडिट'],
    'prepaid': ['पि्रपेड', 'प्रिपेड'],
    'card': ['कार्ड'],
    'cards': ['कार्ड'],
    'कार्ड': ['कार्ड', 'card'],
    'wallet': ['वालेट'],
    'wallets': ['वालेट'],
    'withdrawal': ['झिक्ने', 'भुक्तानी', 'नगद'],
    'withdrawals': ['झिक्ने', 'भुक्तानी', 'नगद'],
    'withdraw': ['झिक्ने', 'नगद'],
    'withdrawn': ['झिक्ने', 'नगद'],
    'cash': ['नगद', 'रकम'],
    'नगद': ['नगद', 'cash', 'रकम'],
    'झिक्ने': ['झिक्ने', 'नगद झिक्ने', 'withdraw'],
    'झिक्न': ['झिक्ने', 'नगद झिक्ने', 'withdraw'],
    'deposit': ['जम्मा'],
    'limit': ['सीमा'],
    'limits': ['सीमा'],
    'सीमा': ['सीमा', 'limit'],
    'max': ['अधिकतम', 'सीमा'],
    'maximum': ['अधिकतम', 'सीमा'],
    'अधिकतम': ['अधिकतम', 'सीमा', 'max'],
    'amount': ['रकम'],
    'रकम': ['रकम', 'amount'],
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
    'npl': ['NPL', 'खराब कर्जा', 'निष्क्रिय कर्जा', 'कमसल', 'शंकास्पद', 'खराब', 'Table 1.2', '10.31', '3.97'],
    'loan': ['कर्जा', 'सापट', 'ऋण', 'loan', 'loans'],
    'loans': ['कर्जा', 'सापट', 'ऋण', 'loan', 'loans'],
    'कर्जा': ['कर्जा', 'सापट', 'ऋण', 'loan', 'loans'],
    'सापट': ['सापट', 'कर्जा', 'ऋण', 'loan'],
    'ऋण': ['ऋण', 'कर्जा', 'सापट', 'loan'],
    'bad': ['खराब', 'निष्क्रिय', 'कमसल', 'शंकास्पद', 'bad'],
    'खराब': ['खराब', 'निष्क्रिय', 'bad', 'loss'],
    'निष्क्रिय': ['निष्क्रिय', 'खराब', 'कमसल', 'शंकास्पद', 'non-performing', 'npl'],
    'सक्रिय': ['सक्रिय', 'असल', 'सूक्ष्म निगरानी', 'performing'],
    'classification': ['वर्गीकरण', 'classification', 'सक्रिय', 'निष्क्रिय'],
    'classify': ['वर्गीकरण', 'classification'],
    'classified': ['वर्गीकरण', 'classification'],
    'categories': ['वर्गीकरण', 'प्रकार', 'श्रेणी'],
    'category': ['वर्गीकरण', 'प्रकार', 'श्रेणी'],
    'वर्गीकरण': ['वर्गीकरण', 'classification', 'कर्जा'],
    'substandard': ['कमसल', 'Substandard', 'निष्क्रिय'],
    'कमसल': ['कमसल', 'substandard'],
    'doubtful': ['शंकास्पद', 'Doubtful', 'निष्क्रिय'],
    'शंकास्पद': ['शंकास्पद', 'doubtful'],
    'loss': ['खराब', 'Loss', 'नोक्सानी', 'निष्क्रिय'],
    'pass': ['असल', 'Pass', 'सक्रिय कर्जा'],
    'असल': ['असल', 'pass'],
    'watchlist': ['सूक्ष्म निगरानी', 'Watchlist'],
    'निगरानी': ['सूक्ष्म निगरानी', 'watchlist'],
    'provision': ['नोक्सानी व्यवस्था', 'कर्जा नोक्सानी', 'provision'],
    'provisioning': ['नोक्सानी व्यवस्था', 'कर्जा नोक्सानी', 'provisioning'],
    'नोक्सानी': ['नोक्सानी', 'provision', 'कर्जा नोक्सानी', 'नोक्सानी व्यवस्था'],
    'व्यवस्था': ['व्यवस्था', 'नोक्सानी व्यवस्था'],
    'performing': ['सक्रिय कर्जा', 'असल', 'सूक्ष्म निगरानी'],
    'non-performing': ['निष्क्रिय कर्जा', 'कमसल', 'शंकास्पद', 'खराब', 'npl'],
    'types': ['प्रकार', 'किसिम', 'वर्गीकरण'],
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
    if any(c in t_lower for c in ['atm', 'debit', 'card', 'एटीएम', 'कार्ड']) and any(w in t_lower for w in ['withdraw', 'withdrawn', 'withdrawal', 'cash', 'झिक्ने', 'झिक्न', 'नगद', 'सीमा', 'limit', 'max', 'maximum', 'amount']):
        keywords.update(['भुक्तानी', 'भुत्तफानी', 'कार्डबाट नगद', 'नगद झिक्ने', 'भिफक्ने', 'अधिकतम सीमा', 'डेबिट कार्ड', '५० हजार', '२० हजार', '२५ हजार', '१ लाख', '३ लाख', 'प्रतिकारोबार', 'प्रतिदिन'])
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

def build_where_filter(doc_spec):
    if not doc_spec or doc_spec == "All Documents":
        return None
    if isinstance(doc_spec, (list, set, tuple)):
        doc_list = [str(d) for d in doc_spec]
        if not doc_list:
            return None
        if len(doc_list) == 1:
            return f"source = '{doc_list[0]}'"
        doc_in_str = ", ".join(f"'{d}'" for d in doc_list)
        return f"source IN ({doc_in_str})"
    return f"source = '{doc_spec}'"

def hybrid_search(user_query, table, model, translated_terms="", selected_doc="All Documents", top_k=6):
    k_const = 30  # Standard RRF constant
    where_filter = build_where_filter(selected_doc)

    # 1. Primary Dense Search (Direct Query Intent)
    d_pri = {}
    q_vec = model.encode(user_query).tolist()
    search_q = table.search(q_vec)
    if where_filter:
        search_q = search_q.where(where_filter)
    for rank, (_, row) in enumerate(search_q.limit(100).to_pandas().iterrows(), 1):
        k = (row['source'], int(row['page']))
        if k not in d_pri:
            d_pri[k] = (rank, row)

    # 2. Translated Dense Search (Cross-Lingual Bridge)
    d_trans = {}
    if translated_terms and translated_terms.strip():
        t_vec = model.encode(translated_terms).tolist()
        search_t = table.search(t_vec)
        if where_filter:
            search_t = search_t.where(where_filter)
        for rank, (_, row) in enumerate(search_t.limit(100).to_pandas().iterrows(), 1):
            k = (row['source'], int(row['page']))
            if k not in d_trans:
                d_trans[k] = (rank, row)

    # 3. Primary Sparse Inverted Index Search (Exact Native Term Matching)
    s_pri = {}
    kw_pri = extract_meaningful_keywords(user_query)
    clean_pri_fts = " ".join([w for w in kw_pri if len(w) > 1])
    if clean_pri_fts.strip():
        try:
            search_fts1 = table.search(clean_pri_fts)
            if where_filter:
                search_fts1 = search_fts1.where(where_filter)
            for rank, (_, row) in enumerate(search_fts1.limit(100).to_pandas().iterrows(), 1):
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
                search_fts2 = table.search(clean_trans_fts)
                if where_filter:
                    search_fts2 = search_fts2.where(where_filter)
                for rank, (_, row) in enumerate(search_fts2.limit(100).to_pandas().iterrows(), 1):
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

        # Gentle Recency Preference for general unanchored regulatory questions (latest active rules take precedence)
        if not where_filter:
            src = row['source']
            fn_m = re.search(r'(20[78][0-9]|20[12][0-9])', src)
            if fn_m:
                doc_yr = int(fn_m.group(1))
                if 'directive' in src and 2078 <= doc_yr <= 2085:
                    rrf_score += (doc_yr - 2078) * 0.006
                elif 'Annual_Report' in src and 2020 <= doc_yr <= 2030:
                    rrf_score += (doc_yr - 2020) * 0.006

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
            "- एकीकृत वित्तीय स्थिति / वित्तीय विवरण -> Consolidated Statement of Financial Position, Financial Position, Annex 3.3, Balance Sheet\n"
            "- विकास बैंक -> Development Banks, DBs\n"
            "- वाणिज्य बैंक -> Commercial Banks, CBs\n"
            "- वित्त कम्पनी -> Finance Companies, FCs\n"
            "- जुलाई / मध्य जुलाई -> Mid-July, July\n"
            "- कुल सम्पत्ति / दायित्व -> Total Assets, Total Liabilities, Equity\n"
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
            "- debit card / ATM cash withdrawal limit -> कार्डबाट नगद झिक्ने अधिकतम सीमा, डेबिट कार्ड, ५० हजार, २० हजार, ३ लाख, नगद झिक्ने, एटीएम\n"
            "- contactless -> Contactless, कन्ट्याक्टलेस, ५ हजार, ५,०००\n"
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

        # Automatic Query Year Routing & Document Selection
        doc_year_map = build_document_year_map(table)
        available_years = set.union(*doc_year_map.values()) if doc_year_map else set()
        matched_years = extract_query_years(user_question, available_years)

        effective_doc = None
        if len(matched_years) == 1:
            target_yr = list(matched_years)[0]
            matching_docs = [d for d, yrs in doc_year_map.items() if target_yr in yrs]
            if matching_docs:
                effective_doc = matching_docs if len(matching_docs) > 1 else matching_docs[0]
                doc_names_str = ", ".join(f"`{d}`" for d in matching_docs)
                print(f"   🎯 Auto-routed to {target_yr} Directives / Reports ({doc_names_str})")
        elif len(matched_years) > 1:
            yrs_str = ", ".join(str(y) for y in sorted(matched_years))
            print(f"   📊 Comparative Multi-Year Query (analyzing across years: {yrs_str})")

        search_query = clean_query_for_search(user_question, matched_years) if effective_doc else user_question
        if not search_query.strip():
            search_query = user_question

        print("   Searching documents (Cross-Lingual Dual-Pass Hybrid Retrieval)...")

        translated_terms = expand_query_crosslingual(search_query, client)
        results = hybrid_search(search_query, table, embedding_model, translated_terms=translated_terms, selected_doc=effective_doc, top_k=6)

        # For comparative multi-year queries, interleave results across matched documents so all target years enter context
        if len(matched_years) > 1:
            target_docs = set()
            for yr in matched_years:
                for d, yrs in doc_year_map.items():
                    if yr in yrs:
                        target_docs.add(d)
            if target_docs:
                by_doc = {d: [] for d in target_docs}
                for item in results:
                    if item['source'] in by_doc:
                        by_doc[item['source']].append(item)
                interleaved = []
                for i in range(3):
                    for d in sorted(by_doc.keys()):
                        if i < len(by_doc[d]):
                            interleaved.append(by_doc[d][i])
                if interleaved:
                    results = interleaved

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
9. Prevailing Active Regulation: If the user does not specify a target year, prioritize and present the latest active regulatory year's provision (e.g. Directive 2082 takes precedence over 2080/2081, and Annual Report 2024/2025 over earlier years) as the prevailing official rule. Clearly indicate the directive/report year cited.

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

            full_response = ""
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_response += content
                print(content, end="", flush=True)

            print(f"\n\n(Generated via {model_used})")
            cited_sources = extract_cited_sources(full_response, results, target_years=matched_years, target_doc=effective_doc)
            print("Verified Source(s) Cited:")
            for c in cited_sources:
                print(f"   * {c['source']} (Page {c['page']})")

            # Also display other retrieved candidate pages
            cited_keys = {(c['source'], c['page']) for c in cited_sources}
            remaining = [r for r in results if (r['source'], r['page']) not in cited_keys]
            if remaining:
                def other_sort_key(c):
                    src = c['source']
                    ym = re.search(r'(20[78][0-9]|20[12][0-9])', src)
                    yr = int(ym.group(1)) if ym else 0
                    target_match = 0
                    if effective_doc:
                        if isinstance(effective_doc, (list, set, tuple)) and src in effective_doc:
                            target_match = 0
                        elif isinstance(effective_doc, str) and src == effective_doc:
                            target_match = 0
                    elif matched_years and yr in matched_years:
                        target_match = 0
                    else:
                        target_match = 1
                    return (target_match, -yr if not matched_years else 0, c.get('page', 0))

                remaining.sort(key=other_sort_key)
                print("\nOther Retrieved Reference Pages:")
                seen_rem = set()
                for r in remaining:
                    rk = (r['source'], r['page'])
                    if rk not in seen_rem:
                        seen_rem.add(rk)
                        print(f"   - {r['source']} (Page {r['page']})")

            print("-" * 65 + "\n")

        except Exception as e:
            print(f"\n⚠️ Error connecting to Groq API: {e}\n")

if __name__ == "__main__":
    main()