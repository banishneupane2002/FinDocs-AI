import lancedb
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
db = lancedb.connect('./lancedb_data')
t = db.open_table('bank_documents')

q7 = "In the FY 2024/25 stress testing results, how many Development Banks fail to meet the minimum Capital Adequacy Ratio under Credit Shock C1 (15% performing loans deteriorating into substandard)?"
vec = embedding_model.encode(q7).tolist()
df = t.search(vec).limit(250).to_pandas()
for rank, (_, r) in enumerate(df.iterrows(), 1):
    if r['source'] == 'Annual_Report_2025.pdf' and r['page'] == 33:
        print(f"p.33 found at dense rank: {rank}")
        break

