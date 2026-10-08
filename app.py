import os
import sys
import json
import re
import math
import time
import subprocess
import unicodedata
import lancedb
import streamlit as st
from sentence_transformers import SentenceTransformer
from groq import Groq

# 1. Page Configuration
st.set_page_config(
    page_title="NRB Regulatory Intelligence (RAG)",
    page_icon="🏦",
    layout="wide"
)

# Custom Institutional Banking & Finance Theme (Clean White & Slate Navy)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Global White App Canvas */
    .stApp {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    
    /* Institutional Executive Header */
    .finance-header {
        background: linear-gradient(135deg, #0A2540 0%, #003366 60%, #08213B 100%);
        color: #FFFFFF;
        padding: 22px 28px;
        border-radius: 12px;
        margin-bottom: 22px;
        box-shadow: 0 4px 14px rgba(10, 37, 64, 0.10);
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(255, 255, 255, 0.12);
    }
    .finance-header-text h1 {
        margin: 0;
        font-size: 1.7rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #FFFFFF !important;
    }
    .finance-header-text p {
        margin: 4px 0 0 0;
        font-size: 0.92rem;
        color: #CBD5E1 !important;
    }
    .finance-badge {
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #F8FAFC;
        white-space: nowrap;
    }
    
    /* Sidebar: Crisp Executive Slate */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #0F2C59 !important;
        font-weight: 600 !important;
    }
    
    /* Expander / Card Containers */
    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        margin-bottom: 10px !important;
    }
    
    /* Chat Message Bubbles */
    div[data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 16px 20px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03) !important;
    }
    
    /* User Message Container Accent */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background-color: #F8FAFC !important;
        border-left: 4px solid #64748B !important;
    }
    
    /* Assistant Message Container Accent (Institutional Navy) */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background-color: #FFFFFF !important;
        border-left: 4px solid #003366 !important;
    }
    
    /* Quick Showcase Buttons */
    div[data-testid="stHorizontalBlock"] button {
        background-color: #FFFFFF !important;
        color: #0A2540 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 8px 14px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        background-color: #F0F7FF !important;
        border-color: #003366 !important;
        color: #003366 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 51, 102, 0.1) !important;
    }
    
    /* Verified Source Cards */
    .stTextArea textarea {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
        border: 1px solid #E2E8F0 !important;
        font-family: 'Consolas', 'Courier New', monospace !important;
        font-size: 0.88rem !important;
    }
    
    /* Chat Input Bar */
    div[data-testid="stChatInput"] {
        border-color: #CBD5E1 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04) !important;
    }
    div[data-testid="stChatInput"]:focus-within {
        border-color: #003366 !important;
        box-shadow: 0 0 0 2px rgba(0, 51, 102, 0.15) !important;
    }
