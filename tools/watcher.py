import time
import os
import sys
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Resolve project root regardless of whether run from root or tools/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCH_FOLDER = os.path.join(PROJECT_ROOT, "File_System")
INGEST_SCRIPT = os.path.join(PROJECT_ROOT, "INGEST.PY")
SUPPORTED_EXTS = (".pdf", ".docx", ".txt")

class DocumentWatcherHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Ignore folders and non-document files
        if not event.is_directory and event.src_path.lower().endswith(SUPPORTED_EXTS):
            filename = os.path.basename(event.src_path)
            print(f"\n[DETECTOR] New file dropped into folder: '{filename}'")
            print(">> Running automatic ingestion in the background...")
            
            # Brief pause to ensure the file is completely saved by the OS
            time.sleep(1)
            
            # Automatically triggers INGEST.PY
            subprocess.run([sys.executable, INGEST_SCRIPT], cwd=PROJECT_ROOT)
            print(">> Document successfully indexed! You can now ask questions about it in ask.py.\n")

    def on_modified(self, event):
        if not event.is_directory and event.src_path.lower().endswith(SUPPORTED_EXTS):
            filename = os.path.basename(event.src_path)
            print(f"\n[DETECTOR] File updated: '{filename}'")
            print(">> Updating document index...")
            time.sleep(1)
            subprocess.run([sys.executable, INGEST_SCRIPT], cwd=PROJECT_ROOT)
            print(">> Index updated!\n")

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.lower().endswith(SUPPORTED_EXTS):
            filename = os.path.basename(event.src_path)
            print(f"\n[DETECTOR] File removed from folder: '{filename}'")
            print(">> Automatically synchronizing database and removing deleted chunks...")
            subprocess.run([sys.executable, INGEST_SCRIPT], cwd=PROJECT_ROOT)
            print(f">> Successfully purged '{filename}' from vector database!\n")

if __name__ == "__main__":
    os.makedirs(WATCH_FOLDER, exist_ok=True)
    event_handler = DocumentWatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_FOLDER, recursive=False)
    
    print("=" * 60)
    print("👀 REAL-TIME FOLDER WATCHER IS ACTIVE!")
    print(f"Monitoring folder: {os.path.abspath(WATCH_FOLDER)}")
    print("Drop any .pdf, .docx, or .txt file here to auto-index it.")
    print("Press Ctrl + C to stop.")
    print("=" * 60 + "\n")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nWatcher stopped.")
    observer.join()

