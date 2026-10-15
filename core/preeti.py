"""
Preeti font mapping and legacy text normalization utilities.
"""

import re

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

def decode_preeti_text(text: str) -> str:
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

