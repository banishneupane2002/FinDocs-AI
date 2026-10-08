import re

def extract_cited_sources(response_text, retrieved_candidates):
    cited = []
    seen = set()
    
    for item in retrieved_candidates:
        src = item['source']
        pg = str(item['page'])
        base_src = src.replace('.pdf', '').replace('.docx', '').replace('.txt', '')
        
        if (src.lower() in response_text.lower() or base_src.lower() in response_text.lower()):
            pg_pattern = rf'(?:page|पृष्ठ|p\.?)\s*:?\s*{pg}\b'
            if re.search(pg_pattern, response_text, re.IGNORECASE) or f" {pg} " in f" {response_text} ":
                key = (src, item['page'])
                if key not in seen:
                    seen.add(key)
                    cited.append({
                        'source': src,
                        'page': item['page'],
                        'text': item['text']
                    })
                    
    if not cited and retrieved_candidates:
        top_item = retrieved_candidates[0]
        cited.append({
            'source': top_item['source'],
            'page': top_item['page'],
            'text': top_item['text']
        })
        
    return cited

# Sample test
candidates = [
    {'source': 'directive_3.pdf', 'page': 15, 'text': 'पुरा भएपछि भुक्तानी प्रणालीको परीक्षण (System Audit)...'},
    {'source': 'directive_1.pdf', 'page': 15, 'text': 'पुरा भएपछि भुक्तानी प्रणालीको परीक्षण (System Audit)...'},
    {'source': 'Annual_Report_2024.pdf', 'page': 40, 'text': 'The balance sheet of the bank shows...'},
    {'source': 'directive_2078.pdf', 'page': 10, 'text': 'General guidelines on payment systems...'},
]

ai_response_1 = """
Based on the provided documents:
1. First System Audit: After 1 year.
Citation: directive_3.pdf, Page 15.
"""

ai_response_2 = """
Here is the audit rule:
Citation: *directive_3.pdf*, Page 15; *directive_1.pdf*, Page 15.
"""

print("Test 1 (Only directive 3 cited):")
res1 = extract_cited_sources(ai_response_1, candidates)
for r in res1:
    print(f"  -> {r['source']} (Page {r['page']})")

print("\nTest 2 (Both directive 3 and 1 cited):")
res2 = extract_cited_sources(ai_response_2, candidates)
for r in res2:
    print(f"  -> {r['source']} (Page {r['page']})")

