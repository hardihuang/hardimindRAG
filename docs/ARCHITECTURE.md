# Technical Architecture

> Deep dive into how Knowledge Search works under the hood.

## 1. Overall Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   RAG Q&A    │  │SemanticSearch│  │ Doc Browser  │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                  │            │
│         ▼                 ▼                  ▼            │
│  ┌─────────────────────────────────────────────────┐     │
│  │               ChromaDB (Local)                  │     │
│  │     N docs · 1024-dim vectors · cosine dist     │     │
│  └─────────────────────┬───────────────────────────┘     │
│                        │                                  │
│           ┌────────────┴────────────┐                    │
│           ▼                         ▼                    │
│  ┌─────────────────┐    ┌──────────────────────┐        │
│  │  Embedding API   │    │     LLM API          │        │
│  │  (Bailian/OpenAI)│    │  (Ark/OpenAI/... )  │        │
│  └─────────────────┘    └──────────────────────┘        │
└──────────────────────────────────────────────────────────┘
```

## 2. Indexing Pipeline

### Flow

```
Markdown files (.md)
       │
       ▼
  [index.py]
       │
   1. Scan directories recursively
   2. Parse YAML frontmatter (title, source_url)
   3. Truncate content to 2000 chars
   4. Batch call embedding API (10 per batch, with retry)
   5. Store vectors + metadata in ChromaDB
   6. Save MD5 hashes for incremental detection
       │
       ▼
  ChromaDB (chroma_db/)
```

### Key Design Decisions

**Incremental Indexing**
- Each file's MD5 hash is saved alongside the index
- On re-index, only new/changed files are processed
- Deleted files are **not** automatically removed from the index (feature gap)

**Batch Processing**
- Embedding API called in batches of 10 articles
- Reduces API call volume significantly for large corpora
- 3 retry attempts with exponential backoff on failure

**Frontmatter Parsing**
- Uses `python-frontmatter` library
- Supports both files with and without YAML frontmatter
- Without frontmatter: filename becomes title, no source URL

## 3. Search Flow

### Semantic Search (Tab 2)

```
User input (natural language)
       │
       ▼
  Embedding API → 1024-dim vector
       │
       ▼
  ChromaDB cosine similarity search
       │
       ▼
  Top-K results (title + similarity + snippet + source_url)
       │
       ▼
  Rendered as styled article cards
```

### RAG Q&A (Tab 1)

```
User question
       │
       ▼
  Semantic search → Top-5 articles
       │
       ▼
  Build context: concatenate article contents (≤6000 chars)
       │
       ▼
  Construct prompt:
    System: "Answer based ONLY on these articles..."
    History: last 6 conversation turns
    User: context + question
       │
       ▼
  LLM API call (temperature=0.3, thinking disabled)
       │
       ▼
  Response + source citations
       │
       ▼
  Rendered in chat UI with expandable source list
```

## 4. Prompt Design

**System Prompt:**
```
You are a knowledgeable assistant grounded in a personal knowledge base.
Answer questions based ONLY on the provided articles.

Rules:
1. Only use information from the provided articles — never make up content
2. If the articles don't contain relevant information, say so explicitly
3. Always cite your sources (which articles you're referencing)
4. Answer in clear, concise language
```

**User Prompt Template:**
```
Answer based on these articles:

[Article 1] Title (Year)
Content...

---
[Article 2] Title (Year)
Content...

...
(up to 5 articles, ~6000 chars total)

Question: {user_question}
```

## 5. Key Parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| Embedding dimension | 1024 | text-embedding-v4 |
| Vector distance | Cosine | ChromaDB default |
| Content truncation | 2000 chars | Per article for embedding |
| Summary length | 200 chars | For search result display |
| RAG Top-K | 5 | Articles retrieved per query |
| Context limit | 6000 chars | Max fed to LLM |
| LLM temperature | 0.3 | Low = factual, less creative |
| LLM max_tokens | 8192 | Room for long answers |
| LLM thinking mode | disabled | Reasoning models need this off |
| Conversation history | 6 rounds | Sliding window |
| Embedding batch size | 10 | Per API call |
| API retries | 3 | Exponential backoff |

## 6. Data Model

### Document Metadata (stored in ChromaDB)

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | From frontmatter (or filename) |
| `year` | string | Extracted from directory path |
| `source_url` | string | Original URL (from frontmatter) |
| `filepath` | string | Absolute path to source file |
| `summary` | string | First ~200 chars (cleaned) |
| `source_type` | string | Identifies which data source |

### ChromaDB Collection

- **Name**: `knowledge_base`
- **Distance**: Cosine
- **Index type**: HNSW (default)
- **Storage**: Local SQLite (file-based)

## 7. Multi-Source Support

The system supports multiple data sources via `source_type` metadata:

```python
SOURCE_CONFIGS = [
    {"name": "source_a", "dir": "/path/a", "label": "Source A"},
    {"name": "source_b", "dir": "/path/b", "label": "Source B"},
]
```

- Each document tagged with its `source_type`
- Search/Q&A can filter by source in the UI
- Document browser groups by source + year

## 8. Performance Characteristics

| Operation | ~900 docs | ~5000 docs |
|-----------|-----------|------------|
| First-time index | ~2 min | ~10 min |
| Incremental index | ~1 sec (nonew) | ~2 sec (nonew) |
| Embedding API call | ~0.5 sec/batch | ~0.5 sec/batch |
| Search (ChromaDB) | <100 ms | <200 ms |
| RAG Q&A (w/ LLM) | 2-5 sec | 2-5 sec |
| ChromaDB storage | ~50 MB | ~250 MB |

## 9. Limitations

- **No full-text search fallback**: Only semantic (vector) search
- **Fixed chunk size**: Whole documents truncated to 2000 chars
- **No re-ranking**: Top-K from vector similarity only
- **Deleted file handling**: No automatic removal from index
- **Single collection**: All sources in one ChromaDB collection
