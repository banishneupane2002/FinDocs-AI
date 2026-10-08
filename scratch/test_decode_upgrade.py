import os, sys
sys.path.insert(0, os.path.abspath("."))
import ask

rec = ask.table.search().where("source = 'directive_3.pdf' AND page = 15").to_pandas()
raw = "\n".join(rec['text'].tolist())

print("=== RAW EXTRACTED LINES FROM P15 ===")
for line in raw.split("\n"):
    if any(k in line for k in ["System", "Audit", "१ वर्ष", "साविक", "द्ध", "ग्उनचबमभ"]):
        print("RAW :", repr(line))

# Test with expanded Preeti replacements
replacements = [
    ('ग्उनचबमभ', 'Upgrade'),
    ('प्रतिस्थापन वा System Upgrade', 'प्रतिस्थापन वा System Upgrade'),
    ('द्ध. भुक्तानी', '४. भुक्तानी'),
    ('द्ध.', '४.'),
    ('द्द.', '२.'),
    ('ज्ञ.', '१.'),
    ('(ज्ञ)', '(१)'),
    ('(द्द)', '(२)'),
    ('(द्ध)', '(४)'),
    ('आर्थकि', 'आर्थिक'),
    ('गरार्इ', 'गराई'),
    ('इकार्इ', 'इकाई'),
    ('र्इ', 'ई'),
]

test_clean = ask.decode_preeti_text(raw)
for garbled, clean in replacements:
    test_clean = test_clean.replace(garbled, clean)

print("\n=== CLEANED LINES ===")
for line in test_clean.split("\n"):
    if any(k in line for k in ["System", "Audit", "१ वर्ष", "साविक", "४.", "Upgrade"]):
        print("CLEAN:", repr(line))

