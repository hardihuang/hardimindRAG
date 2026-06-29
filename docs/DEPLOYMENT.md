# Deployment & Operations Guide

## 1. Requirements

- **Python**: 3.9+
- **OS**: macOS, Linux, or Windows
- **Network**: Internet access for embedding & LLM APIs
- **Storage**: ~50 MB per 1000 documents (vector DB)

## 2. Installation

```bash
# Clone the project
git clone <your-repo-url>
cd knowledge-search

# (Optional) Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your keys
```

## 3. Configuration

### 3.1 API Keys

Create a `.env` file (based on `.env.example`):

```env
EMBEDDING_API_KEY="sk-your-key"
EMBEDDING_ENDPOINT="https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
EMBEDDING_MODEL="text-embedding-v4"

LLM_API_KEY="your-llm-key"
LLM_ENDPOINT="https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions"
LLM_MODEL="glm-5.2"
```

### 3.2 Data Sources

Edit `index.py` to configure your markdown directories:

```python
SOURCE_CONFIGS = [
    {
        "name": "my_knowledge",
        "dir": "/path/to/your/markdown/files",
        "label": "My Knowledge",
    },
]
```

Then sync `SOURCE_LABELS` in `app.py` to match:

```python
SOURCE_LABELS = {"my_knowledge": "My Knowledge"}
```

### 3.3 Switching LLM Models

Edit `.env`:
```env
# Volcengine Ark model
LLM_ENDPOINT="https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions"
LLM_MODEL="glm-5.2"

# Or switch to DeepSeek
LLM_ENDPOINT="https://api.deepseek.com/v1/chat/completions"
LLM_MODEL="deepseek-chat"

# Or switch to OpenAI
LLM_ENDPOINT="https://api.openai.com/v1/chat/completions"
LLM_MODEL="gpt-4o-mini"
```

> ⚠️ **Important for reasoning models** (GLM-5.2, DeepSeek-R1):
> If the LLM returns empty content, add `thinking: {"type": "disabled"}` in `call_llm()` in `app.py`.

### 3.4 Switching Embedding Models

Update both `index.py` and `.env`:

```env
EMBEDDING_ENDPOINT="https://api.openai.com/v1/embeddings"
EMBEDDING_MODEL="text-embedding-3-small"
```

> ⚠️ Changing embedding models requires a **full re-index** (delete `chroma_db/` and rebuild).

## 4. Running

### First-time Index

```bash
python3 index.py
```

Expected output for ~900 files:
```
============================================================
  Knowledge Search - Index Builder
  Started: 2026-06-29 18:00:00
============================================================

[1/5] Scanning markdown directories...
  Knowledge Base: 892 files
  Total: 892 .md files found

[2/5] Checking for incremental updates...
  First-time index: 892 files to process

[3/5] Parsing 892 articles...
  Parsed: 892 articles

[4/5] Generating embeddings (batch size: 10)...
  Progress: 892/892 (90/90 batches)
  Done! 892 vectors generated

[5/5] Storing in ChromaDB...
  Stored: 892/892

============================================================
  Index complete!
  Total documents: 892
  New/updated: 892
============================================================
```

### Start the App

```bash
streamlit run app.py
# Or
bash run.sh
```

Open `http://localhost:8501`

### Incremental Update

When you add or modify files in your source directories:

```bash
python3 index.py
# Only processes new/modified files (MD5 check)
```

## 5. Daily Operations

| Task | Command |
|------|---------|
| Update index | `python3 index.py` |
| Start app | `streamlit run app.py` |
| Change port | `streamlit run app.py --server.port 8502` |
| Backup vector DB | `cp -r chroma_db/ /backup/chroma_db_$(date +%Y%m%d)/` |
| Full re-index | `rm -rf chroma_db/ && python3 index.py` |

## 6. Production Deployment

### 6.1 Server with systemd

```ini
[Unit]
Description=Knowledge Search
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/knowledge-search
ExecStart=/path/to/venv/bin/streamlit run app.py --server.port 8501
Restart=always
EnvironmentFile=/path/to/knowledge-search/.env

[Install]
WantedBy=multi-user.target
```

### 6.2 Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

```bash
docker build -t knowledge-search .
docker run -p 8501:8501 --env-file .env knowledge-search
```

### 6.3 Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 7. Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Search returns empty | No index built | Run `python3 index.py` |
| Embedding API error | Invalid/expired API key | Check `EMBEDDING_API_KEY` in `.env` |
| LLM returns empty | Reasoning model needs config | Add `thinking: {"type": "disabled"}` |
| LLM 400 error | Wrong model ID | Verify model ID with provider |
| Port conflict | Port 8501 in use | `--server.port 8502` |
| Slow first index | Large corpus + API rate limits | Normal for 900+ docs (~2 min) |
| ChromaDB error | Corrupted DB | Delete `chroma_db/` and re-index |

## 8. Backup & Restore

### Backup
```bash
cp -r chroma_db/ /backup/chroma_db_20260629/
```

### Restore
```bash
cp -r /backup/chroma_db_20260629/ chroma_db/
# No need to re-index after restore
```

## 9. Maintenance

- **Weekly**: Run `python3 index.py` to pick up new/modified files
- **Monthly**: Back up `chroma_db/` directory
- **As needed**: Full re-index after embedding model change
