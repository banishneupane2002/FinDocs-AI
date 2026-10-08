import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ask

candidates = [
    {'source': 'directive_3.pdf', 'page': 15},
    {'source': 'Annual_Report_2024.pdf', 'page': 40},
    {'source': 'directive_2078.pdf', 'page': 10},
]

sample_response = """
1. First Audit: After 1 year.
Citation: directive_3.pdf, Page 15.
"""

cited = ask.extract_cited_sources(sample_response, candidates)
print("Filter result:", cited)
assert len(cited) == 1
assert cited[0]['source'] == 'directive_3.pdf'
assert cited[0]['page'] == 15
print("✅ Citation filter verification PASSED!")

