"""
LLM calling logic, prompt engineering, and model failover management.
"""

MODELS_TO_TRY = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]

def build_rag_prompt(context_text: str) -> str:
    """Builds the authoritative NRB banking system prompt with context."""
    return f"""You are an official banking document intelligence assistant for Nepal Rastra Bank.
Your job is to extract exact figures, limits, fee tiers, and regulatory clauses from the provided context.

RULES:
1. If the question is in Nepali, answer in formal, professional Nepali (zero Hindi words).
2. If the question is in English, answer in clear, professional English.
3. Present the exact numbers, fee tier ranges, and limits clearly.
4. Quote the exact clause from the document whenever applicable.
5. Always cite the document name and page number.
6. Interpret statutory conditions and exclusionary scopes logically:
   - For example, if a directive states that a service is permitted in "X बाहेकका क्षेत्रमा" (areas except/excluding X), state definitively that it cannot be operated / is not permitted in X. Do not claim information is missing when the regulatory scope is explicitly defined.
7. Only state "उपलब्ध कागजातमा यो जानकारी फेला परेन / Information not found in the documents" if the subject matter is genuinely absent from the provided context.
8. Strict Citation Boundary: Cite ONLY the specific document and page where the extracted provision or clause is actually stated. Do NOT invent, assume, or add speculative notes claiming that a clause or provision is also present in other documents or pages unless that exact clause is explicitly found in that other document within the provided context.
9. Recency & Conciseness: Unless the user explicitly asks for a comparative analysis across multiple years, prioritize and provide the operative provisions from the latest applicable directive directly. Do NOT append unsolicited historical comparisons or long essays discussing superseded older directives. Keep the answer direct, authoritative, and concise.

Context from files:
{context_text}"""

def call_groq_with_retry(groq_client, messages: list, temperature: float = 0.1, max_tokens: int = 1100, stream: bool = True):
    """
    Executes completion call with automatic failover across candidate models on rate limits.
    Returns (stream/response, model_used).
    """
    last_err = None
    for model_cand in MODELS_TO_TRY:
        try:
            res = groq_client.chat.completions.create(
                model=model_cand,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            return res, model_cand
        except Exception as model_err:
            last_err = model_err
            err_str = str(model_err).lower()
            if "429" in err_str or "rate_limit" in err_str or "413" in err_str or "too large" in err_str:
                continue
            else:
                raise model_err

    if last_err:
        raise last_err
    raise RuntimeError("Failed to generate response across all models.")

