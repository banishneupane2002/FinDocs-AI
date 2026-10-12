import sys
import lancedb
from sentence_transformers import SentenceTransformer

# Ensure clean UTF-8 printing on Windows terminal
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# 1. Connect to our LanceDB table
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")

# 2. Load the active multilingual embedding model
print("Loading multilingual model...")
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# 3. Ask any question about your banking documents!
query = "संस्थापक शेयर खरिदकर्ता संस्था भएमा"

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