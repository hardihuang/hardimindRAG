#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Search - Index Builder

Builds a vector index from a directory of Markdown files.

Features:
1. Recursively scans source directories for .md files
2. Parses YAML frontmatter for title/source metadata
3. Generates embeddings via API (batch processing)
4. Stores vectors in ChromaDB (local file-based)
5. Incremental updates via MD5 hash detection
"""

import os
import sys
import time
import json
import hashlib
import requests
import frontmatter
import chromadb
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================
# Configuration — Edit these or use .env
# ============================================================

# Data source directories
# Format: {"name": "source_id", "dir": "/path/to/markdown/files", "label": "Display Name"}
SOURCE_CONFIGS = [
    {
        "name": "knowledge_base",
        "dir": "/path/to/your/markdown/files",
        "label": "Knowledge Base",
    },
]

# Embedding API
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_ENDPOINT = os.getenv(
    "EMBEDDING_ENDPOINT",
    "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")
EMBEDDING_DIM = 1024

# ChromaDB storage
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")

# Batch settings
BATCH_SIZE = 10
MAX_CONTENT_LENGTH = 2000
PROGRESS_INTERVAL = 50
MAX_RETRIES = 3

# ============================================================
# File Utilities
# ============================================================


def collect_markdown_files(root_dir):
    """Recursively scan all .md files, return sorted list of paths."""
    md_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.endswith(".md"):
                md_files.append(os.path.join(dirpath, fname))
    return sorted(md_files)


def extract_year(filepath):
    """Extract year from file path (looks for 4-digit directory names)."""
    parts = Path(filepath).parts
    for part in parts:
        if part.isdigit() and len(part) == 4:
            return part
    return "unknown"


def parse_article(filepath, source_type):
    """
    Parse a single markdown article.

    Extracts title and source_url from YAML frontmatter (if present).
    Falls back to filename stem if no frontmatter title.
    Returns dict or None on failure.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)
    except Exception as e:
        print(f"  [WARN] Failed to read {filepath}: {e}")
        return None

    title = post.get("title", Path(filepath).stem)
    source_url = post.get("source", "")

    content = post.content[:MAX_CONTENT_LENGTH]

    # Generate summary (first ~200 chars, stripping markdown noise)
    cleaned_lines = []
    for line in content.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("---"):
            continue
        cleaned_lines.append(line)
    summary = " ".join(cleaned_lines)[:200]

    year = extract_year(filepath)

    return {
        "filepath": filepath,
        "title": title,
        "source_url": source_url,
        "year": year,
        "content_for_embedding": content,
        "summary": summary,
        "source_type": source_type,
    }


def get_file_hash(filepath):
    """Compute MD5 hash of file contents for change detection."""
    hasher = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    except Exception:
        return None


def load_index_state():
    """Load previous index state (filepath -> hash mapping)."""
    state_file = os.path.join(CHROMA_DB_DIR, "index_state.json")
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_index_state(state):
    """Save index state to disk."""
    state_file = os.path.join(CHROMA_DB_DIR, "index_state.json")
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def filter_new_or_modified(files, prev_state):
    """Filter files that are new or modified since last index."""
    result = []
    for fp in files:
        current_hash = get_file_hash(fp)
        if current_hash is None:
            continue
        prev_hash = prev_state.get(fp)
        if prev_hash is None or prev_hash != current_hash:
            result.append(fp)
    return result


# ============================================================
# Embedding API
# ============================================================


def call_embedding_api(texts, retries=MAX_RETRIES):
    """
    Call embedding API (batch).

    Supports Alibaba Cloud Bailian / OpenAI-compatible endpoints.
    texts: list of strings
    returns: list of embedding vectors
    """
    headers = {
        "Authorization": f"Bearer {EMBEDDING_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": EMBEDDING_MODEL,
        "input": texts,
    }

    for attempt in range(retries):
        try:
            resp = requests.post(
                EMBEDDING_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            embeddings = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in embeddings]

        except requests.exceptions.Timeout:
            print(f"  [RETRY] API timeout, attempt {attempt + 1}/{retries}...")
            time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            print(f"  [RETRY] API error: {e}, attempt {attempt + 1}/{retries}...")
            time.sleep(2 ** attempt)
        except (KeyError, ValueError) as e:
            print(f"  [ERROR] Unexpected API response: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise

    raise RuntimeError(f"Embedding API failed after {retries} retries")


# ============================================================
# ChromaDB Operations
# ============================================================


def init_chromadb():
    """Initialize ChromaDB client and collection."""
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

    try:
        collection = client.get_collection("knowledge_base")
        print(f"  [INFO] Connected to existing collection ({collection.count()} docs)")
    except Exception:
        collection = client.create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"},
        )
        print("  [INFO] Created new collection: knowledge_base")

    return client, collection


