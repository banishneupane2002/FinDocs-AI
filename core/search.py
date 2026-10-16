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

def expand_query_crosslingual(q: str, client, cache: dict = None) -> str:
    """Bidirectional cross-lingual query expansion for English & Nepali banking documents."""
    clean_q = q.strip().lower()
    if cache is not None and clean_q in cache:
        return cache[clean_q]
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
            "- wallet -> वालेट (NOT वॉलेट)\n"
            "- banking -> बैंकिङ्ग (NOT बैंकिंग)\n"
            "- payment -> भुक्तानी (NOT पेमेन्ट)\n"
            "- agent -> आधिकारिक प्रतिनिधि, एजेन्ट\n"
            "- cash deposit -> नगद जम्मा\n"
            "- cash withdrawal -> नगद झिक्ने, नगद प्राप्त\n"
            "- blacklisting -> कालोसूची, फुकुवा\n"
            "- watchlist / loan classification / provision -> सूक्ष्म निगरानी, सुक्ष्म निगरानी, कर्जा वर्गीकरण, १ देखि ३ महिना, कर्जा नोक्सानी व्यवस्था, ५ प्रतिशत, असल १ प्रतिशत, खराब १०० प्रतिशत\n"
            "- personal guarantee / additional provision -> व्यक्तिगत जमानी, थप २० प्रतिशत कर्जा नोक्सानी व्यवस्था\n"
            "- blacklisted borrower loan classification -> कर्जा सूचना केन्द्र, कालोसूचीमा कायम खराब वर्ग वर्गीकरण, खराब कर्जा १०० प्रतिशत कर्जा नोक्सानी व्यवस्था\n"
            "- CD ratio / credit deposit -> कर्जा निक्षेप अनुपात, Credit to Deposit, ९० प्रतिशत, हर्जाना, बैंक दर\n"
            "- SLR / CRR / liquidity / cash reserve -> ४ प्रतिशत अनिवार्य नगद मौज्दात, १० प्रतिशत वैधानिक तरलता अनुपात\n"
            "- CAR / Capital Adequacy / residential property risk weight -> Capital Adequacy Framework, residential property, mortgages, 60%, ६० प्रतिशत, risk-weighted\n"
            "- deprived sector lending -> विपन्न वर्ग कर्जा, ५.० प्रतिशत, ५ प्रतिशत\n"
            "- MSME / agriculture lending requirement -> तोकिएका क्षेत्र, कृषि, साना तथा मझौला, १३ प्रतिशत, १५ प्रतिशत, २०८४, २०८५\n"
            "- personal residential home loan limit -> व्यक्तिगत आवासीय घर कर्जा, ३ करोड, ३० मिलियन\n"
            "- single obligor limit / SOL -> एकल ग्राहक कर्जा सीमा, प्राथमिक पुँजी, २५ प्रतिशत\n"
            "- margin lending / share loan / LTV -> Margin Lending, शेयर धितो कर्जा, मार्जिन कर्जा, ७० प्रतिशत, १८० दिन, बजार मूल्य\n"
            "- CEO age limit -> प्रमुख कार्यकारी अधिकृत, ६५ वर्ष, ६९ वर्ष\n"
            "- CEO vacancy / appointment -> प्रमुख कार्यकारी अधिकृत, रिक्त पद, पदपूर्ति, ३ महिना, तीन महिना\n"
            "- director loan -> सञ्चालक कर्जा, लिन पाउने छैन, प्रतिबन्ध\n"
            "- self-declaration -> स्वघोषणा\n"
            "- threshold transaction / TTR -> सीमा कारोबार, त्त्च्, १० लाख, १५ दिन, goAML\n"
            "- suspicious transaction / STR -> शंकास्पद कारोबार, क्त्च्, ३ दिन, तीन दिन, ३ कार्यदिन\n"
            "- blacklisting minimum loan default amount -> कालोसूचीमा समावेश दश लाख कर्जा सूचना केन्द्र, १० लाख, ९० दिन\n"
            "- mobile banking / QR transfer daily limit -> मोबाइल बैंकिङ्ग, क्युआर कोड, ३ लाख प्रतिदिन, ३,००,०००\n"
            "- bank account to digital wallet transfer -> बैंक खाताबाट वालेट, २ लाख, १० लाख, प्रतिदिन\n"
            "- suspicious activity / SAR -> शंकास्पद गतिविधि, क्ब्च्\n"
            "- USSD -> ग्क्क्म्, USSD\n"
            "- CCTV / camera / backup -> ऋऋत्ख्, क्यामेरा, ब्याकअप, नब्बे दिन, ९०, एटीएम\n"
            "- force settlement -> Force Settlement, ँयचअभ, क्भततभिफभलत, त्ंघ, त्ंज्ञ\n"
            "- simplified KYC -> सरलीकृत ग्राहक पहिचान, मचर्ेन्ट, १,००,०००\n"
            "- IBFT / fund transfer -> अन्तर बैंक, रकमान्तर, क्ष्धँत्, रु. १०\n"
            "- system audit -> System Audit, क्थकतभफ ब्गमष्त, प्रणाली परीक्षण, १ वर्ष, २ आर्थिक वर्ष\n"
            "- overnight balance -> ओभरनाइट मौज्दात, ५० हजार, बैंक खाता\n"
            "- debit card / ATM cash withdrawal limit -> कार्डबाट नगद झिक्ने अधिकतम सीमा, डेबिट कार्ड, ५० हजार, २० हजार, ३ लाख, नगद झिक्ने, एटीएम\n"
            "- contactless -> Contactless, कन्ट्याक्टलेस, ५ हजार, ५,०००\n"
            "Return 3-6 comma-separated terms in official script (Devanagari or English as specified), nothing else."
        )

    for model_cand in MODELS_TO_TRY:
        try:
            max_toks = 450 if "gpt-oss" in model_cand else 100
            res = client.chat.completions.create(
                model=model_cand,
                messages=[
                    {"role": "system", "content": sys_instruction},
                    {"role": "user", "content": q}
                ],
                temperature=0.0,
                max_tokens=max_toks
            )
            terms = res.choices[0].message.content.strip()
            if terms:
                _TRANSLATION_CACHE[clean_q] = terms
                if cache is not None:
                    cache[clean_q] = terms
                return terms
        except Exception as e:
            continue
    return ""

