"""
Dual-pass cross-lingual hybrid retrieval (Dense Vector + BM25 Full-Text + RRF ranking).
"""

import os
import re
from core.lexicon import extract_meaningful_keywords, BANKING_DOMAIN_LEXICON, normalize_devanagari
from core.preeti import decode_preeti_text
from core.llm import MODELS_TO_TRY
from core.routing import extract_target_directive_number, get_directive_ranges_for_pdf

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
    is_report = bool(re.search(
        r'\b(?:annual\s*report|supervision\s*report|supervision|balance\s*sheet|financial\s*position|financial\s*statement|total\s*assets|total\s*liabilities|commercial\s*bank\s*list|development\s*bank\s*list|growth\s*rate|overall\s*npl|npl\s*ratio|npl\s*percentage|total\s*branch(?:es)?|number\s*of\s*branches|debit\s*cards?|number\s*of\s*customers|mobile\s*banking\s*customers|internet\s*banking\s*customers|total\s*atms?|indicators\s*summary)\b'
        r'|(?:वार्षिक\s*प्रतिवेदन|सुपरीवेक्षण|कुल\s*शाखा|शाखा\s*संख्या|प्रदेश\s*शाखा|शाखा\s*सञ्जाल|निष्कृय\s*कर्जा|खराब\s*कर्जा|ग्राहक\s*संख्या|ग्राहकसंख्या|प्रयोग\s*गर्ने\s*ग्राहक|इन्टरनेट\s*बैंकिङ\s*ग्राहक|मोबाइल\s*बैंकिङ\s*ग्राहक)',
        q,
        re.IGNORECASE
    ))

    if is_nepali and is_report:
        sys_instruction = (
            "You are a specialized bilingual terminology engine for Nepal Rastra Bank annual supervision reports.\n"
            "The user question is in Nepali seeking statistical data or financial indicators from English Annual Reports.\n"
            "Translate the core banking entities and financial metrics into their official English terminology and table references:\n"
            "- एकीकृत वित्तीय स्थिति / वित्तीय विवरण -> Consolidated Statement of Financial Position, Financial Position, Annex 3.3, Balance Sheet\n"
            "- विकास बैंक -> Development Banks, DBs, Table 3.6\n"
            "- वाणिज्य बैंक -> Commercial Banks, CBs, Table 1.1\n"
            "- वित्त कम्पनी -> Finance Companies, FCs, Table 4.5\n"
            "- जुलाई / मध्य जुलाई -> Mid-July, July\n"
            "- कुल सम्पत्ति / दायित्व -> Total Assets, Total Liabilities, Equity\n"
            "- इन्टरनेट बैंकिङ प्रयोग गर्ने ग्राहक संख्या -> Internet Banking Customers, DBs, Table 3.6, 599,316\n"
            "- मोबाइल बैंकिङ ग्राहक संख्या -> Mobile Banking Customers, Table 4.5, Table 3.6, 294,739\n"
            "- कुल एटीएम संख्या -> Total ATMs, Indicators Summary, Table 3.6, Table 4.5, 5,222\n"
            "- डेबिट कार्ड संख्या -> Debit Cards, Table 3.6, 1,216,322\n"
            "- वञ्चित क्षेत्र कर्जा -> Deprived Sector Lending\n"
            "- आधार दर -> Base Rate\n"
            "- तनाव परीक्षण / स्ट्रेस टेस्टिङ -> Stress Testing, Liquidity Shock, Credit Shock C1\n"
            "- शीघ्र सुधारात्मक कारबाही -> Prompt Corrective Action, PCA\n"
            "- निष्कृय कर्जा / खराब कर्जा -> Non-Performing Loans, NPL, NPL ratio, Gross NPL, Table 1.2\n"
            "- कुल शाखा संख्या / शाखा -> Total branches, number of branches, Table 1.1, Structure of Financial Sector\n"
            "- प्रदेश अनुसार शाखा / कर्णाली प्रदेश -> Province-wise Branch Network, Karnali Province, DB branches, FC branches, Figure 1.2\n"
            "- नाफा / घाटा -> net profit, net loss\n"
            "Output 3-5 comma-separated official English terms, nothing else."
        )
    elif is_nepali and not is_report:
        sys_instruction = (
            "You are a specialized regulatory terminology engine for Nepal Rastra Bank Unified and Payment Directives.\n"
            "The user question is in Nepali seeking regulatory provisions, limits, and timelines from Nepali directives.\n"
            "Expand key regulatory concepts into their official NRB Devanagari terminology, clause references, and numerical caps:\n"
            "- वालेटबाट बैंक खातामा दैनिक फण्ड ट्रान्सफर सीमा -> वालेटबाट अन्य बैंक खातामा, २ लाख, १० लाख, प्रतिदिन, विद्युतीय वालेट\n"
            "- एजेन्टमार्फत वालेटमा नगद जम्मा -> आधिकारिक प्रतिनिधि, एजेन्ट, नगद जम्मा, २५ हजार, १ लाख, प्रतिदिन\n"
            "- एजेन्टमार्फत वालेटबाट नगद झिक्ने सीमा -> आधिकारिक प्रतिनिधि, एजेन्ट, नगद झिक्ने, ५ हजार, २५ हजार\n"
            "- वालेटमा अधिकतम ओभरनाइट मौज्दात -> ओभरनाइट मौज्दात, ५० हजार, ५०,०००, निक्षेप बैंक खाता\n"
            "- स्व-घोषणासम्बन्धी व्यवस्था -> सञ्चालक, स्वघोषणा, स्वःघोषणा, अनुसूची ११.१, १५ दिन\n"
            "- कालोसूचीमा परेको एजेन्टको कुलिङ पिरियड -> आधिकारिक प्रतिनिधि, एजेन्ट, कालोसूची, फुकुवा भएको कम्तीमा ३ वर्ष पूरा भएको, ३ वर्ष, स्वघोषणा\n"
            "- संस्थागत सुशासनसम्बन्धी व्यवस्था -> संस्थागत सुशासन, निर्देशन नं. ११, निर्देशन नं. ६, ११/०८२, ११/०८१\n"
            "- युएसएसडी भुक्तानी सीमा -> ग्क्क्म्, USSD, १०,०००, ५,०००, दैनिक रु.१०,०००, प्रति कारोबार रु.५,०००\n"
            "- व्यक्तिगत आवासीय घर कर्जाको अधिकतम सीमा -> व्यक्तिगत आवासीय घर कर्जा, ३ करोड, सीमा गणना गर्दा, रु. ३ करोड, ८० प्रतिशत\n"
            "- विफल कारोबार फिर्ता / दाबी फर्छ्यौट -> विफल कारोबार, दाबी फर्छ्यौट, Force Settlement, T+1, T+3, T+30, अर्को दिन, फिर्ता\n"
            "- सीमा कारोबार र शंकास्पद कारोबार -> सीमा कारोबार, त्त्च्, १० लाख, १५ दिन, शंकास्पद कारोबार, क्त्च्, ३ दिन, goAML\n"
            "- पुँजी पर्याप्तता फ्रेमवर्क -> Capital Adequacy Framework, जोखिम तौल, ६० प्रतिशत\n"
            "- सञ्चालक ऋण -> सञ्चालक कर्जा, लिन पाउने छैन, प्रतिबन्ध\n"
            "Output 3-6 comma-separated official Devanagari terms, nothing else."
        )
    elif not is_nepali and is_report:
        sys_instruction = (
            "You are a specialized banking terminology engine for Nepal Rastra Bank annual supervision reports.\n"
            "The user question is in English seeking statistical data or metrics from English Annual Reports.\n"
            "Expand key entities into their official report table references, section titles, and indicators:\n"
            "- debit cards issued by Development Banks -> Debit Cards, Development Banks, DBs, Table 3.6, Mid-July 2025, 1,216,322\n"
            "- mobile banking customers in Finance Companies -> Mobile Banking Customers, Finance Companies, FCs, Table 4.5, 294,739\n"
            "- total ATMs across all banks -> Total ATMs, Indicators Summary, Table 3.6, Table 4.5, 5,222\n"
            "- NPL ratio of Finance Companies vs Commercial Banks -> NPL ratio, Gross NPL, Table 1.2, Non-Performing Loans, Financial Soundness Indicators\n"
            "- total branches -> Total branches, number of branches, Table 1.1, Structure of Financial Sector\n"
            "- province-wise branches Karnali -> Province-wise Branch Network, Karnali Province, DB branches, FC branches, Figure 1.2\n"
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
            "- debit card / ATM cash withdrawal limit -> कार्डबाट नगद झिक्ने अधिकतम सीमा, डेबिट कार्ड, २५ हजार, १ लाख, ४ लाख, नगद झिक्ने, एटीएम\n"
            "- contactless -> Contactless, कन्ट्याक्टलेस, ५ हजार, ५,०००\n"
            "- blacklisted agent / previously blacklisted agent -> आधिकारिक प्रतिनिधि, एजेन्ट, कालोसूची, फुकुवा भएको कम्तीमा ३ वर्ष पूरा भएको, ३ वर्ष, स्वघोषणा\n"
            "- NPL ratio / non-performing loan ratio -> NPL ratio, Gross NPL, Table 1.2, Non-Performing Loans, Financial Soundness Indicators\n"
            "- total branches / branch count -> Total branches, number of branches, Table 1.1, Structure of Financial Sector\n"
            "- threshold and suspicious transaction / TTR and STR -> सीमा कारोबार, त्त्च्, १० लाख, १५ दिन, शंकास्पद कारोबार, क्त्च्, ३ दिन, goAML\n"
            "- real estate loan LTV / home loan LTV -> घरजग्गा तथा रियल स्टेट कर्जा, Loan to Value Ratio, ५० प्रतिशत, ७० प्रतिशत, ८० प्रतिशत, ३ करोड, First Home Buyer\n"
            "- failed transaction reversal / refund timeframe -> विफल कारोबार, दाबी फर्छ्यौट, Force Settlement, T+1, T+3, T+30, अर्को दिन, फिर्ता, Reversal, ATM, POS, QR\n"
            "- wallet to bank transfer limit -> वालेटबाट अन्य बैंक खातामा, २ लाख, १० लाख, विद्युतीय वालेट, अधिकतम सीमा, प्रतिदिन\n"
            "- finance companies letter of credit / LC import -> प्रतितपत्र, Letter of Credit, LC, वाणिज्य बैंकले जमानत तथा प्रतितपत्र जारी, ग वर्गका वित्तीय संस्था\n"
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

    # Query Intent Detection: Financial/Annual/Supervision Reports vs Regulatory Directives
    has_directive_intent = bool(re.search(
        r'\b(?:directive|clause|circular|limit|withdrawal|rules?|provision|guidelines?|eligibility|penalty|fines?|rates?|fees?)\b'
        r'|(?:निर्देशन|परिपत्र|बुँदा|दफा|व्यवस्था|प्रावधान|सीमा|झिक्ने|नोक्सानी|हर्जाना|नियम|शुल्क|ब्याजदर)',
        user_query,
        re.IGNORECASE
    ))

    is_report_query = (not has_directive_intent) and bool(re.search(
        r'\b(?:annual\s*report|supervision\s*report|supervision|balance\s*sheet|financial\s*position|financial\s*statement|total\s*assets|total\s*liabilities|commercial\s*bank\s*list|development\s*bank\s*list|growth\s*rate|overall\s*npl|npl\s*ratio|npl\s*percentage|total\s*branch(?:es)?|number\s*of\s*branches|number\s*of\s*customers|mobile\s*banking\s*customers|internet\s*banking\s*customers|total\s*atms?|indicators\s*summary)\b'
        r'|(?:वार्षिक\s*प्रतिवेदन|सुपरीवेक्षण|कुल\s*शाखा|शाखा\s*संख्या|प्रदेश\s*शाखा|शाखा\s*सञ्जाल|ग्राहक\s*संख्या|ग्राहकसंख्या|प्रयोग\s*गर्ने\s*ग्राहक)',
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

    # 1b. Directive Chapter Guided Dense Search (Guarantees target chapter chunks are in candidate pool)
    target_dir_num = extract_target_directive_number(user_query)
    if target_dir_num:
        cand_docs = [selected_doc] if isinstance(selected_doc, str) and selected_doc != "All Documents" else ([d for d in selected_doc] if isinstance(selected_doc, (list, set, tuple)) else ["Unified_directive_2082.pdf", "directive_2082.pdf"])
        for c_doc in cand_docs:
            p_ranges = get_directive_ranges_for_pdf(c_doc)
            if target_dir_num in p_ranges:
                p_start, p_end = p_ranges[target_dir_num]
                try:
                    c_query = table.search(q_vec).where(f"source = '{c_doc}' AND page >= {p_start} AND page <= {p_end}").limit(20)
                    for rank, (_, row) in enumerate(c_query.to_pandas().iterrows(), 1):
                        k = (row['source'], int(row['page']))
                        if k not in d_pri or d_pri[k][0] > rank:
                            d_pri[k] = (rank, row)
                except Exception:
                    pass

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

    # 3. Primary Sparse Inverted Index Search (Exact Native Term Matching with Domain Lexicon Expansion)
    s_pri = {}
    kw_pri = extract_meaningful_keywords(user_query)
    q_lower = user_query.lower()
    for lex_k, synonyms in BANKING_DOMAIN_LEXICON.items():
        if lex_k in q_lower or lex_k in kw_pri:
            for syn in synonyms:
                kw_pri.update(extract_meaningful_keywords(syn))

    clean_pri_fts = " ".join([normalize_devanagari(w) for w in kw_pri if len(w) > 1 or w in '०१२३४५६७८९0123456789'])
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
            clean_phrase = phrase.strip()
            fts_candidates = []
            if any(c in clean_phrase for c in '/.-+') or len(clean_phrase.split()) <= 2:
                fts_candidates.append(clean_phrase)
            kw_c = extract_meaningful_keywords(clean_phrase)
            c_fts = " ".join([w for w in kw_c if len(w) > 1 or w in '०१२३४५६७८९0123456789'])
            if c_fts and c_fts not in fts_candidates:
                fts_candidates.append(c_fts)

            for cand in fts_candidates:
                try:
                    s_t = table.search(cand)
                    if where_filter:
                        s_t = s_t.where(where_filter)
                    for rank, (_, row) in enumerate(s_t.limit(20).to_pandas().iterrows(), 1):
                        k = (row['source'], int(row['page']))
                        s_trans_scores[k] = s_trans_scores.get(k, 0.0) + (2.2 / (k_const + rank))
                        if k not in s_trans_rows:
                            s_trans_rows[k] = row
                except Exception:
                    pass

    # 5. RRF Fusion with Year Recency Boost & Directive-Aware Routing
    target_dir_num = extract_target_directive_number(user_query)
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
                score *= 0.35
        else:
            if is_bs and max_bs_year > 0 and doc_yr == max_bs_year:
                score *= 1.80
            elif is_bs and max_bs_year > 0 and doc_yr == max_bs_year - 1:
                score *= 0.75
            elif is_bs:
                score *= 0.40
            else:
                score *= 0.40

        # Directive-Aware Chapter Routing: If user specifically asks for Directive X, lock to that chapter dynamically
        if target_dir_num:
            pdf_ranges = get_directive_ranges_for_pdf(k[0])
            if target_dir_num in pdf_ranges:
                d_start, d_end = pdf_ranges[target_dir_num]
                chunk_page = k[1]
                if d_start <= chunk_page <= d_end:
                    score *= 5.0  # Strongly boost the exact target directive chapter
                else:
                    score *= 0.02  # Suppress wrong directive chapters so they never overshadow the target
            else:
                score *= 0.02  # Strongly suppress documents that do not have this directive chapter

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
                max_for_doc = 3 if is_prevailing else 1
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
    Robustly handles all markdown variations (bullet lists, bold, multiline, backticks).
    """
    cited = []
    seen = set()
    full_page_map = full_page_map or {}
    found_matches = []

    # 1. Broad Proximity Search for any known disk document name + Page number in the response
    known_docs = [f for f in os.listdir("File_System") if f.lower().endswith(('.pdf', '.docx', '.txt'))] if os.path.exists("File_System") else []
    for fname in known_docs:
        base_name = os.path.splitext(fname)[0]
        # Match filename or basename surrounded by word boundary or markdown characters
        pat = rf'(?:^|[\*\_`\s\(\[\{{ ])(?:{re.escape(fname)}|{re.escape(base_name)})(?:$|[\*\_`\s\)\]\}} ])'
        for m in re.finditer(pat, response_text, re.IGNORECASE):
            doc_start = m.start()
            doc_end = m.end()
            # Look in a window after the doc name (up to 200 chars) for page indicator
            window_after = response_text[doc_end:min(len(response_text), doc_end + 200)]
            pg_match = re.search(r'(?:page|पृष्ठ|p\.?)\s*[:\-–—\s\*\_]*(\d+)', window_after, re.IGNORECASE)
            if pg_match:
                page_num = int(pg_match.group(1))
                found_matches.append((doc_start, fname, page_num))
            else:
                # Also check window before (e.g. "Page 22 of directive_2082.pdf")
                window_before = response_text[max(0, doc_start - 100):doc_start]
                pg_match_before = re.search(r'(?:page|पृष्ठ|p\.?)\s*[:\-–—\s\*\_]*(\d+)', window_before, re.IGNORECASE)
                if pg_match_before:
                    page_num = int(pg_match_before.group(1))
                    found_matches.append((doc_start, fname, page_num))

    # 2. Standard Regex Patterns for inline citation blocks
    regex_patterns = [
        r'([a-zA-Z0-9_\-\.]+\.(?:pdf|docx|txt))(?:\s*[\:\|\-\–\—\(\)\[\]\*\_]?\s*|\s+(?:clause|section|दफा|खण्ड)\s*[^\n\r]{0,25}?\s*|\s*\n\s*\-?\s*\*\*?)(?:page|पृष्ठ|p\.?)\s*[:\-]?\s*(\d+)',
        r'(?:page|पृष्ठ|p\.?)\s*[:\-]?\s*(\d+)(?:\s*[\:\|\-\–\—\(\)\[\]\*\_]?\s*|\s*\n\s*\-?\s*\*\*?)(([a-zA-Z0-9_\-\.]+\.(?:pdf|docx|txt)))',
        r'\[\s*(?:कागजात|doc|document)?\s*[:\-]?\s*([a-zA-Z0-9_\-\.]+\.(?:pdf|docx|txt))\s*\|\s*(?:पृष्ठ|page)\s*[:\-]?\s*(\d+)\s*\]',
        r'([a-zA-Z0-9_\-]+(?:directive|report)[a-zA-Z0-9_\-]*)(?:\s*[\:\|\-\–\—\(\)\[\]\*\_]?\s*|\s*\n\s*\-?\s*\*\*?)(?:page|पृष्ठ|p\.?)\s*[:\-]?\s*(\d+)'
    ]

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

    # 3. Match against retrieved candidate chunks if page was mentioned anywhere in text
    norm_resp = re.sub(r'[\s_\-]+', ' ', response_text.lower())
    for item in retrieved_candidates:
        src = item['source']
        pg = str(item['page'])
        base_src = src.replace('.pdf', '').replace('.docx', '').replace('.txt', '')
        norm_base = re.sub(r'[\s_\-]+', ' ', base_src.lower())

        if src.lower() in response_text.lower() or base_src.lower() in response_text.lower() or norm_base in norm_resp:
            pg_pattern = rf'(?:page|पृष्ठ|p\.?)\s*[:\-–—\s\*\_]*{pg}\b'
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

    # 4. Fallback to top-1 primary search match if no explicit citation was found
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


# ---------------------------------------------------------------------------
# 5. INTENT CLARIFICATION & QUERY DISAMBIGUATION (0 GROQ TOKENS, DETERMINISTIC)
# ---------------------------------------------------------------------------

SPECIFIC_ANCHORS = [
    # Metrics, ratios, and limits
    r'\bltv\b', r'loan\s*to\s*value', r'एलटीभी', r'धितो\s*अनुपात',
    r'\bcrr\b', r'cash\s*reserve', r'अनिवार्य\s*नगद',
    r'\bslr\b', r'statutory\s*liquidity', r'वैधानिक\s*तरलता',
    r'\bturnover\b', r'वार्षिक\s*कारोबार', r'[०-९0-9]+\s*(?:करोड|लाख|हजार|crore|lakh|million)',
    r'kathmandu\s*valley', r'काठमाडौ[ंँ]?\s*उपत्यका',
    r'residential\s*home\s*loan', r'आवासीय\s*घर\s*कर्जा',
    r'first\s*home\s*buyer', r'पहिलो\s*घर',
    r'earthquake', r'भूकम्प',
    r'working\s*capital', r'चालू\s*पुँजी',
    r'non-banking\s*asset', r'\bnba\b.*?(?:बिक्री|वर्ष|limit|sale)', r'गैर-?बैंकिङ\s*सम्पत्ति',
    r'letter\s*of\s*credit', r'\blc\b', r'प्रतितपत्र', r'trust\s*receipt', r'ट्रष्ट\s*रिसिप्ट',
    r'cooling\s*period', r'कुलिङ\s*पिरियड', r'कालोसूची\s*(?:समय|अवधि|फुकुवा|criteria)',
    r'debit\s*card', r'डेबिट\s*कार्ड', r'atms?', r'एटीएम',
    r'base\s*rate', r'आधार\s*दर', r'spread\s*rate', r'स्प्रेड\s*दर',
    r'stress\s*test', r'तनाव\s*परीक्षण', r'prompt\s*corrective', r'शीघ्र\s*सुधारात्मक',
    # Specific compliance, multi-directive, and ratio anchors
    r'bad\s*loans?', r'खराब\s*कर्जा',
    r'\bnpl\b', r'\bnpa\b', r'non-?performing', r'निष्क्रि?य\s*कर्जा',
    r'substandard', r'कमसल',
    r'doubtful', r'शंकास्पद',
    r'pass\s*loans?', r'असल\s*कर्जा',
    r'loan\s*classification', r'कर्जा\s*वर्गीकरण',
    r'categories\s*of\s*(?:bad\s*)?loans?', r'प्रकार',
    r'loan\s*loss\s*provision(?:ing)?', r'कर्जा\s*नोक्सानी\s*व्यवस्था', r'नोक्सानी\s*व्यवस्था',
    r'restructur(?:ing|ed)', r'पुनर्संरचना',
    r'reschedul(?:ing|ed)', r'पुनर्तालिकीकरण',
    r'single\s*obligor', r'\bsol\b', r'एकल\s*ग्राहक',
    r'penal\s*interest', r'पेनाल\s*ब्याज', r'हर्जाना', r'fund\s*diversion', r'दुरुपयोग',
    r'microfinance', r'लघुवित्त', r'विपन्न\s*वर्ग', r"['\"]?d['\"]?\s*class", r'घ\s*वर्ग',
    r'tier\s*2', r'पूरक\s*पुँजी', r'supplementary\s*capital', r'watchlist', r'सूक्ष्म\s*निगरानी',
    r'ceo', r'प्रमुख\s*कार्यकारी', r'fixed\s*deposit', r'मुद्दती\s*(?:रसिद|निक्षेप)', r'premature',
    # Specific Directive numbers and explicit category anchors
    r'निर्देशन\s*नं\.?\s*[०-९0-9]+', r'\bdirective\s*[०-९0-9]+\b',
    r'एकीकृत\s*निर्देशन', r'unified\s*directive',
    r'भुक्तानी\s*(?:प्रणाली)?\s*निर्देशन', r'payment\s*directive',
    r'सुपरीवेक्षण\s*प्रतिवेदन', r'supervision\s*report',
    # Specific Calendar Dates (Bikram Sambat & Gregorian, both English & Devanagari numerals)
    r'\b(?:20[5-9][0-9]|२०[५-९][०-९])[/-](?:[0-9]{1,2}|[०-९]{1,2})[/-](?:[0-9]{1,2}|[०-९]{1,2})\b',
    r'\b(?:20[5-9][0-9]|२०[५-९][०-९])\s+(?:बैशाख|वैशाख|जेठ|ज्येष्ठ|असार|आषाढ|साउन|श्रावण|भदौ|भाद्र|असोज|आश्विन|कात्तिक|कार्तिक|मंसिर|मङ्सिर|पुस|पौष|माघ|फागुन|फाल्गुन|चैत|चैत्र|baisakh|jestha|jeth|ashad|shrawan|bhadra|asoj|kartik|mangsir|poush|magh|falgun|chaitra)\s+(?:[0-9]{1,2}|[०-९]{1,2})\b'
]

BROAD_TOPICS = {
    "kyc": {
        "pattern": r'^(?:kyc|cdd|केवाईसी|ग्राहक\s*पहिचान|kyc\s*(?:rules?|guidelines?|information)|ग्राहक\s*पहिचान\s*(?:सम्बन्धी|बारेमा|व्यवस्था))(?:\s*\?*)?$',
        "title": "ग्राहक पहिचान (KYC / Customer Due Diligence)",
        "message": "नेपाल राष्ट्र बैंकको निर्देशनमा **KYC (ग्राहक पहिचान)** सम्बन्धी व्यवस्था विभिन्न क्षेत्रमा फैलिएको छ। तपाईं विशेष गरी कुन विषयमा जानकारी चाहनुहुन्छ?",
        "options": [
            {"label": "📋 ग्राहक पहिचान (KYC) फाराम तथा आवश्यक कागजात", "query": "ग्राहक पहिचान KYC फाराम तथा खाता खोल्दा आवश्यक कागजातहरू के के हुन्?"},
            {"label": "🛡️ उच्च जोखिम तथा PEPs (Politically Exposed Persons) सम्बन्धी व्यवस्था", "query": "उच्च जोखिम ग्राहक तथा PEPs पहिचान र कारोबार सम्बन्धी व्यवस्था के छ?"},
            {"label": "⏰ ग्राहक विवरण आवधिक अद्यावधिक (Periodic Updating) गर्ने समयसीमा", "query": "ग्राहक पहिचान KYC विवरण कति समयमा अद्यावधिक (Update) गर्नुपर्छ?"},
            {"label": "📱 विद्युतीय ग्राहक पहिचान (e-KYC / Video KYC)", "query": "विद्युतीय माध्यमबाट ग्राहक पहिचान e-KYC तथा Video KYC सम्बन्धी व्यवस्था"}
        ]
    },
    "loan": {
        "pattern": r'^(?:loan|loans|credit|credits|कर्जा|सापट|ऋण|loans?\s*(?:rules?|policy|information)|कर्जा\s*(?:सम्बन्धी|बारेमा|व्यवस्था|नियम))(?:\s*\?*)?$',
        "title": "कर्जा तथा सापट सम्बन्धी व्यवस्था (Loans & Advances)",
        "message": "नेपाल राष्ट्र बैंकको **कर्जा (Loan)** सम्बन्धी निर्देशनहरू विभिन्न शीर्षकमा विभाजित छन्। तपाईं कुन कर्जाको विषयमा सोध्न चाहनुहुन्छ?",
        "options": [
            {"label": "🏠 व्यक्तिगत आवासीय घर कर्जा (Personal Residential Loan) सीमा र LTV", "query": "व्यक्तिगत आवासीय घर कर्जाको अधिकतम सीमा र LTV कति हो?"},
            {"label": "🎯 एकल ग्राहक कर्जा सीमा (Single Obligor Limit - SOL) कति प्रतिशत छ?", "query": "एकल ग्राहक कर्जा सीमा Single Obligor Limit कति प्रतिशत तोकिएको छ?"},
            {"label": "🚗 सवारी साधन कर्जा (Auto / Vehicle Loan) LTV सीमा", "query": "सवारी साधन खरिद कर्जाको LTV सीमा के कति छ?"},
            {"label": "📊 कर्जा नोक्सानी व्यवस्था तथा वर्गीकरण (NPL & Loan Loss Provision)", "query": "कर्जा वर्गीकरण र कर्जा नोक्सानी व्यवस्था Loan Loss Provision दरहरू के के हुन्?"}
        ]
    }
}

UNIFIED_DIRECTIVE_CHAPTERS = {
    1: {"name": "पुँजी कोष तथा जोखिम भारित सम्पत्ति (Capital Adequacy - CAR)", "short": "पुँजी कोष (CAR)", "keywords": ["पुँजी कोष", "capital adequacy", "risk weight", "जोखिम भारित", "tier 1", "tier 2", "प्राथमिक पुँजी", "पूरक पुँजी", "car"]},
    2: {"name": "कर्जा वर्गीकरण तथा नोक्सानी व्यवस्था (Loan Classification & Provisioning)", "short": "कर्जा वर्गीकरण तथा नोक्सानी", "keywords": ["कर्जा वर्गीकरण", "npl", "खराब कर्जा", "loan loss", "नोक्सानी व्यवस्था", "सूक्ष्म निगरानी", "भाखा नाघेको", "पेनाल ब्याज", "penal interest", "पुनरतालिकीकरण"]},
    3: {"name": "एकल ग्राहक कर्जा सीमा तथा सञ्चालक कर्जा (Single Obligor Limit)", "short": "एकल ग्राहक कर्जा सीमा (SOL)", "keywords": ["एकल ग्राहक", "single obligor", "sol", "सञ्चालक कर्जा", "पदाधिकारी कर्जा", "कन्सोर्टियम", "सह-वित्तीयकरण"]},
    4: {"name": "लेखा नीति तथा वित्तीय विवरण (Accounting Policies & Reporting)", "short": "लेखा नीति तथा वित्तीय विवरण", "keywords": ["लेखा नीति", "accounting", "nfrs", "वित्तीय विवरण", "नाफा नोक्सान", "वासलात"]},
    5: {"name": "जोखिम व्यवस्थापन मार्गदर्शन (Risk Management)", "short": "जोखिम व्यवस्थापन मार्गदर्शन", "keywords": ["जोखिम व्यवस्थापन", "risk management", "credit risk", "market risk", "operational risk", "तरलता जोखिम"]},
    6: {"name": "संस्थागत सुशासन तथा सञ्चालक योग्यता (Corporate Governance)", "short": "संस्थागत सुशासन तथा योग्यता", "keywords": ["संस्थागत सुशासन", "corporate governance", "सञ्चालकको योग्यता", "कार्यकारी प्रमुख", "ceo", "स्वतन्त्र सञ्चालक", "सञ्चालक समिति"]},
    7: {"name": "वैधानिक तरलता तथा अनिवार्य नगद (SLR & CRR)", "short": "वैधानिक तरलता (SLR) र अनिवार्य नगद (CRR)", "keywords": ["वैधानिक तरलता", "slr", "अनिवार्य नगद", "crr", "तरलता अनुपात", "liquidity"]},
    8: {"name": "सेयर तथा धितोपत्र लगानी (Investment in Shares & Securities)", "short": "सेयर तथा धितोपत्र लगानी सीमा", "keywords": ["सेयर लगानी", "धितोपत्र", "securities", "शेयर", "shares", "डिबेन्चर", "म्युचुअल फण्ड", "लगानी सीमा"]},
    9: {"name": "तथ्याङ्क तथा वित्तीय विवरण पेश गर्ने (Statistical Returns)", "short": "तथ्याङ्क तथा विवरण पेश गर्ने", "keywords": ["तथ्याङ्क", "विवरण पेश", "reporting", "returns", "राष्ट्र बैंकमा पठाउने"]},
    10: {"name": "गैर-बैंकिङ सम्पत्ति तथा शाखा (NBA & Branch Operations)", "short": "गैर-बैंकिङ सम्पत्ति (NBA) र शाखा", "keywords": ["गैर-बैंकिङ सम्पत्ति", "nba", "शाखा कार्यालय", "शाखा खोल्ने", "लिलाम", "सकार"]},
    11: {"name": "सञ्चालकको बैठक भत्ता तथा सुविधा (Board Remuneration & Facilities)", "short": "सञ्चालकको बैठक भत्ता तथा सुविधा", "keywords": ["बैठक भत्ता", "meeting fee", "सञ्चालकको भत्ता", "सञ्चालक सुविधा", "भ्रमण भत्ता"]},
    12: {"name": "कर्जा सूचना तथा कालोसूची (Credit Information & Blacklisting)", "short": "कर्जा सूचना तथा कालोसूची", "keywords": ["कर्जा सूचना", "कालोसूची", "blacklist", "cib", "कालोसूची फुकुवा", "कर्जा अपलेखन"]},
    13: {"name": "वित्तीय ग्राहक संरक्षण तथा गुनासो सुनुवाइ (Consumer Protection)", "short": "ग्राहक संरक्षण तथा गुनासो सुनुवाइ", "keywords": ["ग्राहक संरक्षण", "consumer protection", "गुनासो सुनुवाइ", "grievance"]},
    14: {"name": "शाखाविहीन बैंकिङ तथा निक्षेप परिचालन (Branchless Banking & Deposits)", "short": "शाखाविहीन बैंकिङ तथा निक्षेप", "keywords": ["शाखाविहीन", "branchless", "निक्षेप खाता", "deposit", "बचत खाता", "मुद्दती निक्षेप", "ब्याज गणना"]},
    15: {"name": "ब्याजदर, स्प्रेड दर तथा सेवा शुल्क (Interest Rates, Spread & Fees)", "short": "ब्याजदर, स्प्रेड दर तथा सेवा शुल्क", "keywords": ["ब्याजदर", "interest rate", "आधार दर", "base rate", "स्प्रेड दर", "spread", "सेवा शुल्क", "prepayment fee", "प्रिमियम"]},
    16: {"name": "वित्तीय साक्षरता (Financial Literacy)", "short": "वित्तीय साक्षरता", "keywords": ["वित्तीय साक्षरता", "financial literacy", "सचेतना"]},
    17: {"name": "विपन्न वर्ग कर्जा (Deprived Sector Lending)", "short": "विपन्न वर्ग कर्जा", "keywords": ["विपन्न वर्ग", "deprived sector", "घ वर्ग", "लघुवित्त", "microfinance"]},
    18: {"name": "कर्मचारी सेवा सर्त तथा सुविधा (Employee Bylaws & Facilities)", "short": "कर्मचारी सेवा सर्त तथा सुविधा", "keywords": ["कर्मचारी सेवा", "कर्मचारी सुविधा", "तालिम", "बोनस", "कर्मचारी सापटी"]},
    19: {"name": "सम्पत्ति शुद्धीकरण तथा ग्राहक पहिचान (AML/CFT & KYC)", "short": "सम्पत्ति शुद्धीकरण (AML) तथा KYC", "keywords": ["सम्पत्ति शुद्धीकरण", "aml", "kyc", "ग्राहक पहिचान", "cdd", "pep", "उच्च जोखिम"]},
    20: {"name": "वित्तीय मध्यस्थता तथा एजेन्सी (Agent Operations)", "short": "वित्तीय मध्यस्थता तथा एजेन्सी", "keywords": ["वित्तीय मध्यस्थता", "एजेन्ट", "व्यावसायिक प्रतिनिधि"]},
    21: {"name": "अन्य विविध व्यवस्था (Miscellaneous)", "short": "विविध व्यवस्था", "keywords": ["विविध व्यवस्था", "miscellaneous"]}
}

VERIFIED_SUGGESTION_PROMPTS = [
    {"label": "🏠 व्यक्तिगत आवासीय घर कर्जाको अधिकतम सीमा र LTV कति हो?", "query": "व्यक्तिगत आवासीय घर कर्जाको अधिकतम सीमा कति हो?"},
    {"label": "🎯 एकल ग्राहक कर्जा सीमा (Single Obligor Limit - SOL) कति प्रतिशत छ?", "query": "एकल ग्राहक कर्जा सीमा Single Obligor Limit कति प्रतिशत तोकिएको छ?"},
    {"label": "📊 Finance Companies को लागि Minimum CRR र SLR कति छ?", "query": "Minimum CRR and SLR requirement for finance companies?"},
    {"label": "🏢 गैर-बैंकिङ सम्पत्ति (NBA) कति वर्षभित्र बिक्री गर्नुपर्छ?", "query": "गैर-बैंकिङ सम्पत्ति (NBA) कति वर्षभित्र बिक्री गर्नुपर्छ?"},
    {"label": "📜 वित्त कम्पनीले अन्तर्राष्ट्रिय प्रतितपत्र (Import LC) जारी गर्न पाउँछ?", "query": "Can finance companies issue international import Letters of Credit (LC)?"},
    {"label": "📱 वालेटबाट बैंक खातामा दैनिक फण्ड ट्रान्सफर कारोबार सीमा के छ?", "query": "वालेटबाट बैंक खातामा दैनिक फण्ड ट्रान्सफर कारोबार सीमा के छ?"}
]

UNCLEAR_QUERY_PATTERNS = [
    r'^(?:hi|hello|hey|namaste|नमस्ते|नमस्कार|प्रणाम)(?:\s|$|[?,.!])',
    r'^(?:what|tell me|explain|how|why|can you|कस्तो|के|किन|कसरी|भन्नुस्|जानकारी)\s*[\?\.]*$',
    r'^(?:rule|rules|guideline|guidelines|policy|policies|limit|limits|provision|provisions|नियम|नीति|निर्देशन|व्यवस्था|सीमा)\s*[\?\.]*$'
]

def is_specific_query(query: str) -> bool:
    """Checks if the query contains concrete regulatory anchors ensuring safe fast-tracking."""
    q_lower = query.lower()
    for pat in SPECIFIC_ANCHORS:
        if re.search(pat, q_lower, re.IGNORECASE):
            return True
    return False

def extract_matched_chapters_from_chunks(chunks: list) -> list:
    """Detects which Unified Directive chapters are represented in retrieved chunks using headings and keywords."""
    chapter_scores = {}
    nep_map = {'०':'0','१':'1','२':'2','३':'3','४':'4','५':'5','६':'6','७':'7','८':'8','९':'9'}
    for c in chunks:
        text = c.get('text', '')
        m = re.search(r'निर्देशन\s*नं\.?\s*([०-९0-9]+)', text)
        if m:
            num_str = "".join(nep_map.get(ch, ch) for ch in m.group(1))
            try:
                num = int(num_str)
                if num in UNIFIED_DIRECTIVE_CHAPTERS:
                    chapter_scores[num] = chapter_scores.get(num, 0) + 5
            except Exception:
                pass
        t_lower = text.lower()
        for ch_num, ch_data in UNIFIED_DIRECTIVE_CHAPTERS.items():
            matches = sum(1 for kw in ch_data["keywords"] if kw.lower() in t_lower)
            if matches > 0:
                chapter_scores[ch_num] = chapter_scores.get(ch_num, 0) + matches

    sorted_chapters = sorted(chapter_scores.items(), key=lambda x: x[1], reverse=True)
    return [(num, UNIFIED_DIRECTIVE_CHAPTERS[num]["short"]) for num, score in sorted_chapters if score >= 2]

def detect_query_disambiguation(query: str, retrieved_chunks: list, selected_cat: str = "all") -> tuple[bool, dict | None]:
    """
    Intelligently determines whether a query is broad/ambiguous across directives or sub-topics.
    Complete 4-Step Decision Tree:
    1. Specificity Fast-Track (Safe, zero regression)
    2. Low-Confidence Suggestion (Did you mean?)
    3. Broad Topic & Cross-Category Smart Direct Options (1-Click Combined Category + Chapter)
    4. Intra-Document Chapter Disambiguation (Single Document / Category multi-chapter match)
    Runs 100% locally in Python (0 Groq tokens, < 1ms latency).
    """
    clean_q = query.strip()
    words = clean_q.split()

    # Step 1: Specificity Fast-Track (Never block clear, well-formed queries)
    if is_specific_query(clean_q):
        return False, None

    # Step 2: Low-Confidence / Unclear Question Check (Empty results, greeting, or fragmented query)
    is_unclear = any(re.search(pat, clean_q, re.IGNORECASE) for pat in UNCLEAR_QUERY_PATTERNS)
    if not retrieved_chunks or len(clean_q) < 3 or is_unclear:
        return True, {
            "type": "suggestion",
            "title": "स्पष्टता आवश्यक (Suggested Prompts)",
            "message": "तपाईंको प्रश्नअनुसार स्पष्ट नियामकीय व्यवस्था पहिचान हुन सकेन। के तपाईं निम्न प्रमुख नियामकीय विषयबारे जानकारी खोज्दै हुनुहुन्छ?",
            "options": VERIFIED_SUGGESTION_PROMPTS[:4]
        }

    # Step 3A: Known Broad Topic patterns (e.g. user types just 'kyc' or 'loan')
    q_lower = clean_q.lower()
    for topic_key, topic_data in BROAD_TOPICS.items():
        if re.search(topic_data["pattern"], q_lower) and len(words) <= 4:
            return True, {
                "type": "broad_topic",
                "title": topic_data["title"],
                "message": topic_data["message"],
                "options": topic_data["options"]
            }

    # Step 3B: Smart Direct Options (Cross-Category & Multi-Chapter Unified in 1 Click)
    if selected_cat == "all" and retrieved_chunks and len(words) <= 6:
        from core.ingestion import categorize_file
        top_slice = retrieved_chunks[:8]
        cat_chunks = {}
        for c in top_slice:
            cat = categorize_file(c.get('source', ''), c.get('text', ''))
            cat_chunks.setdefault(cat, []).append(c)

        active_cats = [cat for cat, chks in cat_chunks.items() if len(chks) >= 2 and cat in ('unified', 'payment', 'report')]
        if len(active_cats) >= 2:
            combined_options = []

            # 1. Payment Category Option
            if 'payment' in active_cats:
                combined_options.append({
                    "label": "📱 भुक्तानी प्रणाली निर्देशन (Payment Directives - वालेट, QR तथा कार्ड)",
                    "category": "payment",
                    "query": f"{clean_q} (भुक्तानी प्रणाली निर्देशन)"
                })

            # 2. Supervision / Annual Report Option
            if 'report' in active_cats:
                combined_options.append({
                    "label": "📊 वार्षिक / सुपरीवेक्षण प्रतिवेदन (Supervision & Annual Reports)",
                    "category": "report",
                    "query": f"{clean_q} (सुपरीवेक्षण प्रतिवेदन)"
                })

            # 3. Unified Directives - Extract specific chapters directly from the document
            unified_chunks = cat_chunks.get('unified', [])
            if unified_chunks:
                matched_chapters = extract_matched_chapters_from_chunks(unified_chunks)
                if matched_chapters:
                    slots = max(1, 4 - len(combined_options))
                    for ch_num, ch_name in matched_chapters[:slots]:
                        combined_options.append({
                            "label": f"🏦 एकीकृत निर्देशन (अध्याय {ch_num}): {ch_name}",
                            "category": "unified",
                            "query": f"{clean_q} निर्देशन नं. {ch_num}"
                        })
                else:
                    combined_options.append({
                        "label": "🏦 एकीकृत निर्देशन (Unified Directives - बैंकिङ तथा कर्जा कारोबार)",
                        "category": "unified",
                        "query": f"{clean_q} (एकीकृत निर्देशन)"
                    })

            if len(combined_options) >= 2:
                return True, {
                    "type": "cross_category",
                    "title": "सटीक विषय छनोट (Select Specific Regulation)",
                    "message": f"तपाईंको प्रश्न '**{clean_q}**' नेपाल राष्ट्र बैंकका विभिन्न निर्देशन तथा अध्यायहरूमा समेटिएको छ। कृपया तपाईंले हेर्न चाहनुभएको विषय छनोट गर्नुहोस् वा (specific) प्रश्न सोध्नुहोस:",
                    "options": combined_options[:4]
                }

    # Step 4: Intra-Document Chapter Disambiguation (Single Document / Category multi-chapter match)
    if len(words) <= 4:
        top_slice = retrieved_chunks[:8]
        matched_chapters = extract_matched_chapters_from_chunks(top_slice)
        if len(matched_chapters) >= 2:
            chapter_options = []
            for num, name in matched_chapters[:4]:
                chapter_options.append({
                    "label": f"📖 एकीकृत निर्देशन (अध्याय {num}): {name}",
                    "category": "unified",
                    "query": f"{clean_q} निर्देशन नं. {num}"
                })
            return True, {
                "type": "intra_chapter",
                "title": "निर्देशन अध्याय छनोट (Select Specific Chapter)",
                "message": f"एकीकृत निर्देशनभित्र '**{clean_q}**' सम्बन्धी व्यवस्था निम्न फरक-फरक शीर्षकहरूमा उल्लेख छ। तपाईं कुन व्यवस्था हेर्न चाहनुहुन्छ?",
                "options": chapter_options
            }

    return False, None
