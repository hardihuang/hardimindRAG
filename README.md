<div align="center">

# 🧠 HardiMind RAG

**Local RAG + Semantic Search for your Obsidian Knowledge Base**

将你的 Obsidian 知识库变成可语义搜索、可智能问答的本地 AI 引擎

[English](#english) · [中文](#中文)

---

</div>

## 中文

> **为什么自己造轮子而不是用 AnythingLLM？**

### 💡 背景：从 AnythingLLM 到自研

这套系统的诞生源于使用 [AnythingLLM](https://anythingllm.com/) 时遇到的几个核心痛点：

| 问题 | AnythingLLM | ✅ HardiMind RAG |
|------|-------------|-----------------|
| **性能** | 电脑非常卡，尤其是大批量文件处理时 | 轻量本地 ChromaDB，几乎无性能开销 |
| **同步** | Obsidian 文件无法自动同步，需要手动导入 | **原位向量化**——直接读 Obsidian 原始目录，无需转移或备份文件 |
| **自动化** | 大批量文件处理无法实现自动化 | 增量索引 + MD5 哈希检测，新增文件自动发现 |
| **开放接口** | 封闭系统，无法外部调用 | 配合 OpenClaw 等 Agent 平台，可在手机飞书上直接检索 |
| **检索质量** | 仅向量检索 | 向量语义检索 + 底层 BM25 全文检索双引擎联动 |

### 🏗️ 完整生态架构

这套系统不是孤立的——它嵌入在一个完整的 **AI 原生知识工作流** 中：

```
┌─────────────────────────────────────────────────────────────────┐
│                         Obsidian 知识库                          │
│               Markdown 文件（日记、笔记、文章等）                 │
│                    不转移、不备份，原位使用                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                       HardiMind RAG（本系统）                     │
│                                                                  │
│  1. index.py — 扫描 Obsidian 目录 → 原位 Embedding → ChromaDB   │
│  2. app.py    — Streamlit Web UI（Q&A + 语义搜索 + 文档浏览）    │
│  3. 增量索引 — 新增/修改文件自动检测，无需全量重建                │
│                                                                  │
│  底层引擎：BM25 全文检索（配合 OpenClaw Agent）                  │
│  向量引擎：ChromaDB 余弦相似度搜索                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     OpenClaw Agent 平台                          │
│                                                                  │
│  手机飞书发消息 → AI Agent 自动调用 BM25/向量检索                │
│  → 返回答案 + 引用来源 → 所有对话历史可追溯                      │
│                                                                  │
│  真正做到：坐在沙发上，掏出手机就能查知识库                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                         下游输出                                │
│  · Streamlit Web UI（本地浏览器访问）                          │
│  · 飞书 IM（手机消息对话检索）                                 │
│  · AI Agent 工作流（自动调研、自动写作、自动课评）            │
└────────────────────────────────────────────────────────────────┘
```

### 🎯 三大核心理念

#### 1️⃣ 原位向量化（In-Place Embedding）

**Obsidian 里的所有文件，不需要转移或备份到其他地方。**

传统方案需要你把文件导入到一个"知识库系统"里——文件被复制、移动、格式转换。这套系统直接读取 Obsidian 的原始 Markdown 目录，基于原始位置完成向量化（Embedding）。

- ✅ 文件永远在 Obsidian 里，你只管写
- ✅ 新增文件自动被增量索引检测到
- ✅ 修改文件自动更新向量
- ✅ 不产生任何冗余副本

#### 2️⃣ 双引擎检索（BM25 + Vector Search）

这套系统的最大优势之一是与 [OpenClaw](https://openclaw.ai) Agent 平台的深度联动：

- **向量检索（ChromaDB）**：语义理解，找"概念相关"的内容
- **BM25 全文检索（OpenClaw 底层）**：关键词精确匹配，找"字面匹配"的内容
- **双引擎联动**：向量搜 + 关键词搜，覆盖全面

**最直接的效果：** 我在手机飞书上发一条消息，OpenClaw Agent 自动调用底层检索，帮我找到知识库里最相关的内容。**所有数据的汇总、检索、回答，全部在飞书对话中完成。**

#### 3️⃣ 全栈自动化（Full-Stack Automation）

从 Obsidian 写作 → 自动索引 → Agent 检索 → 飞书输出，全链路打通：

```
写日记/笔记（Obsidian）
    │ 自动保存
    ▼
增量索引（index.py，自动检测新增/修改文件）
    │ 无需手动操作
    ▼
Agent 检索（OpenClaw 底层 BM25 + ChromaDB 向量）
    │ 手机飞书直接对话
    ▼
得到答案 + 引用来源
```

### ✨ Feature 一览

| 功能 | 说明 |
|------|------|
| **💬 RAG 智能问答** | 基于知识库内容回答问题，标注引用来源 |
| **🔎 语义搜索** | 输入自然语言，返回最相关的文章（含相似度评分） |
| **📋 文档浏览** | 按年份/数据源分组浏览全部已索引文档 |
| **🔄 增量索引** | 只处理新增/修改的文件（MD5 哈希检测） |
| **📱 飞书联动** | 配合 OpenClaw，手机飞书直接检索知识库 |
| **🧩 多数据源** | 支持同时索引多个 Markdown 目录 |
| **🌙 暗色/亮色主题** | 墨砚宣纸设计风格，一键切换 |
| **🔌 API 无关** | 兼容任何 OpenAI 格式的 Embedding & LLM API |

### 🏗️ 技术架构

```
                     Streamlit Web UI
    ┌──────────────────┬──────────────────┐
    │   RAG Q&A        │  Semantic Search │  Document Browser
    └────────┬─────────┴────────┬─────────┘
             │                  │
             ▼                  ▼
    ┌──────────────────────────────────┐
    │         ChromaDB（向量检索）       │
    │   文档 · 1024 维 · 余弦相似度     │
    └──────────┬───────────────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
┌────────────┐  ┌──────────────┐
│ Embedding   │  │    LLM       │
│ API（百炼）  │  │ API（方舟）   │
└────────────┘  └──────────────┘

配合 OpenClaw 底层 BM25 全文检索，形成双引擎联动
```

### 🛠️ 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **向量数据库** | ChromaDB | 本地文件存储，零运维，Python 原生 |
| **Embedding** | 阿里百炼 text-embedding-v4 | 1024 维，优秀中文支持 |
| **LLM** | 火山方舟 GLM-5.2 | 通用 OpenAI 兼容 API |
| **前端** | Streamlit | 单文件部署，开箱即用 |
| **索引脚本** | Python + frontmatter | 解析 Markdown frontmatter，增量更新 |
| **Agent 平台** | OpenClaw | BM25 全文检索 + Agent 工作流 |
| **知识管理** | Obsidian | 原始 Markdown 文件管理 |

### 🚀 快速开始

#### 1. 环境要求
- Python 3.9+
- Embedding API Key（阿里百炼 / OpenAI 等）
- LLM API Key（火山方舟 / OpenAI / DeepSeek 等）
- （可选）Obsidian 知识库 + OpenClaw Agent

#### 2. 安装

```bash
git clone https://github.com/hardihuang/hardimindRAG
cd hardimindRAG

pip install -r requirements.txt

cp .env.example .env
# 编辑 .env 填入你的 API Key
```

#### 3. 配置数据源

编辑 `index.py` 中的 `SOURCE_CONFIGS`：

```python
SOURCE_CONFIGS = [
    {
        "name": "my_knowledge",
        "dir": "/path/to/your/obsidian/vault",  # 你的 Obsidian 仓库路径
        "label": "我的知识库",
    },
]
```

Markdown 文件推荐使用 YAML frontmatter：
```yaml
---
title: 文章标题
source: https://example.com/article
---

正文内容...
```

没有 frontmatter 的文件也能用（用文件名作为标题）。

#### 4. 构建索引

```bash
python3 index.py
```

首次索引约 2 分钟（900 篇）。后续运行只处理新增/修改的文件。

#### 5. 启动 Web UI

```bash
streamlit run app.py
```

访问 `http://localhost:8501`

#### 6. 打通飞书（配合 OpenClaw）

安装 [OpenClaw](https://openclaw.ai) 后，配置 AI Agent 调用底层 BM25 + ChromaDB 检索，
即可在手机飞书上直接对话检索知识库。

### 📁 项目结构

```
hardimindRAG/
├── app.py               # Streamlit 主应用（Q&A + 搜索 + 文档浏览）
├── index.py             # 索引构建脚本（扫描 → Embedding → 存入 ChromaDB）
├── run.sh               # 一键启动脚本
├── requirements.txt     # Python 依赖
├── .env.example         # API Key 配置模板
├── .gitignore           # 排除 chroma_db/ 和 .env
├── chroma_db/           # 自动生成的向量数据库
│   ├── chroma.sqlite3          # 向量存储
│   ├── index_state.json        # 文件哈希映射（增量更新用）
│   └── index_time.txt          # 最近索引时间
└── docs/
    ├── ARCHITECTURE.md          # 技术架构详解
    └── DEPLOYMENT.md            # 部署与运维指南
```

### 🧪 工作原理

**索引流程：**
```
扫描 .md 文件 → 解析 frontmatter → 截取前 2000 字
     → 批量 Embedding API 调用（每次 10 篇）
     → 存入 ChromaDB（余弦距离）
     → 保存 MD5 哈希（支持增量更新）
```

**搜索流程：**
```
用户输入 → Embedding API → 1024 维向量
     → ChromaDB 余弦相似度检索
     → 返回 Top-K 篇文章 + 相似度分数
```

**RAG 问答流程：**
```
用户提问 → 检索 Top-5 最相关文章
     → 拼接上下文（最多 6000 字）
     → 构建 Prompt（系统指令 + 上下文 + 历史对话 + 问题）
     → 调用 LLM API → 返回答案 + 引用来源
```

### 🔧 关键参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| Embedding 模型 | text-embedding-v4 | 可通过 `.env` 配置 |
| 向量维度 | 1024 | 随 embedding 模型变化 |
| 正文截取长度 | 2000 字符 | 输入给 embedding |
| RAG Top-K | 5 | 每次检索返回文章数 |
| 上下文上限 | 6000 字符 | 喂给 LLM 的最大内容 |
| LLM Temperature | 0.3 | 偏低，减少幻觉 |
| 对话历史 | 最近 6 轮 | 多轮对话支持 |
| 批量大小 | 10 | 每批 API 调用文章数 |

### 🔌 API 兼容性

本项目使用 **通用 OpenAI 兼容 API 客户端**，可自由切换：

| 提供商 | Embedding | LLM |
|--------|-----------|-----|
| 阿里百炼 | ✅ text-embedding-v4 | ✅ 通义千问系列 |
| 火山方舟 | ✅ | ✅ GLM、DeepSeek |
| OpenAI | ✅ text-embedding-3-* | ✅ GPT-4/3.5 |
| DeepSeek | ✅ | ✅ DeepSeek-V2/V3 |
| 任何 OpenAI 兼容 API | ✅ | ✅ |

### 🧭 扩展方向

- **更多数据源** — 同时索引多个 Obsidian 仓库或飞书文档
- **重排序** — 加入 Cross-Encoder 提升检索精度
- **分块策略** — 从整篇文章转为段落级分块
- **API 服务化** — 封装为 REST API，供其他应用调用
- **多模型** — 配置文件化管理多个 LLM 后端

### 📝 依赖

```
chromadb
streamlit
numpy
requests
python-frontmatter<1.0
python-dotenv
```

---

## English

> **Why build your own instead of using AnythingLLM?**

### 💡 Background: From AnythingLLM to Self-Built

This system was born from concrete pain points with [AnythingLLM](https://anythingllm.com/):

| Issue | AnythingLLM | ✅ HardiMind RAG |
|-------|-------------|-----------------|
| **Performance** | Runs hot and slow, especially with large corpora | Lightweight local ChromaDB, near-zero overhead |
| **Sync** | Obsidian files don't auto-sync — must manually import | **In-place vectorization** — reads Obsidian directories directly, no file transfer needed |
| **Automation** | Cannot auto-process batch files | Incremental indexing with MD5 hash detection |
| **API Access** | Closed system, no external integration | Works with OpenClaw Agent — search from your phone via Feishu/Discord |
| **Search Quality** | Vector-only | Semantic vector search + BM25 full-text dual engine |

### 🏗️ Ecosystem Architecture

This tool is not isolated — it's part of a complete **AI-native knowledge workflow**:

```
┌─────────────────────────────────────────────────────┐
│                   Obsidian Vault                     │
│          Markdown files (notes, journals, etc.)      │
│              In-place — no copying needed            │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                  HardiMind RAG                        │
│                                                      │
│  1. index.py — Scan Obsidian dir → Embedding → DB   │
│  2. app.py — Streamlit UI (Q&A + Search + Browser)  │
│  3. Auto incremental indexing via MD5 hashing        │
│                                                      │
│  Engines: BM25 full-text + ChromaDB semantic search  │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                OpenClaw Agent Platform                │
│                                                      │
│  Send message from phone → Agent calls BM25/Vector   │
│  → Returns answer + citations → Full traceability    │
│                                                      │
│  Search your knowledge base from your couch.         │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                    Output Channels                    │
│  · Streamlit Web UI (local browser)                  │
│  · Feishu IM (mobile chat search)                    │
│  · AI Agent workflows (auto research, writing, etc.)│
└──────────────────────────────────────────────────────┘
```

### 🎯 Three Core Concepts

#### 1️⃣ In-Place Vectorization

**All files in Obsidian stay where they are — no copying, no moving.**

Traditional solutions require importing files into a "knowledge base system." This tool reads your Obsidian vault directly from its original location.

- ✅ Files stay in Obsidian — you just write
- ✅ New files are auto-detected by incremental indexing
- ✅ Modified files update vectors automatically
- ✅ Zero redundant copies

#### 2️⃣ Dual-Engine Retrieval (BM25 + Vector)

The key advantage is deep integration with [OpenClaw](https://openclaw.ai) Agent platform:

- **Vector Search (ChromaDB)**: Semantic understanding — finds conceptually related content
- **BM25 Full-Text (OpenClaw)**: Keyword matching — finds literally matching content
- **Dual engine**: Coverage from both angles

**The real impact:** I send a message from my phone via Feishu, OpenClaw Agent automatically calls the retrieval engine, finds the most relevant content from my knowledge base, and returns the answer — all within the chat. **Everything — search, retrieval, response — happens in one conversation.**

#### 3️⃣ Full-Stack Automation

From Obsidian writing → auto-indexing → agent retrieval → mobile output, the entire pipeline is automated:

```
Write notes (Obsidian)
    │ auto-save
    ▼
Incremental index (auto-detect new/changed files)
    │ zero manual work
    ▼
Agent retrieval (OpenClaw BM25 + ChromaDB vector)
    │ search from your phone
    ▼
Get answers + cited sources
```

### ✨ Features

| Feature | Description |
|---------|-------------|
| **💬 RAG Q&A** | Ask questions, get answers grounded in your knowledge base with citations |
| **🔎 Semantic Search** | Find relevant documents by natural language — not just keyword matching |
| **📋 Document Browser** | Browse all indexed docs by year & source |
| **🔄 Incremental Indexing** | Only re-indexes new/modified files (MD5 detection) |
| **📱 Mobile Search** | Integrate with OpenClaw — search from Feishu/Discord on your phone |
| **🧩 Multi-Source** | Index multiple directories simultaneously |
| **🌙 Dark/Light Theme** | Elegant Chinese ink-on-paper design |
| **🔌 API Agnostic** | Works with any OpenAI-compatible embedding & LLM API |

### 🛠️ Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Vector DB** | ChromaDB | Local file-based, zero-ops |
| **Embedding** | Alibaba Bailian text-embedding-v4 | 1024-dim, great Chinese support |
| **LLM** | Volcengine Ark GLM-5.2 | OpenAI-compatible API |
| **Frontend** | Streamlit | Single-file, instant deploy |
| **Indexing** | Python + frontmatter | Markdown frontmatter parsing |
| **Agent Platform** | OpenClaw | BM25 retrieval + agent workflows |
| **Knowledge Mgmt** | Obsidian | Raw Markdown file management |

### 🚀 Quick Start

```bash
git clone https://github.com/hardihuang/hardimindRAG
cd hardimindRAG

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Configure SOURCE_CONFIGS in index.py to point to your markdown dirs

# Build index
python3 index.py

# Launch
streamlit run app.py
```

Open `http://localhost:8501`

### 📁 Project Structure

```
hardimindRAG/
├── app.py               # Streamlit web app (Q&A + Search + Browser)
├── index.py             # Index builder (scan → embed → store)
├── run.sh               # One-click start script
├── requirements.txt     # Python dependencies
├── .env.example         # API key template
├── .gitignore           # Excludes chroma_db/ and .env
└── docs/
    ├── ARCHITECTURE.md  # Architecture deep dive
    └── DEPLOYMENT.md    # Operations guide
```

---

<div align="center">

**Built with · ChromaDB · Streamlit · OpenAI-compatible APIs**  
**Powered by · OpenClaw · Obsidian**

[GitHub](https://github.com/hardihuang/hardimindRAG)

</div>
