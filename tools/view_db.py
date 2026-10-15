"""
LanceDB Chunk Inspector & Database Viewer
Allows inspecting stored chunks, filtering by document/page, searching text, and checking database stats.
"""

import os
import sys
import argparse
import lancedb

# Ensure clean UTF-8 printing on Windows terminal
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from core.preeti import decode_preeti_text
except ImportError:
    decode_preeti_text = lambda x: x

DB_PATH = os.path.join(PROJECT_ROOT, "lancedb_data")

def main():
    parser = argparse.ArgumentParser(description="Inspect chunks stored in LanceDB vector database.")
    parser.add_argument("--doc", "-d", type=str, default=None, help="Filter chunks by document filename (partial match supported)")
    parser.add_argument("--page", "-p", type=int, default=None, help="Filter chunks by exact page number")
    parser.add_argument("--search", "-s", type=str, default=None, help="Search for text/keyword inside chunks")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Number of chunks to display (default: 5)")
    parser.add_argument("--stats", action="store_true", help="Show document chunk counts summary")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database folder not found at {DB_PATH}")
        return

    db = lancedb.connect(DB_PATH)
    try:
        table = db.open_table("bank_documents")
    except Exception as e:
        print(f"❌ Error opening table 'bank_documents': {e}")
        return

    total_chunks = len(table)

    # If no filter arguments are provided or --stats is requested, show summary
    if (args.doc is None and args.page is None and args.search is None) or args.stats:
        print("=" * 70)
        print(f"📊 LanceDB Database Summary: {total_chunks:,} total chunks")
        print("=" * 70)

        # Pull lightweight metadata to summarize docs
        df_meta = table.search().select(["source", "page"]).to_pandas()
        if not df_meta.empty:
            summary = df_meta.groupby("source").agg(
                chunks=('page', 'count'),
                pages=('page', 'nunique'),
                min_page=('page', 'min'),
                max_page=('page', 'max')
            ).reset_index()

            print(f"{'Document Name':<42} | {'Chunks':<8} | {'Pages'}")
            print("-" * 70)
            for _, row in summary.iterrows():
                print(f"{row['source'][:40]:<42} | {row['chunks']:<8} | {row['pages']} pages (p.{row['min_page']}-{row['max_page']})")
            print("-" * 70)

        print("\n💡 Usage Examples to watch chunks:")
        print("  python tools/view_db.py --doc 2082               # View chunks from 2082 directive")
        print("  python tools/view_db.py --doc 2082 --page 22     # View chunks on page 22")
        print("  python tools/view_db.py --search 'Overnight'     # Search chunks containing 'Overnight'")
        print("  python tools/view_db.py --limit 10               # View first 10 chunks")
        print("=" * 70)

        if not (args.doc or args.page or args.search):
            return

    # Build query filter
    filters = []
    if args.doc:
        # Check matching filenames
        df_sources = table.search().select(["source"]).to_pandas()
        all_sources = list(df_sources["source"].unique())
        if args.doc in all_sources:
            matching_sources = [args.doc]
        else:
            matching_sources = [s for s in all_sources if args.doc.lower() in s.lower()]
        if matching_sources:
            if len(matching_sources) == 1:
                filters.append(f"source = '{matching_sources[0]}'")
                print(f"📁 Filtering by document: {matching_sources[0]}")
            else:
                sources_or = " OR ".join([f"source = '{s}'" for s in matching_sources])
                filters.append(f"({sources_or})")
                print(f"📁 Matching documents: {', '.join(matching_sources)}")
        else:
            print(f"⚠️ No documents match '{args.doc}'. Available: {list(all_sources)}")
            return

    if args.page is not None:
        filters.append(f"page = {args.page}")

    where_clause = " AND ".join(filters) if filters else None

    # Retrieve matching chunks
    query = table.search()
    if where_clause:
        query = query.where(where_clause)

    # If searching text
    if args.search:
        # Full text or substring search
        print(f"🔍 Searching for: '{args.search}' in chunks...")
        df_results = query.select(["source", "page", "text"]).to_pandas()
        search_lower = args.search.lower()
        mask = df_results["text"].str.lower().str.contains(search_lower, regex=False, na=False)
        df_results = df_results[mask].head(args.limit)
    else:
        df_results = query.select(["source", "page", "text"]).limit(args.limit).to_pandas()

    if df_results.empty:
        print("\n⚠️ No chunks found matching your criteria.")
        return

    print(f"\nDisplaying {len(df_results)} chunk(s):\n")
    for idx, (_, row) in enumerate(df_results.iterrows(), 1):
        decoded_text = decode_preeti_text(row['text']).strip()
        print(f"┌{'─' * 68}┐")
        print(f"│ CHUNK #{idx} | Document: {row['source']} | Page: {row['page']}")
        print(f"├{'─' * 68}┤")
        # Print text indented
        for line in decoded_text.splitlines():
            print(f"  {line}")
        print(f"└{'─' * 68}┘\n")

if __name__ == "__main__":
    main()
