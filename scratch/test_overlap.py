import os, sys
sys.path.insert(0, os.getcwd())
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import fitz
from preeti_unicode import convert_text

doc = fitz.open('File_System/Unified_directive_2082.pdf')
page = doc[22] # Page 23
blocks = page.get_text('dict')['blocks']
full_page_lines = []
for b in blocks:
    if 'lines' not in b: continue
    for l in b['lines']:
        line_parts = []
        for s in l['spans']:
            t = s['text']
            font = s['font'].lower()
            if any(f in font for f in ['preeti', 'himali', 'kantipur', 'fontasy', 'bishall', 'sagarmatha']):
                try: t = convert_text(t)
                except: pass
            line_parts.append(t)
        line_text = "".join(line_parts).strip()
        if line_text:
            full_page_lines.append(line_text)
full_p23 = "\n".join(full_page_lines)

def chunk_with_overlap(text: str, target_size: int = 1000, max_size: int = 1500, overlap_size: int = 250) -> list:
    import re
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current = []
    curr_len = 0
    
    for p in paragraphs:
        p_len = len(p)
        if curr_len + p_len > target_size and current:
            chunks.append("\n".join(current))
            # Keep overlap
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
            
        current.append(p)
        curr_len += p_len + 1
        
    if current:
        chunks.append("\n".join(current))
    return chunks

chunks = chunk_with_overlap(full_p23)
print(f"Total chunks created: {len(chunks)}")
for i, c in enumerate(chunks, 1):
    print(f"\n--- CHUNK {i} ({len(c)} chars) ---")
    print(c[:300] + " ... " + c[-150:])
    has_margin = "Margin" in c or "मार्जिन" in c
    has_70 = "७०" in c or "70" in c
    has_180 = "१८०" in c or "180" in c
    print(f"Has Margin: {has_margin} | Has 70%: {has_70} | Has 180-days: {has_180}")
