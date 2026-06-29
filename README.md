# Knowledge Search — Local RAG + Semantic Search

> **Turn your Markdown knowledge base into a searchable, Q&A-ready AI engine — fully local, zero cloud dependencies for data.**

A complete local RAG (Retrieval-Augmented Generation) system that indexes your markdown files, enables semantic search, and answers questions based on your content. Built with ChromaDB, Streamlit, and any OpenAI-compatible embedding + LLM APIs.

## ✨ Features

| Feature | Description |
|---------|------------|
| **💬 RAG Q&A** | Ask questions, get answers grounded in your knowledge base with cited sources |
| **🔎 Semantic Search** | Find relevant documents by natural language — not just keyword matching |
| **📋 Document Browser** | Browse all indexed documents by year and source with filters |
| **🔄 Incremental Indexing** | Only re-indexes new or modified files (MD5 hash detection) |
| **🌙 Dark/Light Theme** | Elegant ink-on-paper design with toggle |
| **📊 Overview Dashboard** | Visual breakdown of your knowledge base composition |
| **🔌 API-agnostic** | Works with any OpenAI-compatible embedding & LLM API |

## 🏗️ Architecture

```
                     Streamlit Web UI
    ┌──────────────────┬──────────────────┐
    │   RAG Q&A        │  Semantic Search │  Document Browser
    └────────┬─────────┴────────┬─────────┘
             │                  │
             ▼                  ▼
    ┌──────────────────────────────────┐
    │         Retrieval Layer          │
    │     ChromaDB (local file DB)     │
    │   Cosine similarity · 1024 dim   │
    └──────────┬───────────────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
┌────────────┐  ┌──────────────┐
│  Embedding  │  │     LLM      │
│    API      │  │    API       │
│ (Bailian /  │  │ (Ark /       │
│  OpenAI)    │  │  OpenAI)     │
└────────────┘  └──────────────┘
```

## 🛠️ Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Vector DB** | [ChromaDB](https://www.trychroma.com/) | Local file-based, zero-ops, Python-native |
| **Embedding** | Any OpenAI-compatible API | 1024-dim, excellent Chinese/English support |
| **LLM** | Any OpenAI-compatible API | Plug in your preferred model |
| **Frontend** | [Streamlit](https://streamlit.io/) | Single-file Python web app, fast to deploy |

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- An embedding API key (e.g., Alibaba Cloud Bailian, OpenAI, etc.)
- An LLM API key (e.g., Volcengine Ark, OpenAI, DeepSeek, etc.)

### 2. Setup

```bash
# Clone or copy the project
cd knowledge-search

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys and endpoints
```

### 3. Configure Data Sources

Edit `index.py` — update the `SOURCE_CONFIGS` array to point to your markdown directories:

```python
SOURCE_CONFIGS = [
    {
        "name": "my_knowledge",
        "dir": "/path/to/your/markdown/files",
        "label": "My Knowledge",
    },
]
```

Your markdown files should ideally have YAML frontmatter:
```yaml
---
title: Article Title
source: https://example.com/article
---

Article content here...
```

Files without frontmatter are also supported (filename used as title).

### 4. Build Index

```bash
python3 index.py
```

First run indexes everything (~2 min for 900 files). Subsequent runs are incremental.

### 5. Launch

```bash
streamlit run app.py
# Or use the start script:
bash run.sh
```

Open `http://localhost:8501` in your browser.

## 📁 Project Structure

```
knowledge-search/
├── app.py               # Streamlit web app (Q&A + Search + Browser)
├── index.py             # Index builder (scan → embed → store)
├── run.sh               # One-click start script
├── requirements.txt     # Python dependencies
├── .env.example         # API key template
├── .gitignore           # Excludes chroma_db/ and .env
├── chroma_db/           # Auto-generated vector database
│   ├── chroma.sqlite3          # Vector store
│   ├── index_state.json        # File hash map (for incremental updates)
│   └── index_time.txt          # Last index timestamp
└── docs/
    ├── ARCHITECTURE.md          # Technical architecture deep dive
    └── DEPLOYMENT.md            # Operations & troubleshooting
```

## 🧪 How It Works

### Indexing Pipeline

```
Scan .md files → Parse frontmatter → Truncate to 2000 chars
     → Batch embedding API call (10 per batch)
     → Store in ChromaDB (cosine distance)
     → Save MD5 hash per file (incremental)
```

### Search Flow

```
User query → Embedding API → vector (1024-dim)
     → ChromaDB cosine similarity search
     → Return Top-K articles with scores
```

### RAG Flow

```
User question → Retrieve Top-5 articles
     → Build context (up to 6000 chars)
     → Construct prompt with system instructions + context + history
     → Call LLM API → Return answer with source citations
```

## 🔧 Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Embedding model | text-embedding-v4 | Configurable via `.env` |
| Vector dimension | 1024 | Per embedding model |
| Content truncation | 2000 chars | Input to embedding |
| RAG Top-K | 5 | Articles retrieved per query |
| Context limit | 6000 chars | Max content fed to LLM |
| LLM Temperature | 0.3 | Lower = less hallucination |
| Conversation history | 6 rounds | For multi-turn Q&A |
| Batch size | 10 | Articles per API call |

## 🔌 API Compatibility

This project uses a **generic OpenAI-compatible API client** — you can swap in:

| Provider | Embedding | LLM |
|----------|-----------|-----|
| Alibaba Bailian | ✅ text-embedding-v4 | ✅ Qwen series |
| Volcengine Ark | ✅ | ✅ GLM, DeepSeek |
| OpenAI | ✅ text-embedding-3-* | ✅ GPT-4/3.5 |
| DeepSeek | ✅ | ✅ DeepSeek-V2/V3 |
| Any OpenAI-compatible API | ✅ | ✅ |

## 🧭 Extensions

- **More data sources** — Add multiple directories with different source names
- **Re-ranking** — Add Cross-Encoder for precision improvement
- **Chunking strategies** — Switch from full-article to paragraph-level embedding
- **API service** — Wrap as REST API for external consumption
- **Multi-model** — Config file for switching LLM backends

## 📝 Requirements

See `requirements.txt`:
```
chromadb
streamlit
numpy
requests
python-frontmatter<1.0
python-dotenv
```

## 🤝 Contributing

This is a practical tool shared openly. Fork it, improve it, share it back.

---

*Built with ChromaDB · Streamlit · OpenAI-compatible APIs*
