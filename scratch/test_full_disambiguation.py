import re

SPECIFIC_ANCHORS = [
    # Metrics, ratios, and limits
    r'\bltv\b', r'loan\s*to\s*value', r'एलटीभी', r'धितो\s*अनुपात',
    r'\bcrr\b', r'cash\s*reserve', r'अनिवार्य\s*नगद',
    r'\bslr\b', r'statutory\s*liquidity', r'वैधानिक\s*तरलता',
    r'\bturnover\b', r'वार्षिक\s*कारोबार', r'[०-९0-9]+\s*(?:करोड|लाख|हजार|crore|lakh|million)',
    r'kathmandu\s*valley', r'काठमाडौ[ंँ]?\s*उपत्यका',
    r'residential\s*home\s*loan', r'आवासीय\s*घर\s*कर्जा',
    r'first\s*home\s*buyer', r'पहिलो\s*घर',
    r'earthquake', r'भूकम्प',
    r'working\s*capital', r'चालू\s*पुँजी',
    r'non-banking\s*asset', r'\bnba\b.*?(?:बिक्री|वर्ष|limit|sale)', r'गैर-?बैंकिङ\s*सम्पत्ति',
    r'letter\s*of\s*credit', r'\blc\b', r'प्रतितपत्र', r'trust\s*receipt', r'ट्रष्ट\s*रिसिप्ट',
    r'cooling\s*period', r'कुलिङ\s*पिरियड', r'कालोसूची\s*(?:समय|अवधि|फुकुवा|criteria)',
    r'debit\s*card', r'डेबिट\s*कार्ड', r'atms?', r'एटीएम',
    r'base\s*rate', r'आधार\s*दर', r'spread\s*rate', r'स्प्रेड\s*दर',
    r'stress\s*test', r'तनाव\s*परीक्षण', r'prompt\s*corrective', r'शीघ्र\s*सुधारात्मक',
    # Specific compliance, multi-directive, and ratio anchors
    r'bad\s*loans?', r'खराब\s*कर्जा',
    r'\bnpl\b', r'\bnpa\b', r'non-?performing', r'निष्क्रि?य\s*कर्जा',
    r'substandard', r'कमसल',
    r'doubtful', r'शंकास्पद',
    r'pass\s*loans?', r'असल\s*कर्जा',
    r'loan\s*classification', r'कर्जा\s*वर्गीकरण',
    r'categories\s*of\s*(?:bad\s*)?loans?',
    r'loan\s*loss\s*provision(?:ing)?', r'कर्जा\s*नोक्सानी\s*व्यवस्था', r'नोक्सानी\s*व्यवस्था',
    r'restructur(?:ing|ed)', r'पुनर्संरचना',
    r'reschedul(?:ing|ed)', r'पुनर्तालिकीकरण',
    r'single\s*obligor', r'\bsol\b', r'एकल\s*ग्राहक',
    r'penal\s*interest', r'पेनाल\s*ब्याज', r'हर्जाना\s*ब्याज', r'हर्जाना\s*दर', r'fund\s*diversion', r'दुरुपयोग',
    r'microfinance', r'लघुवित्त', r'विपन्न\s*वर्ग', r"['\"]?d['\"]?\s*class", r'घ\s*वर्ग',
    r'tier\s*[12]', r'प्राथमिक\s*पुँजी', r'पूरक\s*पुँजी', r'supplementary\s*capital', r'core\s*capital',
    r'watchlist', r'सूक्ष्म\s*निगरानी',
    r'ceo', r'प्रमुख\s*कार्यकारी', r'fixed\s*deposit', r'मुद्दती\s*(?:रसिद|निक्षेप)', r'premature',
    r'audit', r'लेखापरीक्ष[ाण]', r'lock-?in', r'लकइन', r'promoter', r'संस्थापक',
    r'counterfeit', r'जाली\s*नोट', r'खोटा', r'security\s*guard', r'काउन्टर',
    r'liquidity\s*facility', r'olf', r'slf', r'अन्तरबैंक', r'तरलता\s*सुविधा',
    r'prepayment', r'अग्रिम\s*भुक्तानी', r'consortium', r'सह-?वित्तीयकरण',
    r'independent\s*director', r'स्वतन्त्र\s*सञ्चालक', r'tenure', r'कार्यकाल',
    r'compliance\s*officer', r'कम्प्लायन्स', r'qualification', r'योग्यता',
    r'margin\s*lending', r'सेयर\s*धितो', r'loan\s*against\s*shares?',
    # Specific Directive numbers and explicit category anchors
    r'निर्देशन\s*नं\.?\s*[०-९0-9]+', r'\bdirective\s*[०-९0-9]+\b',
    r'एकीकृत\s*निर्देशन', r'unified\s*directive',
    r'भुक्तानी\s*(?:प्रणाली)?\s*निर्देशन', r'payment\s*directive',
    r'सुपरीवेक्षण\s*प्रतिवेदन', r'supervision\s*report',
    # Specific Calendar Dates (Bikram Sambat & Gregorian)
    r'\b(?:20[5-9][0-9]|२०[५-९][०-९])[/-](?:[0-9]{1,2}|[०-९]{1,2})[/-](?:[0-9]{1,2}|[०-९]{1,2})\b',
    r'\b(?:20[5-9][0-9]|२०[५-९][०-९])\s+(?:बैशाख|वैशाख|जेठ|ज्येष्ठ|असार|आषाढ|साउन|श्रावण|भदौ|भाद्र|असोज|आश्विन|कात्तिक|कार्तिक|मंसिर|मङ्सिर|पुस|पौष|माघ|फागुन|फाल्गुन|चैत|चैत्र|baisakh|jestha|jeth|ashad|shrawan|bhadra|asoj|kartik|mangsir|poush|magh|falgun|chaitra)\s+(?:[0-9]{1,2}|[०-९]{1,2})\b'
]