def hybrid_search(user_query: str, table, model, translated_terms: str = "", selected_doc = "All Documents", top_k: int = 6) -> list:
    """
    Executes enterprise multi-concept hybrid retrieval combining dense vectors + multi-phrase sparse BM25.
    Scores chunks via Reciprocal Rank Fusion (RRF) with query-intent awareness and prevailing recency boost.
    """
    k_const = 30  # Standard RRF constant
    where_filter = build_where_filter(selected_doc)

    # Query Intent Detection: Financial/Annual Reports vs Regulatory Directives
    is_report_query = bool(re.search(
        r'\b(?:annual\s*report|वार्षिक\s*प्रतिवेदन|balance\s*sheet|financial\s*position|financial\s*statement|total\s*assets|total\s*liabilities|commercial\s*bank\s*list|development\s*bank\s*list|growth\s*rate)\b',
        user_query,
        re.IGNORECASE
    ))

    def get_doc_year(src: str) -> int:
        ym = re.search(r'(20[78][0-9]|20[12][0-9])', src)
        return int(ym.group(1)) if ym else 0

    # 1. Primary Dense Search (Direct Query Intent)
    d_pri = {}
    q_vec = model.encode(user_query).tolist()
    search_q = table.search(q_vec)
    if where_filter:
        search_q = search_q.where(where_filter)
    for rank, (_, row) in enumerate(search_q.limit(80).to_pandas().iterrows(), 1):
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
        for rank, (_, row) in enumerate(search_t.limit(80).to_pandas().iterrows(), 1):
            k = (row['source'], int(row['page']))
            if k not in d_trans:
                d_trans[k] = (rank, row)

    # 3. Primary Sparse Inverted Index Search (Exact Native Term Matching)
    s_pri = {}
    kw_pri = extract_meaningful_keywords(user_query)
    clean_pri_fts = " ".join([w for w in kw_pri if len(w) > 1 or w in '०१२३४५६७८९0123456789'])
    if clean_pri_fts.strip():
        try:
            search_fts1 = table.search(clean_pri_fts)
            if where_filter:
                search_fts1 = search_fts1.where(where_filter)
            for rank, (_, row) in enumerate(search_fts1.limit(80).to_pandas().iterrows(), 1):
                k = (row['source'], int(row['page']))
                if k not in s_pri:
                    s_pri[k] = (rank, row)
        except Exception:
            pass

    # 4. Multi-Concept Sparse Search on Translated Terms (handles compound concepts without LLM calls)
    s_trans_scores = {}
    s_trans_rows = {}
    if translated_terms and translated_terms.strip():
        concept_phrases = [p.strip() for p in translated_terms.split(',') if p.strip()]
        for phrase in concept_phrases:
            kw_c = extract_meaningful_keywords(phrase)
            c_fts = " ".join([w for w in kw_c if len(w) > 1 or w in '०१२३४५६७८९0123456789'])
            if c_fts.strip():
                try:
                    s_t = table.search(c_fts)
                    if where_filter:
                        s_t = s_t.where(where_filter)
                    for rank, (_, row) in enumerate(s_t.limit(20).to_pandas().iterrows(), 1):
                        k = (row['source'], int(row['page']))
                        s_trans_scores[k] = s_trans_scores.get(k, 0.0) + (2.2 / (k_const + rank))
                        if k not in s_trans_rows:
                            s_trans_rows[k] = row
                except Exception:
                    pass

    # 5. RRF Fusion with Year Recency Boost
    all_keys = set(d_pri.keys()) | set(d_trans.keys()) | set(s_pri.keys()) | set(s_trans_scores.keys())
    all_sources = [k[0] for k in all_keys]
    bs_years = [get_doc_year(s) for s in all_sources if get_doc_year(s) >= 2050]
    ad_years = [get_doc_year(s) for s in all_sources if 2000 <= get_doc_year(s) < 2050]
    max_bs_year = max(bs_years, default=0)
    max_ad_year = max(ad_years, default=0)

    rrf_scores = {}
    for k in all_keys:
        score = 0.0
        row_obj = None

        if k in d_pri:
            score += 0.8 / (k_const + d_pri[k][0])
            row_obj = d_pri[k][1]
        if k in d_trans:
            score += 0.8 / (k_const + d_trans[k][0])
            if row_obj is None:
                row_obj = d_trans[k][1]
        if k in s_pri:
            score += 1.3 / (k_const + s_pri[k][0])
            if row_obj is None:
                row_obj = s_pri[k][1]
        if k in s_trans_scores:
            score += s_trans_scores[k]
            if row_obj is None:
                row_obj = s_trans_rows[k]

        doc_yr = get_doc_year(k[0])
        is_bs = (doc_yr >= 2050)
        if is_report_query:
            if not is_bs and max_ad_year > 0 and doc_yr == max_ad_year:
                score *= 1.60
            elif not is_bs and max_ad_year > 0 and doc_yr == max_ad_year - 1:
                score *= 1.10
            elif is_bs:
                score *= 0.70
        else:
            if is_bs and max_bs_year > 0 and doc_yr == max_bs_year:
                score *= 1.80
            elif is_bs and max_bs_year > 0 and doc_yr == max_bs_year - 1:
                score *= 0.75
            elif is_bs:
                score *= 0.40
            else:
                score *= 0.40

        rrf_scores[k] = (score, row_obj)

    sorted_items = sorted(rrf_scores.values(), key=lambda x: x[0], reverse=True)

    # Diversity capping: allow prevailing documents up to top_k slots
    # Non-prevailing older documents get at most 1 slot so they do not crowd out prevailing regulations
    results = []
    if not selected_doc or selected_doc == "All Documents":
        doc_counts = {}
        for score, r in sorted_items:
            if r is not None:
                src = r['source']
                yr = get_doc_year(src)
                is_bs = (yr >= 2050)
                if is_report_query:
                    is_prevailing = (not is_bs and max_ad_year > 0 and yr == max_ad_year)
                else:
                    is_prevailing = (is_bs and max_bs_year > 0 and yr == max_bs_year)
                max_for_doc = top_k if is_prevailing else 1
                if doc_counts.get(src, 0) < max_for_doc:
                    doc_counts[src] = doc_counts.get(src, 0) + 1
                    r_dict = r.to_dict() if hasattr(r, 'to_dict') else dict(r)
                    results.append(r_dict)
                    if len(results) >= top_k:
                        break

        # Fill any remaining slots if needed
        if len(results) < top_k:
            existing_keys = {(r['source'], r['page']) for r in results}
            for score, r in sorted_items:
                if r is not None:
                    k = (r['source'], r['page'])
                    if k not in existing_keys:
                        existing_keys.add(k)
                        r_dict = r.to_dict() if hasattr(r, 'to_dict') else dict(r)
                        results.append(r_dict)
                        if len(results) >= top_k:
                            break
    else:
        results = [item[1].to_dict() for item in sorted_items[:top_k] if item[1] is not None]

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
            pg_pattern = rf'(?:page|पृष्ठ|p\.?)\s*[:\-–—]?\s*{pg}\b'
            m_pg = re.search(pg_pattern, response_text, re.IGNORECASE)
            if m_pg:
                key = (src, item['page'])
                if key not in seen:
                    seen.add(key)
                    pos = m_pg.start()
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

