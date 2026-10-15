"""
Dual-pass cross-lingual hybrid retrieval (Dense Vector + BM25 Full-Text + RRF ranking).
"""

import os
import re
from core.lexicon import extract_meaningful_keywords
from core.preeti import decode_preeti_text
from core.llm import MODELS_TO_TRY

_TRANSLATION_CACHE = {}

def build_where_filter(doc_spec) -> str | None:
    """Builds a LanceDB SQL WHERE filter based on user selection or auto-routing target."""
    if not doc_spec or doc_spec == "All Documents":
        return None
    if isinstance(doc_spec, (list, set, tuple)):
        doc_list = [str(d) for d in doc_spec]
        if not doc_list:
            return None
        if len(doc_list) == 1:
            return f"source = '{doc_list[0]}'"
        doc_in_str = ", ".join(f"'{d}'" for d in doc_list)
        return f"source IN ({doc_in_str})"
    return f"source = '{doc_spec}'"

def expand_query_crosslingual(q: str, client) -> str:
    """Bidirectional cross-lingual query expansion for English & Nepali banking documents."""
    clean_q = q.strip().lower()
    if clean_q in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[clean_q]

    is_nepali = sum(1 for c in q if '\u0900' <= c <= '\u097f') >= max(len(q.replace(' ', '')), 1) * 0.3

    if is_nepali:
        sys_instruction = (
            "You are a specialized bilingual terminology engine for Nepal Rastra Bank reports and directives.\n"
            "The user question is in Nepali. Translate the core banking entities and financial metrics into their official English terminology (for finding tables in English Annual Reports):\n"
            "- एकीकृत वित्तीय स्थिति / वित्तीय विवरण -> Consolidated Statement of Financial Position, Financial Position, Annex 3.3, Balance Sheet\n"
            "- विकास बैंक -> Development Banks, DBs\n"
            "- वाणिज्य बैंक -> Commercial Banks, CBs\n"
            "- वित्त कम्पनी -> Finance Companies, FCs\n"
            "- जुलाई / मध्य जुलाई -> Mid-July, July\n"
            "- कुल सम्पत्ति / दायित्व -> Total Assets, Total Liabilities, Equity\n"
            "- इन्टरनेट बैंकिङ -> Internet Banking\n"
            "- मोबाइल बैंकिङ -> Mobile Banking\n"
            "- वञ्चित क्षेत्र कर्जा -> Deprived Sector Lending\n"
            "- आधार दर -> Base Rate\n"
            "- तनाव परीक्षण / स्ट्रेस टेस्टिङ -> Stress Testing, Liquidity Shock, Credit Shock C1\n"
            "- शीघ्र सुधारात्मक कारबाही -> Prompt Corrective Action, PCA\n"
            "- निष्कृय कर्जा / खराब कर्जा -> Non-Performing Loans, NPL\n"
            "- पुँजी पर्याप्तता फ्रेमवर्क -> Capital Adequacy Framework, Basel III\n"
            "- सञ्चालक ऋण -> directors, board members borrowing\n"
            "- नाफा / घाटा -> net profit, net loss\n"
            "Output 3-5 comma-separated English terms, nothing else."
        )
    else:
        sys_instruction = (
            "Translate all key banking subjects, services, and regulatory concepts from the question into official Nepal Rastra Bank (NRB) Nepali terms.\n"
            "Always use official Nepali Devanagari terms:\n"
            "- wallet -> वालेट (NOT वॉलेट)\n"
            "- banking -> बैंकिङ्ग (NOT बैंकिंग)\n"
            "- payment -> भुक्तानी (NOT पेमेन्ट)\n"
            "- agent -> आधिकारिक प्रतिनिधि, एजेन्ट\n"
            "- cash deposit -> नगद जम्मा\n"
            "- cash withdrawal -> नगद झिक्ने, नगद प्राप्त\n"
            "- blacklisting -> कालोसूची, फुकुवा\n"
            "- self-declaration -> स्वघोषणा\n"
            "- threshold transaction / TTR -> सीमा कारोबार, त्त्च्, १० लाख, १५ दिन, goAML\n"
            "- suspicious transaction / STR -> शंकास्पद कारोबार, क्त्च्\n"
            "- suspicious activity / SAR -> शंकास्पद गतिविधि, क्ब्च्\n"
            "- USSD -> ग्क्क्म्, USSD\n"
            "- CCTV / camera / backup -> ऋऋत्ख्, क्यामेरा, ब्याकअप, नब्बे दिन, ९०\n"
            "- force settlement -> Force Settlement, ँयचअभ, क्भततभिफभलत, त्ंघ, त्ंज्ञ\n"
            "- simplified KYC -> सरलीकृत ग्राहक पहिचान, मचर्ेन्ट, १,००,०००\n"
            "- IBFT / fund transfer -> अन्तर बैंक, रकमान्तर, क्ष्धँत्, रु. १०\n"
            "- system audit -> System Audit, क्थकतभफ ब्गमष्त, प्रणाली परीक्षण, १ वर्ष, २ आर्थिक वर्ष\n"
            "- overnight balance -> ओभरनाइट मौज्दात, ५० हजार, बैंक खाता\n"
            "- debit card / ATM cash withdrawal limit -> कार्डबाट नगद झिक्ने अधिकतम सीमा, डेबिट कार्ड, ५० हजार, २० हजार, ३ लाख, नगद झिक्ने, एटीएम\n"
            "- contactless -> Contactless, कन्ट्याक्टलेस, ५ हजार, ५,०००\n"
            "Return 3-6 comma-separated Nepali terms in Devanagari script only, nothing else."
        )

    for model_cand in MODELS_TO_TRY:
        try:
            res = client.chat.completions.create(
                model=model_cand,
                messages=[
                    {"role": "system", "content": sys_instruction},
                    {"role": "user", "content": q}
                ],
                temperature=0.0,
                max_tokens=60
            )
            terms = res.choices[0].message.content.strip()
            if terms:
                _TRANSLATION_CACHE[clean_q] = terms
                return terms
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                continue
            break
    return ""

