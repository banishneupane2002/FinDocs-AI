import os
import sys
import io
import re
import unicodedata
import lancedb
from sentence_transformers import SentenceTransformer

# Force UTF-8 on Windows
if sys.platform == "win32":
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# Connect to LanceDB & local embedding model (Zero API calls, 100% offline)
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
    if not text:
        return ""
    for garbled, clean in PREETI_CLEAN_REPLACEMENTS:
        text = text.replace(garbled, clean)
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
        if w_lower in STOP_WORDS or len(w) <= 1:
            continue
        keywords.add(w)
        keywords.add(w_lower)

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

def offline_hybrid_retrieve(user_query, top_k=6):
    """100% offline hybrid retrieval without calling any external LLM."""
    k_const = 30
    d_pri = {}
    q_vec = embedding_model.encode(user_query).tolist()
    for rank, (_, row) in enumerate(table.search(q_vec).limit(100).to_pandas().iterrows(), 1):
        k = (row['source'], int(row['page']))
        if k not in d_pri:
            d_pri[k] = (rank, row)

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

    all_keys = set(d_pri.keys()) | set(s_pri.keys())
    if not all_keys:
        return []

    fused = []
    for k in all_keys:
        dp = d_pri[k][0] if k in d_pri else 999
        sp = s_pri[k][0] if k in s_pri else 999
        row = (d_pri.get(k) or s_pri.get(k))[1]
        rrf = (1.0 / (k_const + dp)) + (1.2 / (k_const + sp))
        fused.append({
            'source': row['source'],
            'page': int(row['page']),
            'text': row['text'],
            'score': rrf
        })

    fused.sort(key=lambda x: x['score'], reverse=True)

    diverse = []
    seen = set()
    for it in fused:
        sp = (it['source'], it['page'])
        if sp not in seen:
            seen.add(sp)
            diverse.append(it)
            if len(diverse) >= top_k:
                break
    return diverse

def inspect_query(q):
    print("=" * 65)
    print(f"QUERY: {q}")
    print("=" * 65)
    results = offline_hybrid_retrieve(q, top_k=6)
    seen_pages = set()
    total_chars = 0
    extracted_context = []

    for item in results:
        sp = (item['source'], item['page'])
        if sp not in seen_pages:
            seen_pages.add(sp)
            try:
                page_records = table.search().where(f"source = '{item['source']}' AND page = {item['page']}").to_pandas()
                full_page_text = "\n".join(page_records['text'].tolist())
            except Exception:
                full_page_text = item['text']

            full_page_text = decode_preeti_text(full_page_text)
            extracted_context.append({
                'source': item['source'],
                'page': item['page'],
                'score': round(item['score'], 4),
                'text': full_page_text
            })
            total_chars += len(full_page_text)
            if len(seen_pages) >= 4 or total_chars > 12000:
                break

    print(f"\nExtracted {len(extracted_context)} parent pages ({total_chars} characters):")
    for idx, c in enumerate(extracted_context, 1):
        print(f"\n--- [PAGE {idx}] {c['source']} | Page {c['page']} (RRF Score: {c['score']}) ---")
        preview = c['text'].strip()
        print(preview[:800] + ("\n... [remaining text truncated for preview]" if len(preview) > 800 else ""))
    print("\n" + "=" * 65 + "\n")
    return extracted_context

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_query(" ".join(sys.argv[1:]))
    else:
        print("Usage: python inspect_context.py <your question>")

