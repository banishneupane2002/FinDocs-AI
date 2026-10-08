import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app

# Test file resolution
pdf_name = "directive_3.pdf"
page = 15

pdf_path = os.path.join("File_System", pdf_name)
assert os.path.exists(pdf_path), "PDF must exist in File_System"
abs_path = os.path.abspath(pdf_path).replace("\\", "/")
target_url = f"file:///{abs_path}#page={page}"
print("Resolved Target URL:", target_url)
print("✅ Path and URL resolution syntax verified!")

