import sys
import os
import re
import unicodedata
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
import lancedb
from sentence_transformers import SentenceTransformer

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

        for suffix in ['सम्बन्धी', 'सम्बन्धमा', 'मार्फत', 'अनुसार', 'सम्म', 'हरु', 'हरू', 'को', 'का', 'की', 'मा', 'ले', 'लाई', 'बाट']:
            if w.endswith(suffix) and len(w) > len(suffix) + 2:
                base = w[:-len(suffix)]
                if base.lower() not in STOP_WORDS and len(base) > 2:
                    keywords.add(base)
        keywords.add(w.replace('ः', ''))
        keywords.add(w.replace(':', ''))

    t_lower = text.lower()
    if any(c in t_lower for c in ['atm', 'debit', 'card', 'एटीएम', 'कार्ड']) and any(w in t_lower for w in ['withdraw', 'withdrawn', 'withdrawal', 'cash', 'झिक्ने', 'झिक्न', 'नगद', 'सीमा', 'limit', 'max', 'maximum', 'amount']):
        keywords.update(['भुक्तानी कार्ड', 'कार्डबाट नगद', 'नगद झिक्ने', 'अधिकतम सीमा', 'डेबिट कार्ड', '५० हजार', '२० हजार', 'प्रतिकारोबार', 'प्रतिदिन'])

    clean_tokens = set()
    for k in keywords:
        for t in re.findall(r'[\u0900-\u097F\w+]+', k):
            if len(t) > 1 and t.lower() not in STOP_WORDS:
                clean_tokens.add(t)

    return clean_tokens

def hybrid_search_test(user_query, table, model, top_k=6):
    k_const = 30
    d_pri = {}
    q_vec = model.encode(user_query).tolist()
    search_q = table.search(q_vec)
    for rank, (_, row) in enumerate(search_q.limit(100).to_pandas().iterrows(), 1):
        k = (row['source'], int(row['page']))
        if k not in d_pri:
            d_pri[k] = (rank, row)

    s_pri = {}
    kw_pri = extract_meaningful_keywords(user_query)
    clean_pri_fts = " ".join([w for w in kw_pri if len(w) > 1])
    if clean_pri_fts.strip():
        try:
            search_fts1 = table.search(clean_pri_fts)
            for rank, (_, row) in enumerate(search_fts1.limit(100).to_pandas().iterrows(), 1):
                k = (row['source'], int(row['page']))
                if k not in s_pri:
                    s_pri[k] = (rank, row)
        except Exception as e:
            print("FTS error:", e)

    all_keys = set(d_pri.keys()) | set(s_pri.keys())
    fused_results = []
    for k in all_keys:
        dp = d_pri[k][0] if k in d_pri else 999
        sp = s_pri[k][0] if k in s_pri else 999
        row = (d_pri.get(k) or s_pri.get(k))[1]

        rrf_score = (1.0 / (k_const + dp)) + (1.2 / (k_const + sp))

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

if __name__ == "__main__":
    db = lancedb.connect('./lancedb_data')
    table = db.open_table('bank_documents')
    model = SentenceTransformer('all-MiniLM-L6-v2')

    for q in [
        "what amount at max could be withdrawn from atm",
        "एटीएमबाट अधिकतम कति रकम झिक्न सकिन्छ?",
        "what was the atm withdrawal limit in 2080"
    ]:
        print(f"\n================ QUERY: {q} ================")
        results = hybrid_search_test(q, table, model, top_k=4)
        for i, r in enumerate(results, 1):
            print(f"#{i} Score: {r['score']:.4f} | {r['source']} Page {r['page']}")