# ============================================================
# Main
# ============================================================


def main():
    print("=" * 60)
    print("  Knowledge Search - Index Builder")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # Step 1: Scan
    print("[1/5] Scanning markdown directories...")
    total_files = 0
    for sc in SOURCE_CONFIGS:
        count = len(collect_markdown_files(sc["dir"]))
        print(f"  {sc['label']} ({sc['name']}): {count} files")
        total_files += count
    print(f"  Total: {total_files} .md files found")

    # Step 2: Incremental check
    print("\n[2/5] Checking for incremental updates...")
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)
    prev_state = load_index_state()

    files_to_process = []
    for sc in SOURCE_CONFIGS:
        source_files = collect_markdown_files(sc["dir"])
        if prev_state:
            filtered = filter_new_or_modified(source_files, prev_state)
        else:
            filtered = source_files
        for fp in filtered:
            files_to_process.append((fp, sc))

    if prev_state:
        print(f"  Previous index: {len(prev_state)} files")
        print(f"  To process: {len(files_to_process)} (new/modified)")
    else:
        print(f"  First-time index: {len(files_to_process)} files to process")

    if not files_to_process:
        print("\n  No updates needed. Index is up to date.")
        print("=" * 60)
        return

    # Step 3: Parse
    print(f"\n[3/5] Parsing {len(files_to_process)} articles...")
    articles = []
    parse_failures = 0
    for fp, sc in files_to_process:
        article = parse_article(fp, sc["name"])
        if article:
            articles.append(article)
        else:
            parse_failures += 1

    print(f"  Parsed: {len(articles)} articles")
    if parse_failures > 0:
        print(f"  Failed: {parse_failures} articles")

    if not articles:
        print("\n  No articles to process.")
        return

    # Step 4: Generate embeddings
    print(f"\n[4/5] Generating embeddings (batch size: {BATCH_SIZE})...")
    total = len(articles)
    all_embeddings = []

    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch = articles[batch_start:batch_end]
        batch_texts = [a["content_for_embedding"] for a in batch]

        try:
            embeddings = call_embedding_api(batch_texts)
            all_embeddings.extend(embeddings)
        except Exception as e:
            print(f"\n  [FATAL] Embedding batch failed: {e}")
            return

        processed = batch_end
        if processed % PROGRESS_INTERVAL == 0 or processed == total:
            batch_num = batch_end // BATCH_SIZE + (1 if batch_end % BATCH_SIZE else 0)
            total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
            print(f"  Progress: {processed}/{total} ({batch_num}/{total_batches} batches)")

    print(f"  Done! {len(all_embeddings)} vectors generated")

    # Step 5: Store in ChromaDB
    print("\n[5/5] Storing in ChromaDB...")
    client, collection = init_chromadb()

    # Delete old records for modified files
    existing_filepaths = set(prev_state.keys())
    new_filepaths = [a["filepath"] for a in articles]
    for fp in new_filepaths:
        if fp in existing_filepaths:
            try:
                collection.delete(where={"filepath": fp})
            except Exception:
                pass

    # Add new records
    existing_count = collection.count()
    ids = [str(existing_count + i) for i in range(len(articles))]
    metadatas = [
        {
            "title": a["title"],
            "year": a["year"],
            "filepath": a["filepath"],
            "source_url": a.get("source_url", ""),
            "summary": a.get("summary", ""),
            "source_type": a["source_type"],
        }
        for a in articles
    ]
    documents = [a["content_for_embedding"] for a in articles]

    ADD_BATCH = 100
    for i in range(0, len(articles), ADD_BATCH):
        end = min(i + ADD_BATCH, len(articles))
        collection.add(
            ids=ids[i:end],
            embeddings=all_embeddings[i:end],
            metadatas=metadatas[i:end],
            documents=documents[i:end],
        )
        print(f"  Stored: {end}/{len(articles)}")

    # Save index state
    new_state = dict(prev_state)
    for a in articles:
        new_state[a["filepath"]] = get_file_hash(a["filepath"])
    save_index_state(new_state)

    with open(os.path.join(CHROMA_DB_DIR, "index_time.txt"), "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    print(f"\n{'=' * 60}")
    print(f"  Index complete!")
    print(f"  Total documents: {len(new_state)}")
    print(f"  New/updated: {len(articles)}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
