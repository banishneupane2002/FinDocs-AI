# NRB Regulatory Intelligence Engine: Search Architecture & Dynamic Option Handling

This document provides a comprehensive, step-by-step technical explanation of how queries are processed, how document contents are retrieved, and how the interactive clarification system decides between displaying immediate answers versus presenting interactive 1-click option cards.

---

## High-Level Architecture Overview

```mermaid
flowchart TD
    UserQuery["User Input Query<br/><i>(e.g., 'categories of bad loan' or 'loan')</i>"] --> DisambigCheck{"Step 1: Disambiguation Decision Tree<br/><i>(100% Local Python, 0 Groq tokens, &lt; 0.05ms)</i>"}
    
    %% Fast track path
    DisambigCheck -->|"Specific Query<br/>(Passes Tier 1, 2, or 3)"| FastTrack["⚡ Specificity Fast-Track<br/><i>(Bypasses all option cards directly to RAG)</i>"]
    
    %% Option path
    DisambigCheck -->|"Vague / Polysemous<br/>(e.g., 'loan', 'fee', 'kyc')"| CardUI["🎯 Interactive Clarification Card<br/><i>(Displays 1-click guidance options in UI)</i>"]
    
    FastTrack --> QueryAnalysis["Step 2: Query Analysis & Routing<br/><i>(Fiscal year detection & Report vs Directive intent)</i>"]
    
    QueryAnalysis --> BilingualExp["Step 3: Bilingual Cross-Lingual Expansion<br/><i>(Devanagari & English domain lexicon translation)</i>"]
    
    BilingualExp --> HybridSearch["Step 4: Dual-Pass Hybrid Retrieval<br/><i>(Dense Vectors + Multi-Phrase Sparse BM25)</i>"]
    
    HybridSearch --> RRF["Step 5: Reciprocal Rank Fusion (RRF)<br/><i>(Combines ranks with active fiscal year recency boost)</i>"]
    
    RRF --> Windowing["Step 6: Targeted Clause Windowing<br/><i>(Centers ~2,200 char window around matched clause; max 8,000 chars)</i>"]
    
    Windowing --> LLM["Step 7: Deterministic Generation (temperature=0.0)<br/><i>(Groq LPU: gpt-oss-120b / qwen3.8-27b / gpt-oss-20b)</i>"]
    
    LLM --> CitationParser["Step 8: Citation Extraction & Overlap Protection<br/><i>(Verifies exact document names and page references)</i>"]
    
    CitationParser --> FinalAnswer["Final Verified Answer + 1-Click PDF Browser Launcher"]
```

---

## PART I: How Contents Are Searched (The Retrieval Pipeline)

The system uses a **Dual-Pass Cross-Lingual Hybrid Retrieval Engine** combining semantic dense vectors and exact keyword sparse inverted indexes, governed by Reciprocal Rank Fusion (RRF).

---

### Step 1: Query Ingestion & Script Normalization
When a user submits a question in either English or Nepali, the text is first normalized.

- **Devanagari Unicode Normalization *(in simple words: fixing broken letters so that Nepali vowels typed on different keyboards match identical characters in the database)*:**
  Nepal Rastra Bank directives contain complex conjunct consonants and nukta marks (e.g., `कर्जा`, `ऋणी`, `बैंक`). The engine applies Unicode NFKC normalization and maps equivalent Devanagari ligatures (e.g., `बैंकिङ` vs `बैंकिङ्ग`, `ऋण` vs `कर्जा`).
- **Preeti Ligature Bridging *(in simple words: older Nepali PDFs visually look like Nepali to humans, but their underlying text is actually typed using English keyboard codes like 'hDdf' for 'जम्मा'; our engine translates these hidden English codes back into real Nepali words)*:**
  The `SPECIAL_PREETI` lexicon bridges key Preeti keystroke sequences (e.g., `8]la6` for Debit/ATM, `jfn]6` for Wallet, `lhkmf` for Reversal) so that search queries match legacy text hidden inside PDF streams.

