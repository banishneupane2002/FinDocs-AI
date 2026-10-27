"""
Core RAG package for NRB Regulatory Intelligence Engine.
"""

from core.preeti import decode_preeti_text
from core.lexicon import (
    STOP_WORDS,
    SPECIAL_PREETI,
    BANKING_DOMAIN_LEXICON,
    normalize_devanagari,
    extract_meaningful_keywords
)
from core.routing import (
    detect_document_years,
    extract_query_years,
    clean_query_for_search,
    prioritize_matching_document,
    build_document_year_map
)
from core.llm import (
    MODELS_TO_TRY,
    build_rag_prompt,
    call_groq_with_retry
)
from core.search import (
    build_where_filter,
    expand_query_crosslingual,
    hybrid_search,
    extract_cited_sources
)
from core.ingestion import (
    run_ingestion,
    check_filesystem_out_of_sync,
    delete_document,
    extract_sample_text_from_file,
    categorize_file,
    get_file_metadata
)

__all__ = [
    "decode_preeti_text",
    "STOP_WORDS",
    "SPECIAL_PREETI",
    "BANKING_DOMAIN_LEXICON",
    "normalize_devanagari",
    "extract_meaningful_keywords",
    "detect_document_years",
    "extract_query_years",
    "clean_query_for_search",
    "prioritize_matching_document",
    "build_document_year_map",
    "MODELS_TO_TRY",
    "build_rag_prompt",
    "call_groq_with_retry",
    "build_where_filter",
    "expand_query_crosslingual",
    "hybrid_search",
    "extract_cited_sources",
    "run_ingestion",
    "delete_document",
    "extract_sample_text_from_file",
    "categorize_file",
    "get_file_metadata",
]