REGULATORY_MODIFIERS = {
    # Question / Intent words
    'what', 'how', 'when', 'where', 'why', 'which', 'who', 'can', 'is', 'are', 'does', 'should',
    'कति', 'के', 'कहिले', 'कसरी', 'किन', 'कुन', 'कसले', 'सकिन्छ', 'पाइन्छ', 'हुनुपर्छ', 'गर्नुपर्छ', 'हुन्छ',
    
    # Specific regulatory attributes & parameters
    'category', 'categories', 'classification', 'limit', 'limits', 'rate', 'rates', 'ratio', 'ratios',
    'timeframe', 'period', 'lock-in', 'audit', 'qualification', 'tenure', 'appointment', 'frequency',
    'criteria', 'procedure', 'penalty', 'guideline', 'guidelines', 'requirement', 'requirements',
    'facility', 'charge', 'charges', 'margin', 'counterfeit', 'security', 'target', 'formula',
    'ceiling', 'floor', 'rule', 'rules', 'percent', 'percentage', 'cooling', 'provision', 'provisioning',
    'mandate', 'process', 'deadline', 'concession', 'exemption', 'spread', 'tenor',
    
    # Nepali regulatory attributes & parameters
    'प्रकार', 'वर्गीकरण', 'सीमा', 'दर', 'अनुपात', 'समयसीमा', 'म्याद', 'अवधि', 'लकइन',
    'लेखापरीक्षण', 'योग्यता', 'कार्यकाल', 'नियुक्ति', 'पटक', 'मापदण्ड', 'प्रक्रिया', 'जरिवाना',
    'हर्जाना', 'सर्त', 'सुविधा', 'मार्जिन', 'धितो', 'सुरक्षा', 'लक्ष्य', 'फाराम',
    'कागजात', 'छुट', 'पुनर्संरचना', 'पुनर्तालिकीकरण', 'अपलेखन', 'फुकुवा', 'भत्ता'
}

