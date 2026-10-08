import lancedb
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

PREETI_KEYMAP = {
    'a': 'ब', 'b': 'द', 'c': 'अ', 'd': 'म', 'e': 'भ', 'f': 'ा', 'g': 'न',
    'h': 'ज', 'i': 'ष', 'j': 'व', 'k': 'प', 'l': 'ि', 'm': 'फ', 'n': 'ल',
    'o': 'य', 'p': 'उ', 'q': 'त्र', 'r': 'च', 's': 'क', 't': 'त', 'u': 'ग',
    'v': 'ख', 'w': 'ध', 'x': 'ह', 'y': 'थ', 'z': 'श',
    'A': 'ब्', 'B': 'द्य', 'C': 'ऋ', 'D': 'म्', 'E': 'भ्', 'F': 'ँ', 'G': 'न्',
    'H': 'ज्', 'I': 'क्ष्', 'J': 'व्', 'K': 'प्', 'L': 'ी', 'M': 'ः', 'N': 'ल्',
    'O': 'इ', 'P': 'ए', 'Q': 'त्त', 'R': 'च्', 'S': 'क्', 'T': 'त्', 'U': 'ग्',
    'V': 'ख्', 'W': 'ध्', 'X': 'ह्र', 'Y': 'थ्', 'Z': 'श्',
    '0': 'ण्', '1': 'ज्ञ', '2': 'द्द', '3': 'घ', '4': 'द्ध', '5': 'छ',
    '6': 'ट', '7': 'ठ', '8': 'ड', '9': 'ढ',
    '+': 'ं', '-': '(', '=': '.', '/': 'र', '.': '।',
}

# Special variants in Nepali PDFs where B was typed as w (ध) or ligatures
SPECIAL_VARIANTS = {
    'IBFT': 'क्ष्धँत्',
    'Backup': 'धबअपगउ',
    'Settlement': 'क्भततभिफभलत',
    'Audit': 'ब्गमष्त',
}

def to_preeti(word):
    res = [SPECIAL_VARIANTS.get(word)] if word in SPECIAL_VARIANTS else []
    mapped = "".join(PREETI_KEYMAP.get(c, c) for c in word)
    if mapped != word:
        res.append(mapped)
    return [r for r in res if r]

words_to_test = ['CCTV', 'IBFT', 'TTR', 'STR', 'SAR', 'goAML', 'USSD', 'KYC', 'POS', 'Force', 'Settlement', 'System', 'Audit', 'T+3', 'T+1']
for w in words_to_test:
    p_tokens = to_preeti(w)
    for pt in p_tokens:
        hits = t.search(pt).limit(2).to_pandas()
        srcs = [f"{r['source']} p.{r['page']}" for _, r in hits.iterrows()]
        print(f"{w} -> '{pt}' -> {srcs}")

