"""
Document administration, filesystem tracking, category classification, and ingestion execution.
"""

import os
import sys
import json
import subprocess
from core.routing import detect_document_years

def run_ingestion():
    """Runs INGEST.PY to synchronize all files in File_System/ with LanceDB."""
    return subprocess.run([sys.executable, "INGEST.PY"], capture_output=True, text=True)

def check_filesystem_out_of_sync(watch_folder: str = "File_System", tracker_file: str = "indexed_files.json") -> bool:
    """Checks in < 1ms whether files in File_System/ were added, modified, or deleted compared to tracker."""
    if not os.path.exists(watch_folder):
        return False
    indexed_files = {}
    if os.path.exists(tracker_file):
        try:
            with open(tracker_file, "r", encoding="utf-8") as f:
                indexed_files = json.load(f)
        except Exception:
            indexed_files = {}

    supported_exts = (".pdf", ".docx", ".txt")
    all_files = [f for f in os.listdir(watch_folder) if f.lower().endswith(supported_exts)]

    # Check for new or updated files on disk
    for fname in all_files:
        fpath = os.path.join(watch_folder, fname)
        try:
            mtime = os.path.getmtime(fpath)
            if fname not in indexed_files or indexed_files[fname] < mtime:
                return True
        except Exception:
            pass

    # Check for files removed from disk
    for fname in list(indexed_files.keys()):
        if fname not in all_files:
            return True

    return False

def delete_document(filename: str, live_table=None) -> bool:
    """Safely removes a file from File_System, cleans up LanceDB records, and updates tracker."""
    file_path = os.path.join("File_System", filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
    
    # Clean from LanceDB
    if live_table is not None:
        try:
            live_table.delete(f"source = '{filename}'")
        except Exception:
            pass
        
    # Clean from tracker
    tracker_file = "indexed_files.json"
    if os.path.exists(tracker_file):
        try:
            with open(tracker_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if filename in data:
                del data[filename]
            with open(tracker_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass
    return True

def extract_sample_text_from_file(filename: str, df=None) -> str:
    """Extracts first pages of text from LanceDB cache or directly from disk."""
    if df is not None:
        try:
            matching = df[df["source"] == filename]["text"].head(6).tolist()
            if matching:
                return " ".join(matching)
        except Exception:
            pass
            
    file_path = os.path.join("File_System", filename)
    if not os.path.exists(file_path):
        return ""
        
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        try:
            import fitz
            doc = fitz.open(file_path)
            pages = [doc[i].get_text() for i in range(min(4, len(doc)))]
            return " ".join(pages)
        except Exception:
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                pages = [reader.pages[i].extract_text() or "" for i in range(min(4, len(reader.pages)))]
                return " ".join(pages)
            except Exception:
                pass
    elif ext in [".txt", ".docx"]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(5000)
        except Exception:
            pass
    return ""

def categorize_file(filename: str, sample_text: str = "") -> str:
    """
    Intelligently categorizes documents into official regulatory classifications
    by analyzing document content first, falling back to filename.
    Even if the filename is completely random, content analysis detects the true category.
    """
    t = sample_text.lower()
    
    # 1. Payment system indicators (content-level)
    if any(k in t for k in [
        'भुक्तानी', 'भुत्तफानी', 'भुत्तानी', 'payment', 'psdept', 
        'वालेट', 'wallet', 'पिएसपी', 'pso', 'psp', "5u'rft", "5m-rfi"
    ]):
        return 'payment'
        
    # 2. Unified directives for BFIs (content-level)
    if any(k in t for k in [
        'एकीकृत निर्देशन', 'एकीकृत निदर्ेशन', 'इजाजतपत्रप्राप्त', 
        'वर्गका इजाजतपत्र', 'unified directive', 'prudential'
    ]):
        return 'unified'
        
    # 3. Supervision & Annual reports (content-level)
    if any(k in t for k in [
        'supervision report', 'annual report', 'सुपरीवेक्षण प्रतिवेदन', 
        'वार्षिक प्रतिवेदन', 'financial institutions supervision'
    ]):
        return 'report'
        
    # 4. Fallback to filename analysis if sample text was empty
    f = filename.lower()
    if 'unified' in f:
        return 'unified'
    elif 'payment' in f or 'directive' in f or 'bhuktani' in f:
        return 'payment'
    elif 'report' in f or 'annual' in f or 'supervision' in f:
        return 'report'
        
    return 'other'

def get_file_metadata(filename: str, sources_summary: dict, df=None) -> dict:
    """Gathers file size, detected fiscal years, chunk count, and category for a file."""
    file_path = os.path.join("File_System", filename)
    size_mb = os.path.getsize(file_path) / (1024 * 1024) if os.path.exists(file_path) else 0.0
    sample_text = extract_sample_text_from_file(filename, df)
    detected_yrs = detect_document_years(filename, sample_text)
    years_str = ", ".join(str(y) for y in sorted(detected_yrs)) if detected_yrs else "—"
    chunk_count = sources_summary.get(filename, 0)
    category = categorize_file(filename, sample_text)
    return {
        "filename": filename,
        "size_mb": size_mb,
        "years_str": years_str,
        "chunk_count": chunk_count,
        "category": category
    }

