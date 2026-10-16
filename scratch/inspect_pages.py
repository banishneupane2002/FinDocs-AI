import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
import lancedb
from core.preeti import decode_preeti_text

db = lancedb.connect('lancedb_data')
t = db.open_table('bank_documents')

def check_page(doc, page, query_terms):
    df = t.search().where(f"source = '{doc}' AND page = {page}").to_pandas()
    if len(df) == 0:
        print(f"Page {page} not found in {doc}")
        return
    text = decode_preeti_text("\n".join(df['text'].tolist()))
    print(f"\n--- {doc} Page {page} ---")
    for term in query_terms:
        found = term.lower() in text.lower()
        print(f"Term '{term}': {'FOUND' if found else 'NOT FOUND'}")
    print("Snippet:")
    print(text[:400])

print("Q3:")
check_page('Unified_directive_2082.pdf', 14, ['कालोसूची', 'खराब', '१००'])
check_page('Unified_directive_2082.pdf', 15, ['कालोसूची', 'खराब', '१००'])

print("\nQ5:")
check_page('Unified_directive_2082.pdf', 118, ['अनिवार्य नगद', 'मौज्दात', '४', 'प्रतिशत'])
check_page('Unified_directive_2082.pdf', 120, ['वैधानिक তরलता', '१०'])

print("\nQ17:")
check_page('Unified_directive_2082.pdf', 105, ['१० लाख', 'दश लाख', '९० दिन', 'कालोसूची'])
check_page('Unified_directive_2082.pdf', 113, ['१० लाख', 'दश लाख', '९० दिन', 'कालोसूची'])

print("\nQ18:")
check_page('directive_2082.pdf', 21, ['३ लाख', 'क्युआर', 'QR', 'मोबाइल'])
check_page('directive_2082.pdf', 22, ['३ लाख', 'क्युआर', 'QR', 'मोबाइल'])
