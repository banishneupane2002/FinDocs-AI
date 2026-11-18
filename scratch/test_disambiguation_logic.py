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

queries = [
    ('categories of bad loan', 'DIRECT'),
    ('statutory audit timeframe', 'DIRECT'),
    ('promoter share lock-in period', 'DIRECT'),
    ('cash counter security guidelines', 'DIRECT'),
    ('overnight liquidity facility rules', 'DIRECT'),
    ('prepayment charge on term loan', 'DIRECT'),
    ('consortium financing lead bank role', 'DIRECT'),
    ('tenure of independent director', 'DIRECT'),
    ('qualification of compliance officer', 'DIRECT'),
    ('what is crr requirement', 'DIRECT'),
    ('counterfeit currency reporting procedure', 'DIRECT'),
    ('working capital loan guidelines', 'DIRECT'),
    ('penalty for delayed reporting', 'DIRECT'),
    ('maximum loan against shares', 'DIRECT'),
    ('interest spread rate formula', 'DIRECT'),
    ('audit committee meeting frequency', 'DIRECT'),
    ('npl write off criteria', 'DIRECT'),
    ('cooling period for ceo', 'DIRECT'),
    ('margin lending limit best finance', 'DIRECT'),
    ('लेखापरीक्षण गर्ने म्याद', 'DIRECT'),
    ('संस्थापक सेयर लकइन अवधि', 'DIRECT'),
    ('नगद काउन्टर सुरक्षा मापदण्ड', 'DIRECT'),
    ('स्वतन्त्र सञ्चालकको कार्यकाल', 'DIRECT'),
    ('कम्प्लायन्स अधिकृतको योग्यता', 'DIRECT'),
    ('जाली नोट भेटिएमा के गर्ने', 'DIRECT'),
    ('विवरण बुझाउन ढिलाइ भएमा जरिवाना', 'DIRECT'),
    ('सेयर धितो कर्जाको अधिकतम सीमा', 'DIRECT'),
    ('लेखापरीक्षण समिति बैठक कति समयमा बस्नुपर्छ', 'DIRECT'),
    ('सञ्चालकको बैठक भत्ता', 'DIRECT'),
    ('सिइओको कुलिङ पिरियड', 'DIRECT'),
    # Ambiguous / Broad queries that MUST trigger cards
    ('loan', 'BROAD_TOPIC'),
    ('kyc', 'BROAD_TOPIC'),
    ('fee', 'POLYSEMOUS'),
    ('शुल्क', 'POLYSEMOUS'),
    ('ब्याजदर', 'POLYSEMOUS'),
    ('कालोसूची', 'POLYSEMOUS'),
    ('हर्जाना', 'POLYSEMOUS'),
    ('reporting', 'POLYSEMOUS'),
    ('hi', 'UNCLEAR')
]

passed = 0
for q, expected in queries:
    is_spec = is_specific_query(q)
    is_unc = any(re.search(pat, q.strip(), re.IGNORECASE) for pat in UNCLEAR_QUERY_PATTERNS)
    is_poly = is_polysemous_cross_category(q)
    
    actual = 'DIRECT' if is_spec else ('UNCLEAR' if is_unc else ('POLYSEMOUS' if is_poly else 'BROAD_TOPIC'))
    ok = (actual == expected) or (expected == 'BROAD_TOPIC' and actual in ('BROAD_TOPIC', 'POLYSEMOUS'))
    if ok:
        passed += 1
        print(f"PASS: {q:42} -> {actual}")
    else:
        print(f"FAIL: {q:42} -> got {actual}, expected {expected}")

print(f"\nTest Passed: {passed}/{len(queries)} ({passed/len(queries)*100:.1f}%)")