def hybrid_search(user_query: str, table, model, translated_terms: str = "", selected_doc = "All Documents", top_k: int = 6) -> list:
    """
    Executes 4-pass hybrid search combining direct and cross-lingual dense vectors + sparse BM25.
    Scores chunks via Reciprocal Rank Fusion (RRF).
    """
    k_const = 30  # Standard RRF constant
    where_filter = build_where_filter(selected_doc)

    # 1. Primary Dense Search (Direct Query Intent)
    d_pri = {}
    q_vec = model.encode(user_query).tolist()
    search_q = table.search(q_vec)
    if where_filter:
        search_q = search_q.where(where_filter)
    for rank, (_, row) in enumerate(search_q.limit(100).to_pandas().iterrows(), 1):
        k = (row['source'], int(row['page']))
        if k not in d_pri:
            d_pri[k] = (rank, row)

    # 2. Translated Dense Search (Cross-Lingual Bridge)
    d_trans = {}
    if translated_terms and translated_terms.strip():
        t_vec = model.encode(translated_terms).tolist()
        search_t = table.search(t_vec)
        if where_filter:
            search_t = search_t.where(where_filter)
        for rank, (_, row) in enumerate(search_t.limit(100).to_pandas().iterrows(), 1):
            k = (row['source'], int(row['page']))
            if k not in d_trans:
                d_trans[k] = (rank, row)

    # 3. Primary Sparse Inverted Index Search (Exact Native Term Matching)
    s_pri = {}
    kw_pri = extract_meaningful_keywords(user_query)
    clean_pri_fts = " ".join([w for w in kw_pri if len(w) > 1])
    if clean_pri_fts.strip():
        try:
            search_fts1 = table.search(clean_pri_fts)
            if where_filter:
                search_fts1 = search_fts1.where(where_filter)
            for rank, (_, row) in enumerate(search_fts1.limit(100).to_pandas().iterrows(), 1):
                k = (row['source'], int(row['page']))
                if k not in s_pri:
                    s_pri[k] = (rank, row)
        except Exception:
            pass

    # 4. Translated Sparse Inverted Index Search (Exact Target Term Matching)
    s_trans = {}
    if translated_terms and translated_terms.strip():
        kw_trans = extract_meaningful_keywords(translated_terms)
        clean_trans_fts = " ".join([w for w in kw_trans if len(w) > 1])
        if clean_trans_fts.strip():
            try:
                search_fts2 = table.search(clean_trans_fts)
                if where_filter:
                    search_fts2 = search_fts2.where(where_filter)
                for rank, (_, row) in enumerate(search_fts2.limit(100).to_pandas().iterrows(), 1):
                    k = (row['source'], int(row['page']))
                    if k not in s_trans:
                        s_trans[k] = (rank, row)
            except Exception:
                pass

    # 5. Reciprocal Rank Fusion (RRF) with Document Recency Boost
    rrf_scores = {}
    all_keys = set(d_pri.keys()) | set(d_trans.keys()) | set(s_pri.keys()) | set(s_trans.keys())

    # Detect modern directive year from filenames to give prevailing rules priority
    def get_doc_year(src: str) -> int:
        ym = re.search(r'(20[78][0-9]|20[12][0-9])', src)
        return int(ym.group(1)) if ym else 0

    all_sources = [k[0] for k in all_keys]
    max_year = max([get_doc_year(s) for s in all_sources], default=0)

    for k in all_keys:
        score = 0.0
        row_obj = None

        if k in d_pri:
            score += 1.0 / (k_const + d_pri[k][0])
            row_obj = d_pri[k][1]
        if k in d_trans:
            score += 0.9 / (k_const + d_trans[k][0])
            row_obj = row_obj or d_trans[k][1]
        if k in s_pri:
            score += 1.3 / (k_const + s_pri[k][0])
            row_obj = row_obj or s_pri[k][1]
        if k in s_trans:
            score += 1.1 / (k_const + s_trans[k][0])
            row_obj = row_obj or s_trans[k][1]

        # Year recency bonus for prevailing directives
        doc_yr = get_doc_year(k[0])
        if max_year > 0 and doc_yr == max_year:
            score *= 1.25
        elif max_year > 0 and doc_yr == max_year - 1:
            score *= 1.10

        rrf_scores[k] = (score, row_obj)

    # Sort candidates by combined RRF score
    sorted_items = sorted(rrf_scores.values(), key=lambda x: x[0], reverse=True)
    results = [item[1].to_dict() for item in sorted_items[:top_k]]
    return results