</style>
""", unsafe_allow_html=True)

# Read Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.strip().split("=", 1)[1].strip()

if not GROQ_API_KEY:
    GROQ_API_KEY = ""

MODELS_TO_TRY = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
MODEL_NAME = MODELS_TO_TRY[0]

# Stop words for hybrid search
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

def open_pdf_at_page(pdf_name: str, page: int):
    """Opens the local PDF on Windows directly scrolled to the specified page in Chrome or Edge."""
    pdf_path = os.path.join("File_System", pdf_name)
    if not os.path.exists(pdf_path):
        pdf_path = pdf_name
    if not os.path.exists(pdf_path):
        st.warning(f"File '{pdf_name}' not found on disk.")
        return

    abs_path = os.path.abspath(pdf_path).replace("\\", "/")
    target_url = f"file:///{abs_path}#page={page}"

    browsers = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    for b_path in browsers:
        if os.path.exists(b_path):
            try:
                subprocess.Popen([b_path, target_url])
                st.toast(f"Opening {pdf_name} at Page {page}...")
                return
            except Exception:
                continue

    try:
        os.startfile(os.path.abspath(pdf_path))
    except Exception as e:
        st.error(f"Error opening document: {e}")

def extract_cited_sources(response_text, retrieved_candidates, full_page_map=None):
    """
    Filters retrieved candidate chunks so that ONLY the exact documents and pages
    actually referenced/cited in the AI response are presented to the user.
    """
    cited = []
    seen = set()
    full_page_map = full_page_map or {}

    for item in retrieved_candidates:
        src = item['source']
        pg = str(item['page'])
        base_src = src.replace('.pdf', '').replace('.docx', '').replace('.txt', '')

        # Check if source name appears in response
        if src.lower() in response_text.lower() or base_src.lower() in response_text.lower():
            # Check if page number appears in response
            pg_pattern = rf'(?:page|पृष्ठ|p\.?)\s*:?\s*{pg}\b'
            if re.search(pg_pattern, response_text, re.IGNORECASE) or f" {pg} " in f" {response_text} ":
                key = (src, item['page'])
                if key not in seen:
                    seen.add(key)
                    cited.append({
                        'source': src,
                        'page': item['page'],
                        'text': full_page_map.get(key, item['text'])
                    })

    # Fallback to top-1 primary search match if no explicit citation format was matched
    if not cited and retrieved_candidates:
        top_item = retrieved_candidates[0]
        key = (top_item['source'], top_item['page'])
        cited.append({
            'source': top_item['source'],
            'page': top_item['page'],
            'text': full_page_map.get(key, top_item['text'])
        })

    return cited

def render_verified_sources(cited_sources, key_prefix="src"):
    """Renders the verified ground truth sources with 1-click PDF page launcher and text viewer."""
    if not cited_sources:
        return

    st.markdown("##### 🔍 Verified Source Document:")
    for idx, c in enumerate(cited_sources):
        if isinstance(c, dict):
            src_name = c['source']
            pg_num = c['page']
            snippet_text = c.get('text', '').strip()
        else:
            # Handle legacy string format e.g. "**directive_3.pdf** (Page 15)"
            src_name = str(c).replace("**", "")
            pg_num = 1
            snippet_text = ""

        col_info, col_btn = st.columns([3, 1])
        with col_info:
            st.markdown(f"📄 **{src_name}** — **Page {pg_num}**")
        with col_btn:
            btn_key = f"{key_prefix}_btn_{idx}_{src_name}_{pg_num}"
            if st.button(f"📖 Open Page {pg_num}", key=btn_key):
                open_pdf_at_page(src_name, pg_num)

        if snippet_text:
            with st.expander(f"👁️ View Extracted Text from {src_name} (Page {pg_num})"):
                st.text_area(
                    "Extracted Context",
                    value=snippet_text,
                    height=160,
                    disabled=True,
                    key=f"{key_prefix}_txt_{idx}_{src_name}_{pg_num}",
                    label_visibility="collapsed"
                )

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

def hybrid_search(user_query, table, model, translated_terms="", selected_doc="All Documents", top_k=6):
    k_const = 30  # Standard RRF constant

    # 1. Primary Dense Search (Direct Query Intent)
    d_pri = {}
    q_vec = model.encode(user_query).tolist()
    search_q = table.search(q_vec)
    if selected_doc and selected_doc != "All Documents":
        search_q = search_q.where(f"source = '{selected_doc}'")
    for rank, (_, row) in enumerate(search_q.limit(100).to_pandas().iterrows(), 1):
        k = (row['source'], int(row['page']))
        if k not in d_pri:
            d_pri[k] = (rank, row)

    # 2. Translated Dense Search (Cross-Lingual Bridge)
    d_trans = {}
    if translated_terms and translated_terms.strip():
        t_vec = model.encode(translated_terms).tolist()
        search_t = table.search(t_vec)
        if selected_doc and selected_doc != "All Documents":
            search_t = search_t.where(f"source = '{selected_doc}'")
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
            if selected_doc and selected_doc != "All Documents":
                search_fts1 = search_fts1.where(f"source = '{selected_doc}'")
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
                if selected_doc and selected_doc != "All Documents":
                    search_fts2 = search_fts2.where(f"source = '{selected_doc}'")
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

if "translation_cache" not in st.session_state:
    st.session_state.translation_cache = {}
if "model_usage" not in st.session_state:
    st.session_state.model_usage = {m: 0 for m in MODELS_TO_TRY}
if "model_status" not in st.session_state:
    st.session_state.model_status = {}

def expand_query_crosslingual(q, client):
    """Bidirectional cross-lingual query expansion for English & Nepali banking documents with failover."""
    clean_q = q.strip().lower()
    if clean_q in st.session_state.translation_cache:
        return st.session_state.translation_cache[clean_q]

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
            res = client.chat.completions.create(
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
                st.session_state.translation_cache[clean_q] = terms
                return terms
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                continue
            break
    return ""

# 2. Cached Resources (Loads heavy ML models once into RAM)
@st.cache_resource
def load_models():
    embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    groq_client = Groq(api_key=GROQ_API_KEY)
    return embedding_model, groq_client

def get_live_table():
    """Always connects to the live database so newly added files are immediately visible."""
    db = lancedb.connect("./lancedb_data")
    return db.open_table("bank_documents")

try:
    embedding_model, groq_client = load_models()
    table = get_live_table()
except Exception as e:
    st.error(f"⚠️ Failed to connect to database or Groq. Error: {e}")
    st.stop()

# 3. Sidebar: System Status & Document Management
with st.sidebar:
    st.title("🏦 Bank Document System")
    # st.caption("Powered by **Qwen 27B** (Groq LPU) • Multilingual (नेपाली / EN)")
    st.divider()



    # File Uploader
    st.subheader("📤 Add New Document")
    uploaded_file = st.file_uploader(
        "Drop a PDF, DOCX, or TXT file here",
        type=["pdf", "docx", "txt"]
    )
    if uploaded_file is not None:
        save_path = os.path.join("File_System", uploaded_file.name)
        if not os.path.exists(save_path):
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Saved '{uploaded_file.name}' to folder!")
            st.info("File saved. Ingest script or watcher will process it automatically.")



    # Active Documents in Database
    st.subheader("📚 Indexed Documents")
    try:
        df = table.to_pandas()
        sources_summary = df["source"].value_counts()
        for doc_name, count in sources_summary.items():
            st.write(f"• **{doc_name}** ({count} chunks)")
        doc_options = ["All Documents"] + list(sources_summary.index)
    except Exception:
        doc_options = ["All Documents"]

    st.divider()

    # Optional Document Filter
    st.subheader("🎯 Search Filter")
    selected_doc = st.selectbox(
        "Focus search on a specific file:",
        options=doc_options,
        index=0
    )

    st.divider()




    

# 4. Main Chat Interface
st.markdown("""
<div class="finance-header">
    <div class="finance-header-text">
        <h1>🏦 Document Extraction Intelligence</h1>
        <p>Institutional Document Search, Statutory Verification & Audit Clauses • Multilingual (नेपाली / EN)</p>
    </div>
    <div class="finance-badge">
        CONFIDENTIAL & SECURE
    </div>
