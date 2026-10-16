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

def clean_extract_keywords(text: str) -> set:
    text_norm = unicodedata.normalize('NFKD', text)
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

        # Nepali morphological suffix trimming
        for suffix in ['सम्बन्धी', 'सम्बन्धमा', 'मार्फत', 'अनुसार', 'सम्म', 'हरु', 'हरू', 'को', 'का', 'की', 'मा', 'ले', 'लाई', 'बाट']:
            if w.endswith(suffix) and len(w) > len(suffix) + 2:
                base = w[:-len(suffix)]
                if base.lower() not in STOP_WORDS and len(base) > 2:
                    keywords.add(base)
    return keywords

import lancedb
db = lancedb.connect('lancedb_data')
tbl = db.open_table('bank_documents')

q = "When calculating the Capital Adequacy Ratio (CAR), what is the risk weight assigned to loans secured by residential properties?"
kw = clean_extract_keywords(q)
query_str = " ".join(kw)
print("Clean query:", query_str)
res = tbl.search(query_str).limit(10).to_pandas()
print("\nTop 10 hits for clean Q6 query:")
for idx, (_, r) in enumerate(res.iterrows(), 1):
    p225 = " *** TARGET PAGE 225 ***" if r['page'] == 225 and '2082' in r['source'] else ""
    print(f"  {idx}: {r['source']} page {r['page']} score={r['_score']:.2f}{p225}")