def extract_cited_sources(response_text: str, retrieved_candidates: list, full_page_map: dict = None, live_table = None, target_years: set = None, target_doc = None) -> list:
    """
    Extracts verified document citations strictly aligned with the ground-truth source
    that generated the AI response, ordered with primary source first.
    """
    cited = []
    seen = set()
    full_page_map = full_page_map or {}

    regex_patterns = [
        r'([a-zA-Z0-9_\-\.]+\.(?:pdf|docx|txt))(?:\s*[\:\|\-\–\—\(\)\[\]]?\s*|\s+(?:clause|section|दफा|खण्ड)\s*[^\n\r]{0,25}?\s*|\s*\n\s*)(?:page|पृष्ठ|p\.?)\s*[:\-]?\s*(\d+)',
        r'(?:page|पृष्ठ|p\.?)\s*[:\-]?\s*(\d+)(?:\s*[\:\|\-\–\—\(\)\[\]]?\s*|\s*\n\s*)(([a-zA-Z0-9_\-\.]+\.(?:pdf|docx|txt)))',
        r'\[\s*(?:कागजात|doc|document)?\s*[:\-]?\s*([a-zA-Z0-9_\-\.]+\.(?:pdf|docx|txt))\s*\|\s*(?:पृष्ठ|page)\s*[:\-]?\s*(\d+)\s*\]',
        r'([a-zA-Z0-9_\-]+(?:directive|report)[a-zA-Z0-9_\-]*)(?:\s*[\:\|\-\–\—\(\)\[\]]?\s*|\s*\n\s*)(?:page|पृष्ठ|p\.?)\s*[:\-]?\s*(\d+)'
    ]

    found_matches = []
    for pat in regex_patterns:
        for m in re.finditer(pat, response_text, re.IGNORECASE):
            g1, g2 = m.group(1), m.group(2)
            if g1.isdigit():
                doc_name = g2
                page_num = int(g1)
            else:
                doc_name = g1
                page_num = int(g2)

            if not doc_name.lower().endswith(('.pdf', '.docx', '.txt')):
                if os.path.exists(os.path.join("File_System", f"{doc_name}.pdf")):
                    doc_name = f"{doc_name}.pdf"

            if os.path.exists(os.path.join("File_System", doc_name)):
                found_matches.append((m.start(), doc_name, page_num))

    # Sort matches by character position in the AI's response text
    found_matches.sort(key=lambda x: x[0])

    for pos, doc_name, page_num in found_matches:
        key = (doc_name, page_num)
        if key not in seen:
            seen.add(key)
            snippet = full_page_map.get(key, "")
            if not snippet and live_table is not None:
                try:
                    recs = live_table.search().where(f"source = '{doc_name}' AND page = {page_num}").to_pandas()
                    if len(recs) > 0:
                        snippet = decode_preeti_text("\n".join(recs['text'].tolist()))
                except Exception:
                    pass
            cited.append({
                'source': doc_name,
                'page': page_num,
                'text': snippet,
                'pos': pos
            })

    # Match against retrieved candidate chunks
    norm_resp = re.sub(r'[\s_\-]+', ' ', response_text.lower())
    for item in retrieved_candidates:
        src = item['source']
        pg = str(item['page'])
        base_src = src.replace('.pdf', '').replace('.docx', '').replace('.txt', '')
        norm_base = re.sub(r'[\s_\-]+', ' ', base_src.lower())

        if src.lower() in response_text.lower() or base_src.lower() in response_text.lower() or norm_base in norm_resp:
            pg_pattern = rf'(?:page|पृष्ठ|p\.?)\s*:?\s*{pg}\b'
            if re.search(pg_pattern, response_text, re.IGNORECASE) or f" {pg} " in f" {response_text} " or f"({pg})" in response_text or f": {pg}" in response_text:
                key = (src, item['page'])
                if key not in seen:
                    seen.add(key)
                    m_src = re.search(re.escape(src), response_text, re.IGNORECASE) or re.search(re.escape(base_src), response_text, re.IGNORECASE)
                    pos = m_src.start() if m_src else 999999
                    cited.append({
                        'source': src,
                        'page': item['page'],
                        'text': full_page_map.get(key, item.get('text', '')),
                        'pos': pos
                    })

    # Fallback to top-1 primary search match if no explicit citation format was matched
    if not cited and retrieved_candidates:
        top_item = retrieved_candidates[0]
        key = (top_item['source'], top_item['page'])
        cited.append({
            'source': top_item['source'],
            'page': top_item['page'],
            'text': full_page_map.get(key, top_item.get('text', '')),
            'pos': 0
        })

    def citation_sort_key(c):
        pos = c.get('pos', 999999)
        src = c['source']
        ym = re.search(r'(20[78][0-9]|20[12][0-9])', src)
        yr = int(ym.group(1)) if ym else 0

        target_match = 1
        if target_doc:
            if isinstance(target_doc, (list, set, tuple)) and src in target_doc:
                target_match = 0
            elif isinstance(target_doc, str) and src == target_doc:
                target_match = 0
        elif target_years and yr in target_years:
            target_match = 0

        tiebreak_year = -yr if not target_years else 0
        return (target_match, pos, tiebreak_year)

    cited.sort(key=citation_sort_key)
    return cited

