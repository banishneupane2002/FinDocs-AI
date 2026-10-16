import os
import sys
import io
import re
import math
import time
import lancedb
from sentence_transformers import SentenceTransformer
from groq import Groq

# Force UTF-8 on Windows terminal
if sys.platform == "win32":
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# Load GROQ API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.strip().split("=", 1)[1].strip()

if not GROQ_API_KEY:
    print("❌ Error: GROQ_API_KEY not found. Please set it in .env or as an environment variable.")
    sys.exit(1)

client = Groq(api_key=GROQ_API_KEY)

# Connect to LanceDB and the Multilingual Model
db = lancedb.connect("./lancedb_data")
table = db.open_table("bank_documents")
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Import all shared RAG algorithms and domain knowledge from core
from core import (
    decode_preeti_text,
    extract_query_years,
    clean_query_for_search,
    build_document_year_map,
    expand_query_crosslingual,
    hybrid_search,
    call_groq_with_retry,
    extract_cited_sources,
    build_rag_prompt,
    MODELS_TO_TRY
)

def main():
    print("=" * 65)
    print("  🏦 NRB Regulatory Intelligence RAG Terminal (Dual-Pass Engine)")
    print("  Type your question in Nepali or English, or 'exit' / 'quit'")
    print("=" * 65)

    while True:
        try:
            user_question = input("\nAsk a question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not user_question:
            continue
        if user_question.lower() in ["exit", "quit", "q"]:
            print("Dhanyabaad! Exiting.")
            break

        # Automatic Query Year Routing & Document Selection
        doc_year_map = build_document_year_map(table)
        available_years = set.union(*doc_year_map.values()) if doc_year_map else set()
        matched_years = extract_query_years(user_question, available_years)

        effective_doc = None
        if len(matched_years) == 1:
            target_yr = list(matched_years)[0]
            matching_docs = [d for d, yrs in doc_year_map.items() if target_yr in yrs]
            if matching_docs:
                effective_doc = matching_docs if len(matching_docs) > 1 else matching_docs[0]
                doc_names_str = ", ".join(f"`{d}`" for d in matching_docs)
                print(f"   🎯 Auto-routed to {target_yr} Directives / Reports ({doc_names_str})")
        elif len(matched_years) > 1:
            yrs_str = ", ".join(str(y) for y in sorted(matched_years))
            print(f"   📊 Comparative Multi-Year Query (analyzing across years: {yrs_str})")

        search_query = clean_query_for_search(user_question, matched_years) if effective_doc else user_question
        if not search_query.strip():
            search_query = user_question

        print("   Searching documents (Cross-Lingual Dual-Pass Hybrid Retrieval)...")

        translated_terms = expand_query_crosslingual(search_query, client)
        results = hybrid_search(search_query, table, embedding_model, translated_terms=translated_terms, selected_doc=effective_doc, top_k=8)

        # For comparative multi-year queries, interleave results across matched documents so all target years enter context
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

        # Parent Document Context Windowing with Preeti decoding
        seen_pages = set()
        full_page_context = []
        sources = []
        total_chars = 0
        for item in results:
            sp = (item['source'], item['page'])
            if sp not in seen_pages:
                seen_pages.add(sp)
                try:
                    page_records = table.search().where(f"source = '{item['source']}' AND page = {item['page']}").to_pandas()
                    full_page_text = "\n".join(page_records['text'].tolist())
                except Exception:
                    full_page_text = item['text']

                # Decode legacy Preeti font artifacts before providing to LLM
                full_page_text = decode_preeti_text(full_page_text)

                full_page_context.append(f"\n[कागजात: {item['source']} | पृष्ठ: {item['page']}]:\n{full_page_text}\n")
                sources.append(f"{item['source']} (Page {item['page']})")
                total_chars += len(full_page_text)
                if len(seen_pages) >= 5 or total_chars > 12000:
                    break

        context_text = "\n".join(full_page_context)
        system_prompt = build_rag_prompt(context_text)

        print("   AI is generating answer...\n")
        try:
            print("Assistant:\n", end="", flush=True)
            stream, model_used = call_groq_with_retry(
                client,
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ]
            )

            full_response = ""
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_response += content
                print(content, end="", flush=True)

            print(f"\n\n(Generated via {model_used})")
            cited_sources = extract_cited_sources(full_response, results, target_years=matched_years, target_doc=effective_doc)
            print("Verified Source(s) Cited:")
            for c in cited_sources:
                print(f"   * {c['source']} (Page {c['page']})")

            # Also display other retrieved candidate pages
            cited_keys = {(c['source'], c['page']) for c in cited_sources}
            remaining = [r for r in results if (r['source'], r['page']) not in cited_keys]
            if remaining:
                def other_sort_key(c):
                    src = c['source']
                    ym = re.search(r'(20[78][0-9]|20[12][0-9])', src)
                    yr = int(ym.group(1)) if ym else 0
                    target_match = 0
                    if effective_doc:
                        if isinstance(effective_doc, (list, set, tuple)) and src in effective_doc:
                            target_match = 0
                        elif isinstance(effective_doc, str) and src == effective_doc:
                            target_match = 0
                    elif matched_years and yr in matched_years:
                        target_match = 0
                    else:
                        target_match = 1
                    return (target_match, -yr if not matched_years else 0, c.get('page', 0))

                remaining.sort(key=other_sort_key)
                print("\nOther Retrieved Reference Pages:")
                seen_rem = set()
                for r in remaining:
                    rk = (r['source'], r['page'])
                    if rk not in seen_rem:
                        seen_rem.add(rk)
                        print(f"   - {r['source']} (Page {r['page']})")

            print("-" * 65 + "\n")

        except Exception as e:
            print(f"\n⚠️ Error connecting to Groq API: {e}\n")

if __name__ == "__main__":
    main()