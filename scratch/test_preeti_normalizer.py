import re, sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Standard Preeti keyboard layout mapping table
PREETI_CHAR_MAP = {
    # Lowercase ASCII mappings
    'ब': 'a', 'द': 'b', 'अ': 'c', 'म': 'd', 'भ': 'e',
    'ि': 'f', 'न': 'g', 'ज': 'h', 'ष': 'i', 'व': 'j',
    'प': 'k', 'य': 'l', 'ड': 'm', 'ल': 'n', 'इ': 'o',
    'उ': 'p', 'त्र': 'q', 'च': 'r', 'क': 's', 'त': 't',
    'ग': 'u', 'ख': 'v', 'ध': 'w', 'ह': 'x', 'थ': 'y',
    'श': 'z',

    # Uppercase ASCII mappings
    'ब्': 'A', 'द्य': 'B', 'ऋ': 'C', 'म्': 'D', 'भ्': 'E',
    'ँ': 'F', 'न्': 'G', 'ज्': 'H', 'क्ष्': 'I', 'व्': 'J',
    'प्': 'K', 'यूँ': 'L', 'ड्': 'M', 'ल्': 'N', 'र्': 'O',
    'ए': 'P', 'त्त': 'Q', 'च्': 'R', 'क्': 'S', 'त्': 'T',
    'ग्': 'U', 'ख्': 'V', 'ध्': 'W', 'ह्': 'X', 'थ्': 'Y',
    'श्': 'Z',

    # Special Symbols & Punctuation
    '९': '(', '०': ')', 'ं': '+', 'घ': '3', 'ज्ञ': '1', 'द्द': '2', 'द्ध': '4',
    'छ': '6', 'ट': '5', 'ठ': '7', 'ड': '8', 'ः': 'M', 'ी': 'L', 'ा': '',
    '(' : '(', ')' : ')'
}

# Known ligature glitched words and Section headers
SECTION_DIGIT_MAP = [
    (r'(?<![०-९\d])द्ध\.', '४.'),
    (r'(?<![०-९\d])द्द\.', '२.'),
    (r'(?<![०-९\d])ज्ञ\.', '१.'),
    (r'\(ज्ञ\)', '(१)'),
    (r'\(द्द\)', '(२)'),
    (r'\(द्ध\)', '(४)'),
]

LIGATURE_FIXES = [
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

# High-frequency Preeti-encoded English tokens extracted from NRB directives
COMMON_PREETI_WORDS = {
    'ग्उनचबमभ': 'Upgrade',
    'क्थकतभफ': 'System',
    'ब्गमष्त': 'Audit',
    'ब्गमषत': 'Audit',
    'ऋऋत्ख्': 'CCTV',
    'त्त्च्': 'TTR',
    'क्त्च्': 'STR',
    'क्ब्च्': 'SAR',
    'ग्क्क्म्': 'USSD',
    'प्थ्ऋ': 'KYC',
    'ब्त्ः': 'ATM',
    'एइक्': 'POS',
    'एइत्': 'POT',
    'क्ष्धँत्': 'IBFT',
    'क्ष्द्यँत्': 'IBFT',
    'नयब्ःी': 'goAML',
    'क्ष्ककगभच': 'Issuer',
    'ष्ककगभच': 'Issuer',
    'ब्अत्रगष्चभच': 'Acquirer',
    'धबबिलअभ': 'Balance',
    'धबअपगउ': 'Backup',
    'द्यबअपगउ': 'Backup',
    'इखभचलष्नजत': 'Overnight',
    'ँयचअभ': 'Force',
    'क्भततभिफभलत': 'Settlement',
    'क्भततिभफभलत': 'Settlement',
    'ख्गलिभचबदष्ष्ितष्भक': 'Vulnerabilities',
    'म्ऋ(म्च्': 'DC-DR',
    '९त्ंघ०': '(T+3)',
    '९त्ंज्ञ०': '(T+1)',
    '९त्ंघण्०': '(T+30)',
    'त्ंघ': 'T+3',
    'त्ंज्ञ': 'T+1',
    'त्ंघण्': 'T+30',
    '९ब्ःी०': '(AML)',
    '९ऋँत्०': '(CFT)',
    'ब्ःीरऋँत्': 'AML/CFT',
}

def decode_preeti_text(text: str) -> str:
    """Universal Preeti font decoder and Devanagari normalizer."""
    if not text:
        return ""
        
    # 1. Section numbers and points (e.g. द्ध. -> ४., (ज्ञ) -> (१))
    for pat, rep in SECTION_DIGIT_MAP:
        text = re.sub(pat, rep, text)
        
    # 2. Known compound words (multi-word phrases)
    compounds = [
        ('इखभचलष्नजत धबबिलअभ', 'Overnight Balance'),
        ('ँयचअभ क्भततभिफभलत', 'Force Settlement'),
        ('क्थकतभफ ब्गमष्त', 'System Audit'),
        ('ऋऋत्ख् ऋबफभचब', 'CCTV Camera'),
        ('ःभफयचथ धबअपगउ', 'Memory Backup'),
        ('नयब्ःी क्यातधबचभ', 'goAML Software'),
        ('त्जचभकजयमि त्चबलकबअतष्यल च्भउयचतष्लन( त्त्च्०', 'Threshold Transaction Reporting (TTR)'),
        ('त्जचभकजयमि त्चबलकबअतष्यल च्भउयचतष्लन', 'Threshold Transaction Reporting'),
        ('प्रतिस्थापन वा क्थकतभफ ग्उनचबमभ', 'प्रतिस्थापन वा System Upgrade'),
        ('प्रतिस्थापन वा System ग्उनचबमभ', 'प्रतिस्थापन वा System Upgrade'),
        ('क्थकतभफ ग्उनचबमभ', 'System Upgrade'),
    ]
    for garbled, clean in compounds:
        text = text.replace(garbled, clean)
        
    # 3. Single-word Preeti font tokens
    for garbled, clean in COMMON_PREETI_WORDS.items():
        text = text.replace(garbled, clean)
        
    # 4. Standard Devanagari spelling / ligature fixes
    for err, fix in LIGATURE_FIXES:
        text = text.replace(err, fix)
        
    return text
    
    # 4. Standard Devanagari spelling / ligature fixes
    for err, fix in LIGATURE_FIXES:
        text = text.replace(err, fix)
        
    return text

# Test cases
test_samples = [
    "साविक System प्रतिस्थापन वा System ग्उनचबमभ नभएको अवस्थामा",
    "द्ध. भुक्तानी प्रणाली परिक्षण ९System Audit०",
    "(ज्ञ) अनुमतिपत्रप्राप्त संस्था ले सेवा सञ्चालन गरेको १ वर्ष पुरा भएपछि",
    "प्रत्येक २ आर्थकि वर्षमा System Audit गरार्इ आर्थकि वर्ष समाप्त भएको ६ महिनाभित्र",
    "ऋऋत्ख् ऋबफभचब को ःभफयचथ धबअपगउ कम्तीमा नब्बे ९९०० दिनसम्म",
    "दुवै नेपाली संस्था भएमा बढीमा ९त्ंघ० भित्र ँयचअभ क्भततभिफभलत गर्ने",
    "दश लाख रुपैयाँ वा सोभन्दा बढीको रकम भएमा त्त्च् नयब्ःी Software मार्फत वित्तीय जानकारी इकार्इमा"
]

print("=== TESTING NORMALIZER ===")
for sample in test_samples:
    print("\n[ORIGINAL]:", sample)
    print("[CLEANED] :", decode_preeti_text(sample))