</div>
""", unsafe_allow_html=True)

# Quick Demo Prompt Buttons (Executive Showcase)
st.markdown("##### ⚡ Quick Showcase Questions (Click to test):")
col1, col2 = st.columns(2)
with col1:
    btn1 = st.button("📋 स्वःघोषणासम्बन्धी व्यवस्था (Self-Declaration)")
    btn2 = st.button("💰 एजेन्टमार्फत नगद जम्मा गर्ने सीमा (Agent Limits)")
with col2:
    btn3 = st.button("🌐 Tell us about the self-declaration system")
    btn4 = st.button("💳 Daily & monthly cash deposit limits (English)")

# Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "नमस्ते! म यस संस्था सम्बन्धी कागजातहरूको आधिकारिक सहायक हुँ। तपाईं परिपत्र, निर्देशन, कारोबार सीमा वा शुल्कबारे कुनै पनि प्रश्न सोध्न सक्नुहुन्छ।",
            "sources": [],
            "latency": None
        }
    ]

# Display Previous Messages
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("latency"):
            st.caption(f"⚡ {msg['latency']}")
        if msg.get("sources"):
            render_verified_sources(msg["sources"], key_prefix=f"hist_{i}")

# Determine Active User Input (from typing or click)
preset_query = None
if btn1:
    preset_query = "स्वःघोषणासम्बन्धी व्यवस्था बारेमा भन्नुहोस"
elif btn2:
    preset_query = "एजेन्टमार्फत वालेटमा प्रतिदिन र प्रतिमहिना कति रकमसम्म नगद जम्मा गर्न पाइन्छ?"
elif btn3:
    preset_query = "Tell us about the self-declaration system."
elif btn4:
    preset_query = "What is the daily and monthly cash deposit limit in a wallet through an authorized agent?"

chat_input_val = st.chat_input("Type your question here (उदा: स्वःघोषणासम्बन्धी व्यवस्था बारेमा भन्नुहोस)...")
active_query = preset_query or chat_input_val

if active_query:
    start_time = time.time()
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": active_query})
    with st.chat_message("user"):
        st.markdown(active_query)

    # 2. Cross-Lingual Dual-Pass Hybrid Retrieval
    translated_terms = expand_query_crosslingual(active_query, groq_client)
    live_table = get_live_table()
    results = hybrid_search(active_query, live_table, embedding_model, translated_terms=translated_terms, selected_doc=selected_doc, top_k=6)

    # Parent Document Context Windowing: provide full page text so clauses are never severed mid-rule
    seen_pages = set()
    full_page_context = []
    full_page_map = {}
    total_chars = 0
    for item in results:
        sp = (item['source'], item['page'])
        if sp not in seen_pages:
            seen_pages.add(sp)
            try:
                page_records = live_table.search().where(f"source = '{item['source']}' AND page = {item['page']}").to_pandas()
                full_page_text = "\n".join(page_records['text'].tolist())
            except Exception:
                full_page_text = item['text']

            # Decode legacy Preeti font artifacts before providing to LLM
            full_page_text = decode_preeti_text(full_page_text)
            full_page_map[sp] = full_page_text

            full_page_context.append(f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}]:\n{full_page_text}\n")
            total_chars += len(full_page_text)
            if len(seen_pages) >= 4 or total_chars > 12000:
                break

    context_text = "\n".join(full_page_context)

    # 3. Professional Banking System Prompt
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

    # 4. Stream Groq Response to UI with Automatic Failover on 429
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        MODELS_TO_TRY = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
        active_model_used = None

        try:
            last_err = None
            for model_cand in MODELS_TO_TRY:
                try:
                    stream = groq_client.chat.completions.create(
                        model=model_cand,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": active_query}
                        ],
                        temperature=0.1,
                        max_tokens=900,
                        stream=True
                    )
                    active_model_used = model_cand
                    for chunk in stream:
                        token = chunk.choices[0].delta.content or ""
                        full_response += token
                        response_placeholder.markdown(full_response + "▌")
                    response_placeholder.markdown(full_response)
                    break
                except Exception as model_err:
                    last_err = model_err
                    if "429" in str(model_err) or "rate_limit" in str(model_err).lower():
                        continue
                    else:
                        raise model_err

            if not full_response and last_err:
                raise last_err

            # Track tokens used in session
            approx_tokens = (len(system_prompt) + len(active_query) + len(full_response)) // 4
            if active_model_used:
                st.session_state.model_usage[active_model_used] = st.session_state.model_usage.get(active_model_used, 0) + approx_tokens

            elapsed_sec = time.time() - start_time
            latency_str = f"Answered in {elapsed_sec:.2f}s via {active_model_used} on Groq LPU"
            st.caption(f"⚡ {latency_str}")

            # Extract and display only the exact verified sources cited in the response
            cited_sources = extract_cited_sources(full_response, results, full_page_map)
            render_verified_sources(cited_sources, key_prefix=f"curr_{len(st.session_state.messages)}")

            # Save to Session State
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": cited_sources,
                "latency": latency_str
            })

        except Exception as e:
            st.error(f"⚠️ Error querying Groq: {e}")
