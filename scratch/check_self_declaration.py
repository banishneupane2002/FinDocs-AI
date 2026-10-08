import sys
import lancedb
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db = lancedb.connect('./lancedb_data')
table = db.open_table('bank_documents')
df = table.to_pandas()
print('Total rows in DB:', len(df))

matches = df[df['text'].str.contains('घोषणा|declaration|स्वः|स्वघोषणा', case=False, na=False)]
print(f'Matches found for declaration/घोषणा: {len(matches)}')
for idx, row in matches.iterrows():
    print(f"Source: {row['source']}, Page: {row['page']}")
    print(row['text'][:250].strip())
    print('-'*50)

