#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Search — RAG + Semantic Search Web UI

A Streamlit application that provides:
- RAG Q&A: Ask questions, get answers grounded in your knowledge base
- Semantic Search: Find relevant articles by natural language query
- Document Browser: Browse all indexed documents

Design theme: Ink (墨砚) · Paper (宣纸) · Seal (朱印)
"""

import os
import json
import streamlit as st
import chromadb
import requests
import pandas as pd
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Configuration — Set via .env
# ============================================================

EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_ENDPOINT = os.getenv(
    "EMBEDDING_ENDPOINT",
    "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_ENDPOINT = os.getenv(
    "LLM_ENDPOINT",
    "https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions",
)
LLM_MODEL = os.getenv("LLM_MODEL", "glm-5.2")

CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
COLLECTION_NAME = "knowledge_base"

# Source display labels — update to match your SOURCE_CONFIGS names in index.py
SOURCE_LABELS = {"knowledge_base": "Knowledge Base"}

# ============================================================
# Page Config
# ============================================================

st.set_page_config(
    page_title="Knowledge Search",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ============================================================
# Theme
# ============================================================

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

theme = st.session_state.theme


def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
    st.rerun()


# ============================================================
# Design Tokens
# ============================================================

DARK_VARS = """
:root {
    --bg: #15171c;
    --bg-surface: #1c1f26;
    --bg-elevated: #252830;
    --bg-hover: #2e323c;
    --bg-sidebar: #121419;
    --text: #e8e4dc;
    --text-secondary: #c4bfb5;
    --text-muted: #7a7568;
    --text-faint: #4a4640;
    --border: #2e323c;
    --border-subtle: #22252c;
    --seal: #b8423d;
    --seal-soft: rgba(184, 66, 61, 0.14);
    --seal-glow: rgba(184, 66, 61, 0.25);
    --shadow: 0 2px 8px rgba(0,0,0,0.3);
    --shadow-lg: 0 8px 24px rgba(0,0,0,0.4);
    --badge-h-bg: rgba(184,66,61,0.15);   --badge-h-fg: #d4685f;
    --badge-m-bg: rgba(200,180,120,0.12); --badge-m-fg: #c8b478;
    --badge-l-bg: rgba(120,120,120,0.1);  --badge-l-fg: #6a655d;
    --tag-f-bg: rgba(120,160,200,0.12);   --tag-f-fg: #7aa5c8;
    --tag-x-bg: rgba(170,130,190,0.12);   --tag-x-fg: #b08ec0;
}
"""

LIGHT_VARS = """
:root {
    --bg: #f5f2ed;
    --bg-surface: #faf8f4;
    --bg-elevated: #ede9e1;
    --bg-hover: #e2ddd3;
    --bg-sidebar: #f0ede6;
    --text: #1a1d23;
    --text-secondary: #3a3d44;
    --text-muted: #7a7568;
    --text-faint: #a8a298;
    --border: #d4cfc7;
    --border-subtle: #e2ddd3;
    --seal: #a83a36;
    --seal-soft: rgba(168, 58, 54, 0.08);
    --seal-glow: rgba(168, 58, 54, 0.15);
    --shadow: 0 1px 4px rgba(60,50,30,0.06);
    --shadow-lg: 0 6px 20px rgba(60,50,30,0.1);
    --badge-h-bg: rgba(168,58,54,0.1);    --badge-h-fg: #a83a36;
    --badge-m-bg: rgba(180,140,50,0.12);  --badge-m-fg: #8a6a20;
    --badge-l-bg: rgba(120,120,120,0.08); --badge-l-fg: #6a655d;
    --tag-f-bg: rgba(60,100,160,0.1);     --tag-f-fg: #3a6a9a;
    --tag-x-bg: rgba(130,80,150,0.1);     --tag-x-fg: #7a4a8a;
}
"""

BASE_CSS = """
.stApp {
    background: var(--bg);
    font-family: 'PingFang SC', -apple-system, 'Helvetica Neue', sans-serif;
    color: var(--text);
}
.stApp, .stApp p, .stApp span, .stApp li, .stApp td, .stApp th {
    color: var(--text-secondary) !important;
    line-height: 1.7;
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
    color: var(--text) !important;
    font-family: 'Songti SC', 'Noto Serif SC', 'STSong', serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em;
}
.stAppViewBlockContainer {
    max-width: 720px !important;
    padding-top: 2.5rem !important;
    padding-bottom: 5rem !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 2rem !important;
}
section[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-subtle) !important;
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stText {
    color: var(--text-secondary) !important;
}
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] h5 {
    font-family: 'Songti SC', 'Noto Serif SC', serif !important;
    color: var(--text) !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    margin-bottom: 0.5rem !important;
}
section[data-testid="stSidebar"] hr {
    border: none !important;
    border-top: 1px solid var(--border-subtle) !important;
    margin: 1rem 0 !important;
}
.hm-header {
    display: flex; align-items: baseline; gap: 14px;
    margin-bottom: 0.2rem;
}
.hm-header .logo { font-size: 1.3rem; }
.hm-header .title {
    font-family: 'Songti SC', 'Noto Serif SC', 'STSong', serif;
    font-size: 1.35rem; font-weight: 700; color: var(--text);
    letter-spacing: -0.02em;
}
.hm-sub {
    color: var(--text-muted); font-size: 0.8rem; margin-bottom: 2rem;
    letter-spacing: 0.02em;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    border-bottom: 1px solid var(--border-subtle) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"] {
    padding: 10px 20px !important;
    border-radius: 0 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.2s !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-secondary) !important;
}
.stTabs [aria-selected="true"] {
    color: var(--text) !important;
    border-bottom: 2px solid var(--seal) !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: var(--seal) !important;
    height: 2px !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.5rem !important; }
