import lancedb
from sentence_transformers import SentenceTransformer

# 1. Connect to our LanceDB table
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")

# 2. Load the same embedding model
print("Loading model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# 3. Ask any question about your book!
query = "formula of duration?"

print(f"\n🔍 Searching for: '{query}'\n")

# Convert the question into a vector
query_vector = embedding_model.encode(query).tolist()

# 4. Search the vector database for the top 3 closest matches
results = table.search(query_vector).limit(3).to_pandas()

# 5. Display the matching paragraphs and their exact pages
for i, row in results.iterrows():
    print(f"=== RESULT #{i + 1} ===")
    print(f"📄 Document : {row['source']}")
    print(f"📖 Page     : Page {row['page']}")
    print(f"📝 Excerpt  :\n{row['text'].strip()}")
    print("-" * 60)