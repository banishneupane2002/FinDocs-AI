import os
import sys
import json
import pypdf
import lancedb
from sentence_transformers import SentenceTransformer

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

def chunk_page_text(text: str, target_size: int = 1000, max_size: int = 1500) -> list:
    """Intelligently chunks text preserving paragraphs, numbered clauses,
    and tables rather than cutting mid-sentence or mid-table."""
    import re
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current = []
    curr_len = 0
    
    for p in paragraphs:
        p_len = len(p)
        if curr_len + p_len > target_size and current:
            chunks.append("\n".join(current))
            current = []
            curr_len = 0
        
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