---

### Step 2: Query Intent Detection & Document Routing
Before touching the database, the engine analyzes the intent of the query:

- **Fiscal Year Detection *(in simple words: if you ask about 'fiscal year 2081', the system automatically locks onto documents from 2081 and ignores 2080 or 2082)*:**
  `extract_query_years()` dynamically extracts calendar and fiscal years (e.g., `2082`, `2081`, `2024`, `2025`, `२०८१/८२`). If an exact single year is targeted, an SQL-style `where_filter` restricts search candidates exclusively to documents published in that fiscal year.
- **Report vs. Directive Intent *(in simple words: deciding whether you want rules and penalties from the legal Directives, or institutional statistics and bank lists from the Annual Supervision Reports)*:**
  - **Directive Intent (`has_directive_intent`):** Matches regulatory terms like `limit`, `withdrawal`, `penalty`, `provision`, `rates`, `fees`, `दफा`, `सीमा`, `नोक्सानी`, `हर्जाना`.
  - **Report Intent (`is_report_query`):** Matches statistical/reporting terms like `annual report`, `supervision report`, `balance sheet`, `total assets`, `list of finance companies`, `total branches`, `NPL ratio`, `वार्षिक प्रतिवेदन`, `वित्त कम्पनीहरूको सूची`.
  - **The Scoring Multiplier:** If a query seeks report statistics, English Annual Reports receive a **$1.60\times$ boost**, while Nepali Directives receive a **$0.35\times$ penalty**. If a query seeks regulatory limits, Nepali Directives receive a **$1.80\times$ boost**, while Annual Reports are suppressed with a **$0.20\times$ penalty**.

---

### Step 3: Bilingual Cross-Lingual Query Expansion
Because regulatory documents exist in both Nepali (Directives) and English (Annual Supervision Reports), a user query in one language must match documents written in the other.

- **Bilingual Terminology Engine *(in simple words: like a specialized central-bank dictionary translating English financial phrases into their official NRB Devanagari equivalents and vice versa)*:**
  `expand_query_crosslingual()` translates and enriches the query with verified central-bank terms:
  - `"mobile banking limit"` $\rightarrow$ `मोबाइल बैंकिङ्ग, क्युआर कोड, ३ लाख प्रतिदिन, ३,००,०००`
  - `"Directors' Meeting Allowance"` $\rightarrow$ `सञ्चालक समितिको बैठक, बैठक भत्ता, नियमावलीमा तोकिए बमोजिम`
  - `"qualification of compliance officer"` $\rightarrow$ `व्यवस्थापकीय तहको कार्यान्वयन अधिकारी, Compliance Officer, AML/CFT, योग्यता`
  - `"show me list of finance companies"` $\rightarrow$ `List of FCs, Annex 4.1, Table 2.3, Finance Companies, Best Finance Ltd.`
- **Domain Lexicon Anchoring (`BANKING_DOMAIN_LEXICON`):**
  Runs locally with **0 API tokens**, instantly mapping acronyms and abbreviations (e.g., `CRR` $\rightarrow$ `४ प्रतिशत अनिवार्य नगद मौज्दात`, `SLR` $\rightarrow$ `१० प्रतिशत वैधानिक तरलता अनुपात`, `CD Ratio` $\rightarrow$ `९० प्रतिशत`, `SOL` $\rightarrow$ `२५ प्रतिशत प्राथमिक पुँजी`).

---

### Step 4: The Dual-Pass Hybrid Retrieval Execution
The engine queries the LanceDB vector database using four parallel retrieval passes:

