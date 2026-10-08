import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# The user types English keystrokes, which display Nepali glyphs.
# When PyPDF / pdfplumber extracts the text from these PDFs, the character codes
# stored in the PDF's font encoding get extracted into these specific Unicode glyphs!

ENGLISH_TO_PREETI_MAP = {
    # Lowercase
    'a': 'ब', 'b': 'द', 'c': 'अ', 'd': 'म', 'e': 'भ', 'f': 'ा', 'g': 'न',
    'h': 'ज', 'i': 'ष', 'j': 'व', 'k': 'प', 'l': 'ि', 'm': 'फ', 'n': 'ल',
    'o': 'य', 'p': 'उ', 'q': 'त्र', 'r': 'च', 's': 'क', 't': 'त', 'u': 'ग',
    'v': 'ख', 'w': 'ध', 'x': 'ह', 'y': 'थ', 'z': 'श',
    # Uppercase
    'A': 'ब्', 'B': 'द्य', 'C': 'ऋ', 'D': 'म्', 'E': 'भ्', 'F': 'ँ', 'G': 'न्',
    'H': 'ज्', 'I': 'क्ष्', 'J': 'व्', 'K': 'प्', 'L': 'ी', 'M': 'ः', 'N': 'ल्',
    'O': 'इ', 'P': 'ए', 'Q': 'त्त', 'R': 'च्', 'S': 'क्', 'T': 'त्', 'U': 'ग्',
    'V': 'ख्', 'W': 'ध्', 'X': 'ह्र', 'Y': 'थ्', 'Z': 'श्',
    # Numbers and symbols
    '0': 'ण्', '1': 'ज्ञ', '2': 'द्द', '3': 'घ', '4': 'द्ध', '5': 'छ',
    '6': 'ट', '7': 'ठ', '8': 'ड', '9': 'ढ',
    '+': 'ं', '-': '(', '=': '.', '/': 'र', '.': '।',
}

def eng_to_preeti(text):
    return "".join(ENGLISH_TO_PREETI_MAP.get(c, c) for c in text)

print("CCTV ->", eng_to_preeti("CCTV"))
print("Camera ->", eng_to_preeti("Camera"))
print("Memory ->", eng_to_preeti("Memory"))
print("Backup ->", eng_to_preeti("Backup"))
print("Force ->", eng_to_preeti("Force"))
print("IBFT ->", eng_to_preeti("IBFT"))
print("System ->", eng_to_preeti("System"))
print("Audit ->", eng_to_preeti("Audit"))
print("T+3 ->", eng_to_preeti("T+3"))
print("T+1 ->", eng_to_preeti("T+1"))
print("USSD ->", eng_to_preeti("USSD"))
