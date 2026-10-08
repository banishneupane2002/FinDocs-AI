import sys, os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('.'))

from scratch.test_accuracy15 import extract_meaningful_keywords

q7 = "In the FY 2024/25 stress testing results, how many Development Banks fail to meet the minimum Capital Adequacy Ratio under Credit Shock C1 (15% performing loans deteriorating into substandard)?"
kw = extract_meaningful_keywords(q7)
print("Q7 keywords:", kw)