POLYSEMOUS_CROSS_DIRECTIVE_PATTERNS = [
    r'^(?:fee|fees|charge|charges|service\s*charges?|शुल्क|सेवा\s*शुल्क|दस्तुर)(?:\s*\?*)?$',
    r'^(?:interest\s*rates?|rate|rates|ब्याज|ब्याजदर)(?:\s*\?*)?$',
    r'^(?:blacklists?|blacklisting|कालोसूची)(?:\s*\?*)?$',
    r'^(?:penalt(?:y|ies)|fines?|हर्जाना|जरिवाना|पेनाल्टी)(?:\s*\?*)?$',
    r'^(?:report(?:ing|s)?|returns?|प्रतिवेदन|तथ्याङ्क|विवरण\s*पेश)(?:\s*\?*)?$',
    r'^(?:directives?|circulars?|guidelines?|निर्देशन|परिपत्र|मार्गदर्शन)(?:\s*\?*)?$'
]

UNCLEAR_QUERY_PATTERNS = [
    r'^(?:hi|hello|hey|namaste|नमस्ते|नमस्कार|प्रणाम)(?:\s|$|[?,.!])',
    r'^(?:what|tell me|explain|how|why|can you|कस्तो|के|किन|कसरी|भन्नुस्|जानकारी)\s*[\?\.]*$',
    r'^(?:rule|rules|guideline|guidelines|policy|policies|limit|limits|provision|provisions|नियम|नीति|निर्देशन|व्यवस्था|सीमा)\s*[\?\.]*$'
]

BROAD_TOPICS = {
    "kyc": {
        "pattern": r'^(?:kyc|cdd|केवाईसी|ग्राहक\s*पहिचान|kyc\s*(?:rules?|guidelines?|information)|ग्राहक\s*पहिचान\s*(?:सम्बन्धी|बारेमा|व्यवस्था))(?:\s*\?*)?$',
        "title": "ग्राहक पहिचान (KYC / Customer Due Diligence)",
        "message": "नेपाल राष्ट्र बैंकको निर्देशनमा **KYC (ग्राहक पहिचान)** सम्बन्धी व्यवस्था विभिन्न क्षेत्रमा फैलिएको छ।",
        "options": []
    },
    "loan": {
        "pattern": r'^(?:loan|loans|credit|credits|कर्जा|सापट|ऋण|loans?\s*(?:rules?|policy|information)|कर्जा\s*(?:सम्बन्धी|बारेमा|व्यवस्था|नियम))(?:\s*\?*)?$',
        "title": "कर्जा तथा सापट सम्बन्धी व्यवस्था (Loans & Advances)",
        "message": "नेपाल राष्ट्र बैंकको **कर्जा (Loan)** सम्बन्धी निर्देशनहरू विभिन्न शीर्षकमा विभाजित छन्।",
        "options": []
    }
}

def is_specific_query(query: str) -> bool:
    clean_q = query.strip()
    q_lower = clean_q.lower()
    for pat in SPECIFIC_ANCHORS:
        if re.search(pat, q_lower, re.IGNORECASE):
            return True
    tokens = set(re.findall(r'[\w\u0900-\u097F]+', q_lower))
    if (tokens & REGULATORY_MODIFIERS) and len(tokens) >= 2:
        return True
    words = clean_q.split()
    if len(words) >= 4 and not any(re.search(pat, clean_q, re.IGNORECASE) for pat in UNCLEAR_QUERY_PATTERNS):
        return True
    return False

def is_polysemous_cross_category(query: str) -> bool:
    clean_q = query.strip()
    return any(re.search(pat, clean_q, re.IGNORECASE) for pat in POLYSEMOUS_CROSS_DIRECTIVE_PATTERNS)

