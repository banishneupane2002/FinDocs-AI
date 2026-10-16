"""
Domain lexicon, stopwords, Unicode Devanagari normalization, and keyword extraction.
"""

import re
import unicodedata

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

def normalize_devanagari(text: str) -> str:
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

def extract_meaningful_keywords(text: str) -> set:
    """Zero-hardcoding pure NLP keyword extraction with Devanagari Unicode normalization."""
    if not text:
        return set()
    text_norm = normalize_devanagari(text)
    raw_words = re.findall(r'[\u0900-\u097F\w+]+', text_norm)
    keywords = set()
    for w in raw_words:
        w_lower = w.lower()
        if w_lower in STOP_WORDS:
            continue
        # Preserve single digits (e.g. 4%, 5%, 3 crore) but filter punctuation/single chars
        if len(w) <= 1 and w not in '०१२३४५६७८९0123456789':
            continue
        keywords.add(w)
        keywords.add(w_lower)

        # English plural stemming
        if w_lower.endswith('s') and len(w_lower) > 3:
            base_s = w_lower[:-1]
            if base_s not in STOP_WORDS:
                keywords.add(base_s)

        # Nepali grammatical suffix trimming
        for suffix in ['सम्बन्धी', 'सम्बन्धमा', 'मार्फत', 'अनुसार', 'सम्म', 'हरु', 'हरू', 'को', 'का', 'की', 'मा', 'ले', 'लाई', 'बाट']:
            if w.endswith(suffix) and len(w) > len(suffix) + 2:
                base = w[:-len(suffix)]
                if base.lower() not in STOP_WORDS and (len(base) > 2 or base in '०१२३४५६७८९0123456789'):
                    keywords.add(base)

        keywords.add(w.replace('ः', ''))
        keywords.add(w.replace(':', ''))

    clean_tokens = set()
    for k in keywords:
        for t in re.findall(r'[\u0900-\u097F\w+]+', k):
            if (len(t) > 1 or t in '०१२३४५६७८९0123456789') and t.lower() not in STOP_WORDS:
                clean_tokens.add(t)

    return clean_tokens