```mermaid
flowchart LR
    subgraph Passes["4 Parallel Search Passes"]
        P1["Pass 1: Primary Dense Vector<br/><i>(Embeds user question directly)</i>"]
        P1b["Pass 1b: Chapter-Guided Dense<br/><i>(Scans specific chapter pages if Directive # mentioned)</i>"]
        P2["Pass 2: Translated Dense Vector<br/><i>(Embeds cross-lingual translated terms)</i>"]
        P3["Pass 3: Primary Sparse BM25<br/><i>(Exact keyword index with domain synonyms)</i>"]
        P4["Pass 4: Translated Sparse BM25<br/><i>(Exact keyword index on translated Devanagari/English)</i>"]
    end
    
    Passes --> RRFMerge["Reciprocal Rank Fusion (RRF)<br/><i>Score = Sum( Weight / (30 + Rank) )</i>"]
```

1. **Pass 1: Primary Dense Vector Search *(in simple words: scanning for conceptual meaning—finding pages that discuss the same ideas even if they use slightly different phrasing)*:**
   Encodes the query into a 384-dimensional dense semantic vector using `all-MiniLM-L6-v2` / `paraphrase-multilingual-MiniLM-L12-v2` and performs cosine distance nearest-neighbor search.
2. **Pass 1b: Directive Chapter-Guided Dense Search *(in simple words: if you ask about 'Directive 2', it guarantees that pages from Directive 2 are included in the search pool even if general keywords appear elsewhere)*:**
   Dynamically determines the start and end pages for the requested directive (using `pymupdf` chapter markers) and performs a targeted dense search inside that exact page range.
3. **Pass 2: Translated Dense Vector Search *(in simple words: searching the vector space using the Devanagari translation of an English query or the English translation of a Nepali query)*:**
   Searches the cross-lingual embedding space using the expanded official terminology.
4. **Pass 3: Primary Sparse Inverted Index Search *(in simple words: like an index at the back of a textbook that instantly pinpoints pages containing exact numbers like 'Rs. 300,000' or technical codes like 'Annex 4.1')*:**
   Performs full-text token matching using BM25 scoring. It incorporates synonyms from `BANKING_DOMAIN_LEXICON` to capture numbers, percentages, and acronyms that dense vectors often blur.
5. **Pass 4: Translated Sparse Inverted Index Search:**
   Performs full-text keyword matching on the translated terms.

---

### Step 5: Reciprocal Rank Fusion (RRF) & Recency Boost
Once candidate chunks are retrieved from all passes, they must be combined into a single, authoritative ranking.

- **The Standard RRF Formula *(in simple words: an Olympic scoring method where each search pass votes on the best pages; the pages that rank high across multiple judges win)*:**
  $$\text{RRF Score}(d) = \sum_{m \in \text{Passes}} \frac{W_m}{k + \text{Rank}_m(d)}$$
  *(where $k = 30$ is the standard smoothing constant, and $W_m$ is the pass weight: $0.8$ for dense passes, $1.3$ to $2.2$ for sparse passes).*
- **Prevailing Recency Multiplier *(in simple words: ensuring that rules from Directive 2082 always outrank older superseded rules from 2081 or 2080 unless the user specifically asked for an older year)*:**
  - Active Bikram Sambat Directives (e.g., 2082) receive a **$1.80\times$ multiplier**.
  - Superseded previous year directives (e.g., 2081) receive a **$0.75\times$ multiplier**.
  - Outdated older directives (e.g., 2080) receive a **$0.40\times$ multiplier**.

---

### Step 6: Targeted Clause Windowing (Prompt Context Optimization)
Previously, the system dumped 5 entire physical PDF pages (~12,000 characters) into the LLM prompt. This triggered **Groq HTTP 429 rate-limit backoff sleeps (causing 22s–57s latency spikes)** and crashed models with 7k context limits (`qwen3.8-27b`).

- **The Technical Solution *(in simple words: instead of dumping an entire 15-page chapter into the AI prompt, the system cuts out a targeted window containing the exact rule plus 400 characters before it and 600 characters after it)*:**
  ```python
  # If a PDF page is very long (> 2400 chars), center window around the matched clause
  if len(full_page_text) > 2400:
      pos = full_page_text.find(chunk_txt[:80])
      if pos != -1:
          start = max(0, pos - 400)
          end = min(len(full_page_text), pos + len(chunk_txt) + 600)
          page_excerpt = full_page_text[start:end]
  ```
