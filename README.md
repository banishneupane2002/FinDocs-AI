# NRB Banking Document Intelligence System (RAG)

An offline-first, dual-language Retrieval-Augmented Generation (RAG) system built for searching, verifying, and querying Nepal Rastra Bank (NRB) Directives, Circulars, and Annual Supervision Reports in both English and official Nepali.

---

## 🌟 Key Features

- **Font-Aware PDF Extraction:** Preserves English terms inside Preeti documents and normalizes legacy Preeti text into clean Devanagari Unicode using PyMuPDF and rule-based decoders.
- **Cross-Lingual Dual-Pass Hybrid IR:** Combines semantic dense retrieval (`paraphrase-multilingual-MiniLM-L12-v2`) and BM25-style keyword search in LanceDB with reciprocal rank fusion.
- **Auto Year Detection & Query Routing:** Intelligently routes queries containing specific fiscal or directive years (e.g. 2080, 2082, 2024) to the exact governing document, while applying recency weighting for unanchored queries.
- **Grounded Low-Latency Answers:** Streams verifiable answers using Groq LPU models (`qwen/qwen3.8-27b`, `openai/gpt-oss-120b`) with strict anti-hallucination prompts.
- **Interactive Source Verification:** 1-click in-browser page viewer and expandable text snippets for rapid audit verification.
- **Real-Time Indexing:** Automatic folder watcher (`watcher.py`) that synchronizes document additions, updates, and deletions in seconds.

---

## 🚀 Quick Setup

### 1. Prerequisites & Environment
Ensure you have Python 3.10+ installed.

```bash
# Install required dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the template and add your Groq API key:
```bash
copy .env.example .env
```
Inside `.env`:
```ini
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Ingest Banking Documents
Place your PDF files inside the `File_System/` directory, then run:
```bash
python INGEST.PY
```

---

## 🖥️ Running the Application

### Streamlit Web Interface
To launch the interactive dashboard:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### Terminal Assistant (CLI)
To run in terminal mode:
```bash
python ask.py
```

### Background File Watcher
To automatically ingest new or modified files dropped into `File_System/`:
```bash
python watcher.py
```

---

## 🛠️ Utility Scripts

- **`python view_db.py`**: Quick diagnostic script to inspect table metadata and stored vectors in LanceDB.
- **`python search.py`**: Fast offline semantic search probe for testing query vectors directly against `bank_documents`.
