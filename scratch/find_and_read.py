import os
import json

found_path = None
for root, dirs, files in os.walk(r"C:\Users\Banish"):
    if "benchmark_final_15.json" in files:
        found_path = os.path.join(root, "benchmark_final_15.json")
        print("FOUND:", found_path)
        break

if found_path:
    with open(found_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} results successfully!")
    # Copy to current project scratch
    dst = os.path.join(os.path.dirname(__file__), "benchmark_final_15.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved copy to:", dst)
    for d in data:
        print(f"\n[{d['id']}] {d['question']}")
        print(f"Sources: {d['sources']}")
        print(f"Model: {d['model']}")
        print(f"Answer:\n{d['answer']}")
else:
    print("Not found in C:\\Users\\Banish")

