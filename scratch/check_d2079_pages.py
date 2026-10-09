import pypdf
reader = pypdf.PdfReader("File_System/directive_2079.pdf")
print("Total pages in directive_2079.pdf:", len(reader.pages))
for i in range(min(5, len(reader.pages))):
    print(f"--- Page {i+1} ---")
    print(repr(reader.pages[i].extract_text()[:300]))

