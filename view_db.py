import lancedb

# 1. Connect to our saved database
db = lancedb.connect("./lancedb_data")
table = db.open_table("dsp_book")

# 2. Check how many chunks were saved
total_chunks = len(table)
print(f"Total chunks stored in database: {total_chunks}")
print("-" * 60)

# 3. Look at the first 2 chunks
# (We convert to pandas to easily inspect it like an Excel table)
df = table.to_pandas()

for index, row in df.head(2).iterrows():
    print(f"--- CHUNK #{index + 1} ---")
    print(f"Page Number : {row['page']}")
    print(f"Source File : {row['source']}")
    print(f"Text Content: {row['text'][:150]}...") # printing first 150 characters
    
    # Let's peek at the vector numbers!
    vec = row['vector']
    print(f"Vector (Numbers): [{vec[0]:.4f}, {vec[1]:.4f}, {vec[2]:.4f}, ... {len(vec)} total numbers]")
    print("-" * 60)