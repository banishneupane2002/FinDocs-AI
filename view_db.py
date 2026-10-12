import sys
import lancedb

# Ensure clean UTF-8 printing on Windows terminal
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# 1. Connect to our saved database
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")

# 2. Check how many chunks were saved
total_chunks = len(table)
print(f"Total chunks stored in database: {total_chunks}")
print("-" * 60)

# 3. Look at the first 2 chunks
df = table.to_pandas()

for index, row in df.head(2).iterrows():
    print(f"--- CHUNK #{index + 1} ---")
    print(f"Page Number : {row['page']}")
    print(f"Source File : {row['source']}")
    print(f"Text Content: {row['text'][:150]}...")
    
    vec = row['vector']
    print(f"Vector (Numbers): [{vec[0]:.4f}, {vec[1]:.4f}, {vec[2]:.4f}, ... {len(vec)} total numbers]")
    print("-" * 60)