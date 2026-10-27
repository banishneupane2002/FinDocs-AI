import os
import sys

# Prevent network calls/hangs in HuggingFace & PyTorch
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import io
import re
import unicodedata

# Force UTF-8 on Windows
if sys.platform == "win32":
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import lancedb
from sentence_transformers import SentenceTransformer

from core import (
    decode_preeti_text,
    extract_query_years,
    clean_query_for_search,
    build_document_year_map,
    expand_query_crosslingual,
    hybrid_search,
)

# Connect to LanceDB & local embedding model (Zero API calls, 100% offline)
DB_PATH = os.path.join(PROJECT_ROOT, "lancedb_data")
db = lancedb.connect(DB_PATH)
table = db.open_table("bank_documents")
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def inspect_query(q, show_full=False):
    print("=" * 65)
    print(f"QUERY: {q}")
    print("=" * 65)

    # 1. Fiscal year routing
    matched_years = extract_query_years(q)
    doc_year_map = build_document_year_map(table)

    effective_doc = None
    if matched_years:
        matching_docs = []
        for d, yrs in doc_year_map.items():
            if any(y in yrs for y in matched_years):
                matching_docs.append(d)
        if matching_docs:
            effective_doc = matching_docs if len(matching_docs) > 1 else matching_docs[0]
            print(f"🎯 Target Document(s): {effective_doc} (matched year: {matched_years})")

    search_query = clean_query_for_search(q, matched_years) if effective_doc else q
    if not search_query.strip():
        search_query = q

    # 2. Cross-Lingual Domain Lexicon Expansion (0 LLM tokens, 100% offline!)
    translated_terms = expand_query_crosslingual(search_query, client=None)
    if translated_terms:
        print(f"🌐 Domain Lexicon Expansion: {translated_terms}")

    # 3. Hybrid Search (Dense vector + BM25 FTS with RRF fusion)
    results = hybrid_search(
        search_query, 
        table, 
        embedding_model, 
        translated_terms=translated_terms, 
        selected_doc=effective_doc, 
        top_k=8
    )

    # 4. Multi-year interleaving if comparative
    if len(matched_years) > 1:
        target_docs = set()
        for yr in matched_years:
            for d, yrs in doc_year_map.items():
                if yr in yrs:
                    target_docs.add(d)
        if target_docs:
            by_doc = {d: [] for d in target_docs}
            for item in results:
                if item['source'] in by_doc:
                    by_doc[item['source']].append(item)
            interleaved = []
            for i in range(3):
                for d in sorted(by_doc.keys()):
                    if i < len(by_doc[d]):
                        interleaved.append(by_doc[d][i])
            if interleaved:
                results = interleaved

    # 5. Parent Document Context Windowing with Preeti decoding
    seen_pages = set()
    total_chars = 0
    extracted_context = []

    for item in results:
        sp = (item['source'], item['page'])
        if sp not in seen_pages:
            seen_pages.add(sp)
            try:
                page_records = table.search().where(f"source = '{item['source']}' AND page = {item['page']}").select(["text"]).to_pandas()
                full_page_text = "\n".join(page_records['text'].tolist())
            except Exception:
                full_page_text = item['text']

            full_page_text = decode_preeti_text(full_page_text)
            extracted_context.append({
                'source': item['source'],
                'page': item['page'],
                'score': round(item.get('score', 0), 4),
                'text': full_page_text
            })
            total_chars += len(full_page_text)
            if len(seen_pages) >= 5 or total_chars > 12000:
                break

    print(f"\nExtracted {len(extracted_context)} parent pages ({total_chars} characters):")
    for idx, c in enumerate(extracted_context, 1):
        print(f"\n--- [PAGE {idx}] {c['source']} | Page {c['page']} (RRF Score: {c['score']}) ---")
        preview = c['text'].strip()
        if show_full:
            print(preview)
        else:
            print(preview[:900] + ("\n... [remaining text truncated for preview; pass --full to view entire page]" if len(preview) > 900 else ""))
    print("\n" + "=" * 65 + "\n")
    return extracted_context


if __name__ == "__main__":
    args = sys.argv[1:]
    show_full = "--full" in args
    filtered_args = [a for a in args if a != "--full"]
    if filtered_args:
        inspect_query(" ".join(filtered_args), show_full=show_full)
    else:
        print("Usage: python inspect_context.py <your question> [--full]")
