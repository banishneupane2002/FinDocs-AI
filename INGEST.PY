import os
import sys
import json
import re
import pypdf
try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None
import lancedb
from sentence_transformers import SentenceTransformer

# Year Detection Helpers for Preeti cover glyphs and Devanagari numerals
PREETI_NUM_MAP = {'!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0'}
NEP_TO_ARABIC = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}

def detect_document_years(filename: str, sample_text: str = "") -> set:
    """
    Detects all official fiscal or calendar years covered by a document.
    Distinguishes real years from phone numbers, P.O. Box, registration numbers.
    Supports multi-year documents (e.g. 2079/80, 2022-23).
    """
    years = set()

    # 1. From Filename
    for m in re.finditer(r'(20[78][0-9]|20[12][0-9])', filename):
        years.add(int(m.group(1)))

    # 2. Preeti Cover Shift Glyphs (Anchor: follows 'निर्देशन' or cover title)
    for preeti_m in re.finditer(r'@\)([&*][!@#$%\^&*()०-९0-9])', sample_text):
        decade_code = preeti_m.group(1)[0]
        unit_code = preeti_m.group(1)[1]
        decade = '7' if decade_code == '&' else '8'
        unit = PREETI_NUM_MAP.get(unit_code, NEP_TO_ARABIC.get(unit_code, unit_code))
        try:
            val = int(f"20{decade}{unit}")
            if 2070 <= val <= 2085:
                years.add(val)
        except Exception:
            pass

    # 3. Multi-year Devanagari ranges (e.g. २०७९/८० or आर्थिक वर्ष २०८०/८१)
    for m in re.finditer(r'२०([७८][०-९])(?:/([०-९]{2}))?', sample_text):
        decade_unit = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(1))
        y1 = int(f"20{decade_unit}")
        if 2070 <= y1 <= 2085:
            years.add(y1)
        if m.group(2):
            unit2 = "".join(NEP_TO_ARABIC.get(c, c) for c in m.group(2))
            y2 = int(f"20{unit2}")
            if 2070 <= y2 <= 2085:
                years.add(y2)

    # 4. Multi-year English ranges (e.g. 2023/24, 2022-23)
    for m in re.finditer(r'\b(20[12][0-9])[/-]([0-9]{2})\b', sample_text):
        y1 = int(m.group(1))
        y2 = int(str(y1)[:2] + m.group(2))
        years.add(y1)
        years.add(y2)

    # 5. Standalone English / Devanagari with Regulatory Anchors (rejects phone numbers, fax, PO Box)
    anchored_matches = re.finditer(
        r'(?:directive|circular|report|fiscal\s*year|निर्देशन|परिपत्र|प्रतिवेदन|संवत्|मिति)\s*[,:\s]*([०-९\d]{4})',
        sample_text,
        re.IGNORECASE
    )
    for m in anchored_matches:
        raw = m.group(1)
        arabic = "".join(NEP_TO_ARABIC.get(c, c) for c in raw)
        try:
            val = int(arabic)
            if 2070 <= val <= 2085 or 2010 <= val <= 2030:
                years.add(val)
        except Exception:
            pass

    return years

# Word document support
try:
    import docx
except ImportError:
    docx = None

# Preeti / Kantipur to Unicode converter
try:
    from preeti_unicode import convert_text
except ImportError:
    convert_text = None

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---
WATCH_FOLDER = "File_System"
os.makedirs(WATCH_FOLDER, exist_ok=True)
DB_FOLDER = "./lancedb_data"
TABLE_NAME = "bank_documents"
TRACKER_FILE = "indexed_files.json"

db = lancedb.connect(DB_FOLDER)

# Load tracking file
if os.path.exists(TRACKER_FILE):
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        indexed_files = json.load(f)
else:
    indexed_files = {}

SUPPORTED_EXTS = (".pdf", ".docx", ".txt")
all_files = [f for f in os.listdir(WATCH_FOLDER) if f.lower().endswith(SUPPORTED_EXTS)]