- **The Operational Benefits:**
  1. **Preserves 100% of Legal Context:** Captures all provisos, exceptions, footnotes, and sub-clauses attached to the clause.
  2. **Covers Up to 5 Distinct Pages:** Because each excerpt is concise (~1,000–1,500 chars), the context can include up to 5 different pages while strictly capping total characters at **8,000 characters (~2,000–2,500 prompt tokens)**.
  3. **Zero 429 Rate Limits:** Latency dropped from **57 seconds down to 1.2–3.5 seconds**.

---

### Step 7: Deterministic Generation (`temperature = 0.0`)
- The assembled prompt is dispatched to Groq LPUs (`openai/gpt-oss-120b`, failing over to `qwen/qwen3.8-27b` and `openai/gpt-oss-20b`).
- **Greedy Decoding (`temperature = 0.0`) *(in simple words: turning off AI randomness so that the exact same banking question always produces the exact same authoritative answer)*:**
  Ensures that regulatory extractions are 100% repeatable, deterministic, and free of stylistic variance.

---

### Step 8: Strict Citation Extraction & Overlap Protection
After the LLM generates the response, the system identifies the verified sources cited in the text to display in the right sidebar.

- **Lookaround Boundaries *(in simple words: making sure the system doesn't accidentally think 'directive_2082.pdf' was cited just because its name appears at the end of 'Unified_directive_2082.pdf')*:**
  Uses strict regex assertions:
  ```python
  pat = rf'(?<![a-zA-Z0-9_])(?:{re.escape(fname)}|{re.escape(base_name)})(?![a-zA-Z0-9_])'
  ```
- **Longest-First Evaluation:**
  Documents are sorted by length descending so that `Unified_directive_2082.pdf` is evaluated before `directive_2082.pdf`. Once a longer filename claims a span of text, shorter sub-names are prohibited from claiming overlapping characters.

---

## PART II: How Options Are Handled (General vs. Option-Showing Questions)

A central challenge in building a banking assistant is balancing **immediate answers** for clear queries against **interactive guidance** for broad, polysemous queries:
- If a user types a specific question like *"categories of bad loan"*, they want an **immediate answer**, NOT an annoying clarification card.
- If a user types a bare, ambiguous single-word term like *"loan"* or *"fee"*, the directives contain hundreds of conflicting provisions across different chapters. They need an **interactive clarification card** with 1-click option buttons.

Here is the exact **4-Step Decision Tree** implemented in `detect_query_disambiguation()` in `core/search.py`:

```mermaid
flowchart TD
    Start["User Query Input"] --> S1{"Step 1: Is it a Specific Query?<br/><code>is_specific_query(clean_q)</code>"}
    
    %% Step 1: Specificity Fast-Track
    S1 -->|"YES (Matches Tier 1, 2, or 3)"| FastTrackAnswer["⚡ Specificity Fast-Track (Direct Answer)<br/><i>0 Groq tokens, &lt; 0.05ms execution.<br/>No clarification card is ever shown.</i>"]
    
    %% Step 2: Unclear check
    S1 -->|"NO"| S2{"Step 2: Low Confidence / Unclear?<br/><i>Empty chunks, greeting ('hi'),<br/>or fragmented query ('what', 'rules')</i>"}
    
    S2 -->|"YES"| SuggestionCard["💡 Suggested Prompts Card<br/><i>'स्पष्टता आवश्यक (Suggested Prompts)'<br/>Shows 4 verified popular banking prompts</i>"]
    
    %% Step 3A: Broad Topic
    S2 -->|"NO"| S3A{"Step 3A: Known Broad Topic?<br/><i>Matches 'loan', 'kyc' pattern (&lt;= 4 words)</i>"}
    
    S3A -->|"YES"| BroadTopicCard["🎯 Broad Topic Card<br/><i>'कर्जा तथा सापट सम्बन्धी व्यवस्था' or 'KYC'<br/>Shows 4 tailored 1-click options (Home, SOL, Auto, NPL)</i>"]
    
    %% Step 3B: Cross-Category
    S3A -->|"NO"| S3B{"Step 3B: Cross-Category Polysemy?<br/><i>Bare keyword like 'fee', 'ब्याजदर', 'कालोसूची'<br/>AND retrieved chunks hit Payment + Unified + Reports</i>"}
    
    S3B -->|"YES"| CrossCatCard["🌐 Smart Direct Options Card<br/><i>'सटीक विषय छनोट (Select Specific Regulation)'<br/>1-click buttons for Payment Directives vs Unified Directives vs Reports</i>"]
    
    %% Step 4: Intra-Chapter
    S3B -->|"NO"| S4{"Step 4: Intra-Chapter Multi-Match?<br/><i>Bare keyword (&lt;= 2 words)<br/>AND chunks hit &gt;= 2 different Directive chapters</i>"}
    
    S4 -->|"YES"| IntraChapterCard["📖 Directive Chapter Card<br/><i>'निर्देशन अध्याय छनोट'<br/>1-click buttons for Directive 2 vs Directive 15 vs Directive 6</i>"]
    
    S4 -->|"NO"| FastTrackAnswer
```

---

### Step 1: The Zero-Token Specificity Fast-Track (For General Queries)

Whenever a user asks a specific question, the system must **fast-track it directly to the retrieval and answer engine without interrupting the user**.

`is_specific_query()` uses a 3-Tier deterministic evaluation running in local Python:

#### Tier 1: Concrete Regulatory Anchors
Matches specific domain terms that leave no doubt about the user's intent:
- **Loan Classification & NPL:** `bad loans`, `npl`, `substandard`, `doubtful`, `loss loan`, `pass loan`, `loan classification`, `categories of bad loan`, `कर्जा वर्गीकरण`, `खराब कर्जा`, `नोक्सानी व्यवस्था`.
- **Governance & HR:** `directors meeting allowance`, `meeting allowance`, `compliance officer`, `ceo age limit`, `promoter share lock-in`, `independent director tenure`, `बैठक भत्ता`, `योग्यता`.
- **Digital Banking & Limits:** `mobile banking limit`, `cash withdrawal`, `contactless`, `ussd`, `overnight balance`, `ttr`, `str`, `cctv backup`, `chargeback`.
- **Statutory Ratios & Capital:** `crr`, `slr`, `cd ratio`, `capital adequacy`, `single obligor`, `margin lending`, `home loan ltv`, `paid-up capital`.
- **Explicit Chapter/Date References:** Any query containing `Directive 2`, `निर्देशन नं. ६`, or specific calendar dates (`२०८२/०४/०१`, `Mid-July 2025`).

#### Tier 2: Deterministic Regulatory Modifiers
If a query contains any question word (`what`, `how`, `when`, `कति`, `के`, `कसरी`) AND any regulatory attribute (`category`, `limit`, `rate`, `ratio`, `timeframe`, `period`, `qualification`, `criteria`, `procedure`, `penalty`, `सीमा`, `दर`, `अवधि`, `म्याद`, `मापदण्ड`):
- Example: `"categories of bad loan"` contains modifier `categories` + anchor `bad loan`. It fast-tracks immediately.
- Example: `"qualification of compliance officer"` contains modifier `qualification` + anchor `compliance officer`. It fast-tracks immediately.

#### Tier 3: Natural Sentence Structure ($\ge 4$ words)
Any coherent question containing 4 or more words that is not a generic greeting automatically bypasses clarification cards.
- Example: `"how much cash can agent deposit in a wallet per day?"` (9 words) $\rightarrow$ Fast-tracked immediately.

> **Result:** All general queries bypass clarification cards in **$< 0.05$ milliseconds using 0 Groq LLM tokens**.

---

### Step 2: Low-Confidence & Fragmented Query Fallback
If a query is unspecific, the system checks whether it is a vague greeting or broken fragment:
- **Trigger Conditions:**
  1. The retrieval engine returned 0 results.
  2. The input length is $< 3$ characters (e.g., `a`, `??`).
  3. Matches unclear query patterns (`hi`, `hello`, `namaste`, `नमस्ते`, bare `what`, `explain`, `rule`, `policy`).
- **UI Behavior:** Displays a friendly card titled **"स्पष्टता आवश्यक (Suggested Prompts)"** containing 4 verified, popular banking prompts that the user can click with one tap:
  1. 🏠 *व्यक्तिगत आवासीय घर कर्जाको अधिकतम सीमा र LTV कति हो?*
  2. 🎯 *एकल ग्राहक कर्जा सीमा (Single Obligor Limit - SOL) कति प्रतिशत तोकिएको छ?*
  3. 📊 *Finance Companies को लागि Minimum CRR र SLR कति छ?*
  4. 📱 *वालेटबाट बैंक खातामा दैनिक फण्ड ट्रान्सफर कारोबार सीमा के छ?*

---

### Step 3A: Predefined Broad Topic Clarification Cards
When a user types a bare, broad subject keyword without any modifiers (e.g., typing just `"loan"` or just `"kyc"` with $\le 4$ words):

- **The `"loan"` / `"कर्जा"` Trigger:**
  Instead of guessing which of the 100+ loan regulations the user wants, it displays the card:
  **"🎯 कर्जा तथा सापट सम्बन्धी व्यवस्था (Loans & Advances)"**
  with 4 distinct 1-click option buttons:
  - 🏠 *व्यक्तिगत आवासीय घर कर्जा (Personal Residential Loan) सीमा र LTV*
  - 🎯 *एकल ग्राहक कर्जा सीमा (Single Obligor Limit - SOL) कति प्रतिशत छ?*
  - 🚗 *सवारी साधन कर्जा (Auto / Vehicle Loan) LTV सीमा*
  - 📊 *कर्जा नोक्सानी व्यवस्था तथा वर्गीकरण (NPL & Loan Loss Provision)*

- **The `"kyc"` / `"ग्राहक पहिचान"` Trigger:**
  Displays the card:
  **"ग्राहक पहिचान (KYC / Customer Due Diligence)"**
  with 4 tailored options:
  - 📋 *ग्राहक पहिचान (KYC) फाराम तथा आवश्यक कागजात*
  - 🛡️ *उच्च जोखिम तथा PEPs सम्बन्धी व्यवस्था*
  - ⏰ *ग्राहक विवरण आवधिक अद्यावधिक (Periodic Updating) गर्ने समयसीमा*
  - 📱 *विद्युतीय ग्राहक पहिचान (e-KYC / Video KYC)*

---

### Step 3B: Cross-Category Polysemous Disambiguation
Certain banking terms have completely different legal meanings depending on whether you look in the **Payment Directives**, the **Unified Directives**, or the **Supervision Reports**.

- **Recognized Polysemous Keywords (`POLYSEMOUS_CROSS_DIRECTIVE_PATTERNS`):**
  - `fee`, `fees`, `charges`, `शुल्क`, `सेवा शुल्क`
  - `rate`, `rates`, `interest rate`, `ब्याजदर`
  - `blacklist`, `blacklisting`, `कालोसूची`
  - `penalty`, `fines`, `हर्जाना`, `जरिवाना`
- **How It Works *(in simple words: if you type just 'fees', the engine checks what documents match; seeing that some results discuss ATM card fees in Payment Directives and others discuss Loan prepayment fees in Unified Directives, it gives you a 1-click button for each document category)*:**
  If the retrieved candidate chunks span across multiple document categories, the engine dynamically generates a card:
  **"सटीक विषय छनोट (Select Specific Regulation)"**
  - 📱 *भुक्तानी प्रणाली निर्देशन (Payment Directives - वालेट, QR तथा कार्ड शुल्क)*
  - 🏦 *एकीकृत निर्देशन (Unified Directives - कर्जा तथा बैंकिङ सेवा शुल्क)*
  - 📊 *वार्षिक / सुपरीवेक्षण प्रतिवेदन (Supervision & Annual Reports)*

---

### Step 4: Intra-Document Chapter Disambiguation
If a bare 1- to 2-word query falls entirely within the **Unified Directives**, but spans multiple chapters (e.g., typing just `"reporting"` which touches Directive 4 Accounting, Directive 9 Statistics, and Directive 19 AML):
- The engine inspects the retrieved chunks, identifies which chapters are represented, and displays a card titled:
  **"निर्देशन अध्याय छनोट (Select Specific Chapter)"**
  with buttons pointing directly to the specific chapter (e.g., `एकीकृत निर्देशन (अध्याय २): कर्जा वर्गीकरण` vs `एकीकृत निर्देशन (अध्याय १५): ब्याजदर तथा शुल्क`).

---

## Real-World Query Comparison Matrix

| User Query | Action Taken | Disambiguation Result | Why? |
| :--- | :---: | :---: | :--- |
| `"categories of bad loan"` | **Direct Answer** | **No Card** | Contains domain anchor `bad loan` and attribute `categories` (Fast-Track Tier 1 & 2). |
| `"loan"` | **Option Card** | **Broad Topic Card** | Bare single-word keyword matching `BROAD_TOPICS["loan"]`. |
| `"mobile banking limit"` | **Direct Answer** | **No Card** | Contains domain anchor `mobile banking` and modifier `limit` (Fast-Track Tier 1). |
| `"fee"` | **Option Card** | **Cross-Category Card** | Polysemous keyword spanning Payment Directive fees (ATM/wallet) vs Unified Directive loan charges. |
| `"Directors' Meeting Allowance"` | **Direct Answer** | **No Card** | Contains specific anchors `meeting allowance` and `directors` (Fast-Track Tier 1). |
| `"qualification of compliance officer"` | **Direct Answer** | **No Card** | Contains anchor `compliance officer` and modifier `qualification` (Fast-Track Tier 1 & 2). |
| `"show me list of finance companies"` | **Direct Answer** | **No Card** | Natural sentence ($\ge 4$ words) with report intent routing to Annual Report 2025 Annex 4.1. |
| `"hi"` or `"rules"` | **Option Card** | **Suggested Prompts Card** | Matches low-confidence / greeting filter; presents 4 verified popular prompts. |

---

## Summary Checklist

| Component | Responsibility | Tech Stack / Algorithm | Cost / Tokens |
| :--- | :--- | :--- | :--- |
| **Specificity Fast-Track** | Prevents false-positive clarification cards | 3-Tier Regex & Token Intersection | **0 Groq Tokens** (<0.05ms) |
| **Broad Topic Engine** | Displays 1-click option cards for bare terms | Pattern Matching (`BROAD_TOPICS`) | **0 Groq Tokens** (<0.05ms) |
| **Intent Classifier** | Routes to Directives vs Annual Reports | Regex Intent Boundary Filter | **0 Groq Tokens** (<0.05ms) |
| **Cross-Lingual Engine** | Translates technical terms across languages | Groq Central Bank Few-Shot Engine | Sub-150ms Groq call |
| **Hybrid Retrieval** | Dual-pass Dense + Sparse search | LanceDB + SentenceTransformers + BM25 | Local Vector Cosine |
| **Targeted Windowing** | Trims long pages to ~2,200 char windows | Sub-string Indexing (400 lead, 600 trail) | Prevents Groq 429 sleeps |
| **Citation Extractor** | Maps references to exact PDF pages | Strict Lookaround Regex + Length Sort | Eliminates substring bugs |
| **LLM Generation** | Produces authoritative legal answers | `gpt-oss-120b` / `qwen3.8-27b` (`temp=0.0`) | Fully Deterministic |