def detect_query_disambiguation_new(query: str, retrieved_chunks: list, selected_cat: str = "all") -> tuple[bool, dict | None]:
    clean_q = query.strip()
    words = clean_q.split()

    # Step 1: Specificity Fast-Track (Never block clear, well-formed queries)
    if is_specific_query(clean_q):
        return False, None

    # Step 2: Low-Confidence / Unclear Question Check
    is_unclear = any(re.search(pat, clean_q, re.IGNORECASE) for pat in UNCLEAR_QUERY_PATTERNS)
    if not retrieved_chunks or len(clean_q) < 3 or is_unclear:
        return True, {"type": "suggestion", "title": "Unclear Query"}

    # Step 3A: Known Broad Topic patterns (e.g. user types just 'kyc' or 'loan')
    q_lower = clean_q.lower()
    for topic_key, topic_data in BROAD_TOPICS.items():
        if re.search(topic_data["pattern"], q_lower) and len(words) <= 4:
            return True, {"type": "broad_topic", "title": topic_data["title"]}

    # Step 3B: Smart Direct Options (Cross-Category & Multi-Chapter Unified in 1 Click)
    # Strictly restricted to recognized polysemous keywords or bare <= 2 word terms
    is_poly = is_polysemous_cross_category(clean_q)
    if selected_cat == "all" and retrieved_chunks and (is_poly or len(words) <= 2):
        return True, {"type": "cross_category", "title": "Cross Category"}

    # Step 4: Intra-Document Chapter Disambiguation (Single Document / Category multi-chapter match)
    # Strictly restricted to recognized polysemous keywords or bare <= 2 word terms
    if (is_poly or len(words) <= 2):
        return True, {"type": "intra_chapter", "title": "Intra Chapter"}

    return False, None

mock_chunks = [
    {'source': 'Unified_directive_2081.pdf', 'text': 'निर्देशन नं. २ कर्जा वर्गीकरण तथा नोक्सानी व्यवस्था खराब कर्जा'},
    {'source': 'Unified_directive_2081.pdf', 'text': 'निर्देशन नं. ३ एकल ग्राहक कर्जा सीमा'},
    {'source': 'payment_directive_2081.pdf', 'text': 'भुक्तानी प्रणाली निर्देशन कार्ड तथा वालेट शुल्क'},
    {'source': 'Annual_Report_2025.pdf', 'text': 'वार्षिक प्रतिवेदन वित्तीय विवरण'}
]

queries = [
    ('categories of bad loan', False),
    ('statutory audit timeframe', False),
    ('promoter share lock-in period', False),
    ('cash counter security guidelines', False),
    ('overnight liquidity facility rules', False),
    ('prepayment charge on term loan', False),
    ('consortium financing lead bank role', False),
    ('tenure of independent director', False),
    ('qualification of compliance officer', False),
    ('what is crr requirement', False),
    ('counterfeit currency reporting procedure', False),
    ('working capital loan guidelines', False),
    ('penalty for delayed reporting', False),
    ('maximum loan against shares', False),
    ('interest spread rate formula', False),
    ('audit committee meeting frequency', False),
    ('npl write off criteria', False),
    ('cooling period for ceo', False),
    ('margin lending limit best finance', False),
    ('लेखापरीक्षण गर्ने म्याद', False),
    ('संस्थापक सेयर लकइन अवधि', False),
    ('नगद काउन्टर सुरक्षा मापदण्ड', False),
    ('स्वतन्त्र सञ्चालकको कार्यकाल', False),
    ('कम्प्लायन्स अधिकृतको योग्यता', False),
    ('जाली नोट भेटिएमा के गर्ने', False),
    ('विवरण बुझाउन ढिलाइ भएमा जरिवाना', False),
    ('सेयर धितो कर्जाको अधिकतम सीमा', False),
    ('लेखापरीक्षण समिति बैठक कति समयमा बस्नुपर्छ', False),
    ('सञ्चालकको बैठक भत्ता', False),
    ('सिइओको कुलिङ पिरियड', False),
    # Broad/ambiguous queries that SHOULD return True
    ('loan', True),
    ('kyc', True),
    ('fee', True),
    ('शुल्क', True),
    ('ब्याजदर', True),
    ('कालोसूची', True),
    ('हर्जाना', True),
    ('reporting', True),
    ('hi', True)
]

all_pass = True
for q, should_disambig in queries:
    is_ambig, data = detect_query_disambiguation_new(q, mock_chunks)
    dtype = data["type"] if data else "None"
    if is_ambig != should_disambig:
        print(f"FAILED: {q:42} -> got is_ambig={is_ambig} ({dtype}), expected {should_disambig}")
        all_pass = False
    else:
        status = f"DISAMBIG ({dtype})" if is_ambig else "DIRECT ANSWER"
        print(f"OK: {q:42} -> {status}")

if all_pass:
    print("\nALL 39 TESTS PASSED PERFECTLY!")