.stChatMessage {
    padding: 0.5rem 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
}
.stChatMessage [data-testid="stChatMessageAvatarComponent"] {
    width: 28px !important; height: 28px !important;
}
.stChatMessage [data-testid="stChatMessageAvatarComponent"] svg {
    width: 16px !important; height: 16px !important;
}
.stChatMessage[data-testid="stChatMessage"]:has(img[alt="user"]),
.stChatMessage:has(div[data-testid="stChatMessageAvatarComponent-user"]) {
    background: var(--bg-elevated) !important;
    border-radius: 14px !important;
    padding: 0.6rem 1rem !important;
    margin-left: 15% !important;
}
.stChatMessage:has(div[data-testid="stChatMessageAvatarComponent-assistant"]) {
    background: transparent !important;
    border-radius: 0 !important;
    padding: 0.8rem 0 !important;
}
.stChatMessage [data-testid="stMarkdownContainer"] {
    font-size: 0.9rem !important;
    line-height: 1.75 !important;
    color: var(--text-secondary) !important;
}
.stChatInput { border: none !important; }
.stChatInput textarea {
    border: 1px solid var(--border) !important;
    border-radius: 22px !important;
    background: var(--bg-surface) !important;
    color: var(--text) !important;
    padding: 14px 22px !important;
    font-size: 0.9rem !important;
    font-family: 'PingFang SC', sans-serif !important;
    box-shadow: var(--shadow) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stChatInput textarea:focus {
    border-color: var(--seal) !important;
    box-shadow: 0 0 0 3px var(--seal-soft) !important;
}
.stChatInput textarea::placeholder { color: var(--text-faint) !important; }
.stChatInput button {
    background: var(--seal) !important;
    color: white !important;
    border-radius: 50% !important;
    border: none !important;
    width: 36px !important; height: 36px !important;
    min-width: 36px !important;
}
.stChatInput button:hover {
    background: var(--seal) !important;
    opacity: 0.85;
}
.stButton > button {
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-surface) !important;
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    padding: 7px 16px !important;
    font-family: 'PingFang SC', sans-serif !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: var(--bg-hover) !important;
    border-color: var(--seal) !important;
    color: var(--text) !important;
}
.stTextInput input {
    background: var(--bg-surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 0.875rem !important;
    padding: 8px 12px !important;
    font-family: 'PingFang SC', sans-serif !important;
    transition: border-color 0.2s !important;
}
.stTextInput input:focus {
    border-color: var(--seal) !important;
    box-shadow: 0 0 0 3px var(--seal-soft) !important;
}
.stTextInput input::placeholder { color: var(--text-faint) !important; }
div[data-baseweb="select"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 0.875rem !important;
}
div[data-baseweb="select"] > div {
    background: var(--bg-surface) !important;
    color: var(--text) !important;
    font-family: 'PingFang SC', sans-serif !important;
}
[data-baseweb="menu"] { background: var(--bg-elevated) !important; }
[data-baseweb="menu"] li { color: var(--text-secondary) !important; }
[data-baseweb="menu"] li:hover {
    background: var(--bg-hover) !important;
    color: var(--text) !important;
}
.stSlider label {
    font-size: 0.8rem !important;
    color: var(--text-muted) !important;
    margin-bottom: 0.3rem !important;
}
.stSlider [data-baseweb="slider"] { height: 4px !important; }
.stSlider [data-baseweb="thumb"] {
    background: var(--seal) !important;
    border: 2px solid var(--bg) !important;
    width: 16px !important; height: 16px !important;
}
.stSlider [data-baseweb="track"] { background: var(--bg-elevated) !important; }
.stSlider [data-baseweb="track-fill"] { background: var(--seal) !important; }
.stMetric {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 10px 14px !important;
}
.stMetric label {
    font-size: 0.7rem !important;
    color: var(--text-muted) !important;
    font-family: 'PingFang SC', sans-serif !important;
}
.stMetric [data-testid="stMetricValue"] {
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    font-family: 'SF Mono', 'Menlo', monospace !important;
}
.stat-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 0.9rem 1.1rem; text-align: center;
    box-shadow: var(--shadow);
}
.stat-card .num {
    font-size: 1.4rem; font-weight: 700; color: var(--text);
    font-family: 'SF Mono', 'Menlo', monospace;
}
.stat-card .label {
    font-size: 0.7rem; color: var(--text-muted); margin-top: 0.15rem;
    letter-spacing: 0.03em;
}
.article-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 0.85rem 1.1rem; margin-bottom: 0.5rem;
    transition: all 0.15s;
}
.article-card:hover {
    border-color: var(--seal) !important;
    box-shadow: var(--shadow-lg);
    transform: translateY(-1px);
}
.sim-badge {
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-size: 0.68rem; font-weight: 600; line-height: 1.5;
    font-family: 'SF Mono', monospace;
}
.sim-high { background: var(--badge-h-bg); color: var(--badge-h-fg); }
.sim-mid  { background: var(--badge-m-bg); color: var(--badge-m-fg); }
.sim-low  { background: var(--badge-l-bg); color: var(--badge-l-fg); }
.source-tag {
    display: inline-block; padding: 1px 6px; border-radius: 3px;
    font-size: 0.64rem; font-weight: 600; margin-left: 3px;
}
details {
    border: 1px solid var(--border-subtle) !important;
    border-radius: 10px !important;
    background: var(--bg-surface) !important;
    overflow: hidden;
}
details summary {
    padding: 0.6rem 1rem !important;
    font-size: 0.82rem !important;
    color: var(--text-muted) !important;
    font-family: 'PingFang SC', sans-serif !important;
}
details summary span { color: var(--text-muted) !important; }
details[open] summary {
    border-bottom: 1px solid var(--border-subtle) !important;
}
.stCodeBlock {
    border-radius: 8px !important;
    border: 1px solid var(--border-subtle) !important;
}
.stCodeBlock pre {
    background: var(--bg-sidebar) !important;
    font-size: 0.8rem !important;
}
.stCodeBlock code {
    font-family: 'SF Mono', 'Menlo', monospace !important;
}
a { color: var(--seal) !important; text-decoration: none !important; }
a:hover { text-decoration: underline !important; }
.stDataFrame {
    border: 1px solid var(--border-subtle) !important;
    border-radius: 10px !important;
    overflow: hidden;
}
.suggest-chip {
    display: inline-block; padding: 5px 14px; border-radius: 18px;
    background: var(--bg-surface); border: 1px solid var(--border);
    color: var(--text-muted); font-size: 0.78rem; margin: 3px;
    transition: all 0.15s;
}
.suggest-chip:hover { border-color: var(--seal); color: var(--seal); }
.stProgress > div > div { background: var(--seal) !important; }
.stSpinner > div { border-top-color: var(--seal) !important; }
hr {
    border: none !important;
    border-top: 1px solid var(--border-subtle) !important;
    margin: 1rem 0 !important;
}
.stCaption, .stCaption p {
    color: var(--text-muted) !important;
    font-size: 0.76rem !important;
}
#MainMenu, footer { visibility: hidden; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-faint); }
.theme-btn { font-size: 1.1rem; line-height: 1; cursor: pointer; background: transparent; border: none; padding: 4px 8px; }
"""

theme_vars = DARK_VARS if theme == "dark" else LIGHT_VARS
st.markdown(f"<style>{theme_vars}\n{BASE_CSS}</style>", unsafe_allow_html=True)

# ============================================================
# Utils
# ============================================================


@st.cache_resource
def init_chromadb():
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return None, None
    return client, collection


def load_index_info():
    time_file = os.path.join(CHROMA_DB_DIR, "index_time.txt")
    state_file = os.path.join(CHROMA_DB_DIR, "index_state.json")
    index_time = "Not indexed"
    if os.path.exists(time_file):
        with open(time_file, "r") as f:
            index_time = f.read().strip()
    doc_count = 0
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            doc_count = len(json.load(f))
    return doc_count, index_time


def encode_query(text):
    headers = {
        "Authorization": f"Bearer {EMBEDDING_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": EMBEDDING_MODEL, "input": [text]}
    resp = requests.post(EMBEDDING_ENDPOINT, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]


def search_knowledge_base(query, top_k=5, source_filter=None):
    query_embedding = encode_query(query)
    where_clause = {"source_type": source_filter} if source_filter else None
    results = collection.query(
        query_embeddings=[query_embedding], n_results=top_k, where=where_clause,
    )
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    documents = results.get("documents", [[]])[0]
    articles = []
    for doc_id, distance, meta, doc in zip(ids, distances, metadatas, documents):
        articles.append({
            "id": doc_id,
            "title": meta.get("title", "Untitled"),
            "year": meta.get("year", ""),
            "source_url": meta.get("source_url", ""),
            "filepath": meta.get("filepath", ""),
            "summary": meta.get("summary", ""),
            "source_type": meta.get("source_type", "knowledge_base"),
            "content": doc,
            "similarity": 1.0 - distance,
        })
    return articles


def build_rag_context(articles, max_chars=6000):
    parts, total = [], 0
    for i, a in enumerate(articles, 1):
        content = a["content"][:2000]
        part = f"[Article {i}] {a['title']} ({a['year']})\n{content}\n"
        if total + len(part) > max_chars:
            break
        parts.append(part)
        total += len(part)
    return "\n---\n".join(parts)


def call_llm(query, context, chat_history=None, temperature=0.3, max_tokens=8192):
    system_prompt = (
        "You are a knowledgeable assistant grounded in a personal knowledge base. "
        "Answer questions based ONLY on the provided articles.\n\n"
        "Rules:\n"
        "1. Only use information from the provided articles — never make up content\n"
        "2. If the articles don't contain relevant information, say so explicitly\n"
        "3. Always cite your sources (which articles you're referencing)\n"
        "4. Answer in clear, concise language\n"
    )
    messages = [{"role": "system", "content": system_prompt}]
    if chat_history:
        messages.extend(chat_history)
    messages.append({
        "role": "user",
        "content": f"Answer based on these articles:\n\n{context}\n\nQuestion: {query}",
    })
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": LLM_MODEL, "messages": messages,
        "temperature": temperature, "max_tokens": max_tokens,
        "thinking": {"type": "disabled"},
    }
    resp = requests.post(LLM_ENDPOINT, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    message = resp.json()["choices"][0]["message"]
    content = message.get("content", "") or message.get("reasoning_content", "")
    return content or "(Model returned empty response — please retry)"


def sim_badge(sim):
    pct = f"{sim*100:.1f}%"
    cls = "sim-high" if sim > 0.6 else "sim-mid" if sim > 0.4 else "sim-low"
    return f'<span class="sim-badge {cls}">{pct}</span>'


def source_tag(stype):
    label = SOURCE_LABELS.get(stype, stype)
    return f'<span class="source-tag">{label}</span>'


def render_sources(items):
    for a in items:
        sim_html = sim_badge(a["similarity"])
        tag_html = source_tag(a.get("source_type", "knowledge_base"))
        link = f"[{a['title']}]({a['source_url']})" if a.get("source_url") else a["title"]
        st.markdown(f"- {link} {tag_html} {sim_html}", unsafe_allow_html=True)


# ============================================================
# Initialize
# ============================================================

doc_count, index_time = load_index_info()

# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    hc, tc = st.columns([5, 1])
    with hc:
        st.markdown("### 🧠 Knowledge Search")
    with tc:
        icon = "☀️" if theme == "dark" else "🌙"
        if st.button(icon, help="Toggle theme", key="theme_toggle"):
            toggle_theme()

    st.caption("Local RAG · Semantic Search")
    st.markdown("---")

    st.markdown("##### Index")
    c1, c2 = st.columns(2)
    c1.metric("Documents", doc_count)
    c2.metric("Dimensions", "1024")
    st.caption(f"🕒 {index_time}")

    st.markdown("---")

    st.markdown("##### Parameters")
    rag_top_k = st.slider("Top-K", 3, 15, 5, help="Number of articles to retrieve")
    rag_temp = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1)
    rag_context = st.slider("Context limit", 2000, 12000, 6000, 500, help="Characters per query")

    st.markdown("---")
    st.caption("ChromaDB · Embedding API · LLM")

# ============================================================
# Main Area
# ============================================================

st.markdown(
    '<div class="hm-header">'
    '<span class="logo">🧠</span>'
    '<span class="title">Knowledge Search</span>'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hm-sub">Semantic search · Intelligent Q&A · Making knowledge retrievable</div>',
    unsafe_allow_html=True,
)

if doc_count == 0:
    st.warning("No index found. Run `python index.py` first.")
    st.stop()

client, collection = init_chromadb()
if collection is None:
    st.error("Cannot connect to ChromaDB")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["💬 Q&A", "🔎 Search", "📋 Documents", "📊 Overview"])

# ============================================================
# Tab 1: RAG Q&A
# ============================================================

with tab1:
    bc, bs, be = st.columns([2, 2, 3])
    with bc:
        rag_source = st.selectbox(
            "Source", ["All"] + list(SOURCE_LABELS.values()),
            key="rag_src", label_visibility="collapsed",
        )
    with bs:
        if st.session_state.get("rag_messages"):
            if st.button("✨ New conversation", use_container_width=True):
                st.session_state.rag_messages = []
                st.rerun()
    with be:
        if st.session_state.get("rag_messages"):
            lines = []
            for m in st.session_state.rag_messages:
                who = "🙋" if m["role"] == "user" else "🤖"
                lines.append(f"### {who}\n{m['content']}\n")
                if m["role"] == "assistant" and m.get("sources"):
                    lines.append("**Sources:**")
                    for s in m["sources"]:
                        lines.append(f"- {s['title']} ({s['similarity']*100:.1f}%)")
                    lines.append("")
            st.download_button(
                "📥 Export", "\n".join(lines),
                file_name="knowledge_search.md", mime="text/markdown",
                use_container_width=True,
            )

    if "rag_messages" not in st.session_state:
        st.session_state.rag_messages = []

    for msg in st.session_state.rag_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander(f"Sources ({len(msg['sources'])} articles)"):
                    render_sources(msg["sources"])

    user_question = st.chat_input("Ask a question...")

    if user_question:
        st.session_state.rag_messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Searching..."):
                try:
                    sf = None
                    if rag_source != "All":
                        reverse_labels = {v: k for k, v in SOURCE_LABELS.items()}
                        sf = reverse_labels.get(rag_source)
                    articles = search_knowledge_base(
                        user_question, top_k=rag_top_k, source_filter=sf
                    )
                except Exception as e:
                    st.error(f"Search failed: {e}")
                    st.stop()

            if not articles:
                response = "No relevant articles found."
                st.markdown(response)
                st.session_state.rag_messages.append({
                    "role": "assistant", "content": response, "sources": []
                })
            else:
                context = build_rag_context(articles, max_chars=rag_context)

                with st.expander(f"Retrieved {len(articles)} articles"):
                    render_sources(articles)

                with st.spinner("Generating answer..."):
                    try:
                        history = [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.rag_messages[:-1]
                        ][-6:]
                        response = call_llm(
                            user_question, context, history, temperature=rag_temp
                        )
                    except Exception as e:
                        response = f"Error generating response: {e}"

                st.markdown(response)
                st.code(response, language="markdown")

                sources = [
                    {
                        "title": a["title"], "source_url": a["source_url"],
                        "similarity": a["similarity"], "source_type": a["source_type"],
                    }
                    for a in articles
                ]
                st.session_state.rag_messages.append({
                    "role": "assistant", "content": response, "sources": sources
                })

# ============================================================
# Tab 2: Search
# ============================================================

with tab2:
    cs, cf, ct = st.columns([5, 2, 2])
    with cs:
        query = st.text_input(
            "Search", placeholder="Keywords or natural language...", key="search_input",
            label_visibility="collapsed",
        )
    with cf:
        search_source = st.selectbox(
            "Source", ["All"] + list(SOURCE_LABELS.values()), key="search_src",
            label_visibility="collapsed",
        )
    with ct:
        search_top = st.selectbox(
            "Max results", [10, 20, 30, 50], index=1, key="search_top",
            label_visibility="collapsed",
        )

    if query:
        with st.spinner("Searching..."):
            try:
                sf = None
                if search_source != "All":
                    reverse_labels = {v: k for k, v in SOURCE_LABELS.items()}
                    sf = reverse_labels.get(search_source)
                qe = encode_query(query)
                where = {"source_type": sf} if sf else None
                results = collection.query(
                    query_embeddings=[qe], n_results=search_top, where=where,
                )
            except Exception as e:
                st.error(f"Search error: {e}")
                st.stop()

            ids = results.get("ids", [[]])[0]
            distances = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            if not ids:
                st.info("No results found. Try a different query.")
            else:
                st.markdown(f"**{len(ids)} results**")

                for i, (doc_id, distance, meta) in enumerate(
                    zip(ids, distances, metadatas), 1
                ):
                    sim = 1.0 - distance
                    title = meta.get("title", "Untitled")
                    source_url = meta.get("source_url", "")
                    year = meta.get("year", "")
                    filepath = meta.get("filepath", "")
                    summary = meta.get("summary", "")
                    stype = meta.get("source_type", "knowledge_base")

                    sim_html = sim_badge(sim)
                    tag_html = source_tag(stype)

                    st.markdown('<div class="article-card">', unsafe_allow_html=True)
                    ct1, ct2 = st.columns([8, 2])

                    with ct1:
                        icons = ["◆", "◇", "◇"] + ["·"] * 47
                        icon = icons[i - 1] if i <= 50 else "·"
                        if source_url:
                            st.markdown(f"**{icon}　[{title}]({source_url})**")
                        else:
                            st.markdown(f"**{icon}　{title}**")
                        st.caption(
                            f"{year} · `{os.path.basename(filepath)}` {tag_html}",
                            unsafe_allow_html=True,
                        )

                    with ct2:
                        st.markdown(f"`{sim:.4f}`")
                        st.markdown(sim_html, unsafe_allow_html=True)

                    if summary:
                        st.markdown(summary[:280] + ("..." if len(summary) > 280 else ""))

                    st.markdown('</div>', unsafe_allow_html=True)

    if not query:
        st.info("Enter a query to search your knowledge base")
        st.markdown("")
        st.markdown("##### Try")
        suggestions = ["What is this knowledge base about?", "Key concepts", "Recent updates"]
        chips = "".join(f'<span class="suggest-chip">{s}</span>' for s in suggestions)
        st.markdown(chips, unsafe_allow_html=True)

        cols = st.columns(len(suggestions))
        for col, s in zip(cols, suggestions):
            if col.button(s, key=f"sg_{s}"):
                st.session_state.search_input = s
                st.rerun()

# ============================================================
# Tab 3: Document Browser
# ============================================================

with tab3:
    all_docs = collection.get()
    if not all_docs["ids"]:
        st.info("No documents")
        st.stop()

    all_metas = all_docs["metadatas"]
    total = len(all_metas)
    src_counts = Counter(m.get("source_type", "knowledge_base") for m in all_metas)
    yr_counts = Counter(m.get("year", "unknown") for m in all_metas)
    latest_yr = max((y for y in yr_counts if y != "unknown"), default="-")

    for col, (n, l) in zip(
        st.columns(4),
        [(total, "Documents"), (len(src_counts), "Sources"),
         (len(yr_counts), "Years"), (latest_yr, "Latest")],
    ):
        col.markdown(
            f'<div class="stat-card"><div class="num">{n}</div>'
            f'<div class="label">{l}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    f1, f2, f3 = st.columns([2, 2, 3])
    with f1:
        dsf = st.selectbox(
            "Source", ["All"] + list(src_counts.keys()),
            format_func=lambda x: "All" if x == "All" else SOURCE_LABELS.get(x, x),
            key="doc_sf",
        )
    with f2:
        yrs = sorted(yr_counts.keys(), reverse=True)
        dyf = st.selectbox("Year", ["All"] + yrs, key="doc_yf")
    with f3:
        tf = st.text_input("Title filter", placeholder="Filter...", key="doc_tf")

    filtered = []
    for m in all_metas:
        stype = m.get("source_type", "knowledge_base")
        yr = m.get("year", "unknown")
        title = m.get("title", "")
        if dsf != "All" and stype != dsf:
            continue
        if dyf != "All" and yr != dyf:
            continue
        if tf and tf.lower() not in title.lower():
            continue
        filtered.append(m)

    st.markdown(f"**{len(filtered)} documents**")

    if not filtered:
        st.info("No matches")
        st.stop()

    grouped = {}
    for m in filtered:
        stype = m.get("source_type", "knowledge_base")
        yr = m.get("year", "unknown")
        grouped.setdefault((stype, yr), []).append(m)

    cur_src = None
    for (stype, yr) in sorted(
        grouped.keys(),
        key=lambda x: (x[0], x[1] if x[1] != "unknown" else "0"),
    ):
        if stype != cur_src:
            cur_src = stype
            label = SOURCE_LABELS.get(stype, stype)
            st.markdown(f"#### {label}")

        items = sorted(grouped[(stype, yr)], key=lambda x: x.get("title", ""))
        with st.expander(f"{yr} ({len(items)} documents)"):
            for m in items:
                title = m.get("title", "Untitled")
                url = m.get("source_url", "")
                fp = m.get("filepath", "")
                a, b, c = st.columns([7, 2, 3])
                with a:
                    st.markdown(f"[{title}]({url})" if url else f"- {title}")
                with b:
                    st.caption(os.path.basename(fp))
                with c:
                    if url:
                        st.caption(f"[🔗]({url})")

# ============================================================
# Tab 4: Overview
# ============================================================

with tab4:
    total = len(all_metas)
    src_counts = Counter(m.get("source_type", "knowledge_base") for m in all_metas)
    yr_counts = Counter(m.get("year", "unknown") for m in all_metas)

    st.markdown("##### Data Sources")
    for col, (st2, cnt) in zip(st.columns(len(src_counts)), src_counts.items()):
        label = SOURCE_LABELS.get(st2, st2)
        col.metric(label, f"{cnt} docs")
        col.progress(cnt / total)

    st.markdown("---")

    st.markdown("##### Year Distribution")
    sorted_yrs = sorted(
        yr_counts.items(), key=lambda x: x[0] if x[0] != "unknown" else "0"
    )
    mx = max(yr_counts.values())
    rows = [
        {
            "Year": y, "Count": c,
            "Pct": f"{c/total*100:.1f}%",
            "Bar": "█" * int(c / mx * 30),
        }
        for y, c in sorted_yrs
    ]
    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True, hide_index=True,
            column_config={"Bar": st.column_config.TextColumn("Bar", width="medium")},
        )

    st.markdown("---")

    st.markdown("##### Commands")
    for col, (cmd, desc) in zip(
        st.columns(4),
        [("python3 index.py", "Update index"),
         ("streamlit run app.py", "Start"),
         ("--server.port 8502", "Change port"),
         ("cp -r chroma_db/ bak/", "Backup")],
    ):
        col.code(cmd, language="bash")
        col.caption(desc)

    st.markdown("---")
    st.caption(f"Knowledge Search · {index_time} · {total} documents")