files_to_process = []
for filename in all_files:
    filepath = os.path.join(WATCH_FOLDER, filename)
    last_modified = os.path.getmtime(filepath)
    if filename not in indexed_files or indexed_files[filename] < last_modified:
        files_to_process.append((filename, filepath, last_modified))
    else:
        print(f"Skipping '{filename}' (already indexed and up to date).")

# Check for deleted files and clean up database
deleted_files = [f for f in list(indexed_files.keys()) if f not in all_files]
if deleted_files:
    print(f"\nDetected {len(deleted_files)} deleted file(s). Cleaning up database...")
    try:
        table = db.open_table(TABLE_NAME)
        for df_name in deleted_files:
            table.delete(f"source = '{df_name}'")
            del indexed_files[df_name]
            print(f"   Removed '{df_name}' and its chunks from database.")
        with open(TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump(indexed_files, f, indent=4)
        print("   Database successfully synchronized with folder deletions.")
    except Exception as e:
        print(f"   Error removing deleted records: {e}")

if not files_to_process:
    print("\nAll files in the folder are already up to date in the database!")
    exit()

print("\nLoading Multilingual Embedding Model (paraphrase-multilingual-MiniLM-L12-v2)...")
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def clean_nepali_artifacts(text: str) -> str:
    """Fix common Preeti converter glitches and garbled English acronyms."""
    replacements = {


        "अधाविधक": "अद्यावधिक",
        "विधुतीय": "विद्युतीय",
        "विधमान": "विद्यमान"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def auto_convert_nepali(text: str) -> str:
    """Detects Preeti/Kantipur legacy font and automatically converts it to real Unicode Devanagari."""
    if not text or not text.strip() or convert_text is None:
        return text
    
    # If the text already has Devanagari Unicode characters, keep it as is
    if any('\u0900' <= c <= '\u097f' for c in text):
        return text
    
    # Common markers of Preeti/Kantipur text
    preeti_markers = ["af6", "dfq", "k|lt", ";+", "g+=", "eGbf", "sf]", "nfO{", 
                      ";~rfng", "lgb]{zg", "ug'{", "kg]{", "a}+s", "shf{", "tyf", "g]kfn"]
    if any(m in text for m in preeti_markers):
        try:
            converted = convert_text(text)
            return clean_nepali_artifacts(converted)
        except Exception:
            return text
            
    return text

def chunk_page_text(text: str, target_size: int = 1000, max_size: int = 1500, overlap_size: int = 250) -> list:
    """Intelligently chunks text preserving paragraphs, numbered clauses,
    and tables with semantic overlap rather than cutting mid-sentence or mid-clause."""
    import re
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current = []
    curr_len = 0
    
    for p in paragraphs:
        p_len = len(p)
        if curr_len + p_len > target_size and current:
            chunks.append("\n".join(current))
            # Preserve semantic overlap from previous clause
            overlap = []
            o_len = 0
            for prev in reversed(current):
                if o_len + len(prev) <= overlap_size:
                    overlap.insert(0, prev)
                    o_len += len(prev)
                else:
                    break
            current = overlap
            curr_len = sum(len(x) + 1 for x in current)
        
        if p_len > max_size:
            sentences = [s.strip() for s in re.split(r'([।\.\n])', p) if s.strip()]
            temp = ""
            for s in sentences:
                if len(temp) + len(s) > target_size and temp:
                    chunks.append(temp.strip())
                    temp = ""
                temp += (" " if temp and not temp.endswith(("।", ".")) else "") + s
            if temp.strip():
                current.append(temp.strip())
                curr_len += len(temp)
        else:
            current.append(p)
            curr_len += p_len + 1
            
    if current:
        chunks.append("\n".join(current))
        
    return [c for c in chunks if len(c) >= 50]

def extract_text_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    pages_data = []
    
    if ext == ".pdf":
        if fitz is not None:
            try:
                doc = fitz.open(filepath)
                for i, page in enumerate(doc, start=1):
                    blocks = page.get_text("dict")["blocks"]
                    full_page_lines = []
                    for b in blocks:
                        if "lines" not in b:
                            continue
                        for line in b["lines"]:
                            line_parts = []
                            for span in line["spans"]:
                                text = span["text"]
                                if not text:
                                    continue
                                font = span["font"].lower()
                                # Check if span is a legacy typewriter font
                                if any(f in font for f in ["preeti", "himali", "kantipur", "fontasy", "bishall", "sagarmatha"]):
                                    try:
                                        converted = convert_text(text) if convert_text else text
                                        line_parts.append(clean_nepali_artifacts(converted))
                                    except Exception:
                                        line_parts.append(text)
                                else:
                                    # English or clean Unicode font (Times New Roman, Arial, Mangal, Calibri, etc.)
                                    line_parts.append(text)
                            line_text = "".join(line_parts).strip()
                            if line_text:
                                full_page_lines.append(line_text)
                    page_text = "\n".join(full_page_lines)
                    if page_text.strip():
                        pages_data.append((i, page_text))
            except Exception as e:
                print(f"   [PyMuPDF extraction fallback to pypdf due to: {e}]")
                pages_data = []

        # Graceful fallback to pypdf if PyMuPDF was unavailable or returned empty
        if not pages_data and pypdf is not None:
            reader = pypdf.PdfReader(filepath)
            for i, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                text = auto_convert_nepali(text)
                if text.strip():
                    pages_data.append((i, text))
                
    elif ext == ".docx":
        if docx is None:
            print("   Warning: 'python-docx' is not installed.")
            return []
        doc = docx.Document(filepath)
        full_text = "\n".join([auto_convert_nepali(p.text) for p in doc.paragraphs if p.text.strip()])
        if full_text.strip():
            pages_data.append((1, full_text))
            
    elif ext == ".txt":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            full_text = auto_convert_nepali(f.read())
        if full_text.strip():
            pages_data.append((1, full_text))
            
    return pages_data

new_records = []

for filename, filepath, last_modified in files_to_process:
    print(f"\nProcessing file: '{filename}'...")
    pages_data = extract_text_from_file(filepath)
    sample_text = " ".join([text for _, text in pages_data[:3]])
    detected_yrs = detect_document_years(filename, sample_text)
    if detected_yrs:
        yrs_str = ", ".join(str(y) for y in sorted(detected_yrs))
        print(f"   📅 Detected Document Year(s): {yrs_str}")
    
    file_chunks = 0
    for page_num, text in pages_data:
        chunks = chunk_page_text(text)
        for chunk in chunks:
            vector = embedding_model.encode(chunk).tolist()
            new_records.append({
                "vector": vector,
                "text": chunk,
                "page": page_num,
                "source": filename
            })
            file_chunks += 1

    print(f"   Extracted {file_chunks} chunks from '{filename}'.")
    indexed_files[filename] = last_modified

if not new_records:
    print("\nWarning: No readable text found in new files (they may be scanned images).")
    exit()

print("\nUpdating the database...")
try:
    table = db.open_table(TABLE_NAME)
    for filename, _, _ in files_to_process:
        try:
            table.delete(f"source = '{filename}'")
        except Exception:
            pass
    table.add(new_records)
    print(f"   Synchronized {len(new_records)} chunks into database.")
except Exception:
    table = db.create_table(TABLE_NAME, data=new_records)
    print(f"   Created new database table with {len(new_records)} chunks.")

try:
    table.create_fts_index("text", replace=True)
    print("   Synchronized native Full-Text (FTS) Inverted Index.")
except Exception as e:
    pass

with open(TRACKER_FILE, "w", encoding="utf-8") as f:
    json.dump(indexed_files, f, indent=4)

print("\nSuccess! Database is synchronized with your folder.")