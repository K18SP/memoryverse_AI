# MemoryVerse AI — Digital Identity System
### MemoryVerse AI '26 Hackathon Submission

> *"I never have to search through folders again."*

MemoryVerse AI transforms a student's fragmented academic and professional data into a structured, searchable, and intelligent knowledge repository powered by RAG, semantic embeddings, and a live knowledge graph.

---

## Live Demo

> Upload documents → Ask questions in plain English → Watch your career graph build itself.

```
http://localhost:3000
```

---

## The Problem

Every student accumulates certificates, resumes, project reports, internship letters, and GitHub repositories over years. This data is scattered across folders, emails, and cloud drives. Traditional storage platforms save files they cannot **understand** a person's journey.

## Our Solution

MemoryVerse AI does 5 things no file storage system can:

| # | Feature | What it does |
|---|---|---|
| 1 | **AI Ingestion** | Reads PDFs, DOCX, images (OCR), GitHub repos, Markdown |
| 2 | **Auto-Categorization** | Classifies every document into Education / Experience / Projects / Skills / Achievements |
| 3 | **Knowledge Graph** | Maps Certification → Skill → Project → Internship as typed relationships |
| 4 | **Smart Retrieval** | Answers natural language questions with source citations |
| 5 | **Timeline** | Chronological visual of your entire academic journey |

**Beyond the Brief:**
- 🎯 **Skill Gap Analyst** -> compare your skills vs any job role, get a learning roadmap
- 🤖 **AI Interview Coach** -> practice with questions grounded in your actual documents

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                              │
│   PDF │ DOCX │ Image (OCR) │ GitHub URL │ Markdown/TXT         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                             │
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │   Chunker   │───▶│  Embeddings  │───▶│  Qdrant Vector   │   │
│  │ 512 tokens  │    │ MiniLM-L6-v2 │    │  DB (Hybrid)     │   │
│  │ 50 overlap  │    │  384 dims    │    │  Dense + Sparse  │   │
│  └─────────────┘    └──────────────┘    └──────────────────┘   │
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │   Entity    │───▶│  Knowledge   │───▶│   NetworkX       │   │
│  │  Extractor  │    │    Graph     │    │   DiGraph        │   │
│  │  (Mistral)  │    │ Nodes+Edges  │    │   + D3.js UI     │   │
│  └─────────────┘    └──────────────┘    └──────────────────┘   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                               │
│                                                                 │
│  Smart Q&A    │  Timeline  │  Gap Analysis  │  Interview Coach  │
│  (RAG + LLM)  │  (Chron.)  │  (Radar Chart) │  (STAR Scoring)  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | FastAPI (Python 3.12) | Async REST API |
| LLM | Mistral 7B via Ollama | RAG generation, entity extraction, categorization |
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) | 384-dim semantic vectors — runs locally, free |
| Vector DB | Qdrant (standalone binary) | Hybrid search: dense + sparse (BM25) |
| Graph | NetworkX DiGraph | Knowledge graph with typed edges |
| OCR | Tesseract + PyMuPDF | Scanned PDF and image text extraction |
| Frontend | React + TailwindCSS + D3.js | Interactive UI and graph visualization |
| Search | RRF Fusion (Dense + BM25) | Reciprocal Rank Fusion for best retrieval |

**100% Free & Local, No paid API keys required.**

---

## Key AI/ML Techniques

### 1. Hybrid Search with RRF Fusion
```
Query → Dense Embedding → Qdrant cosine search
      → BM25 tokenized  → Lexical scoring
      → RRF(rank_dense, rank_bm25) → Top-K results
```
Dense search finds semantically similar content. BM25 nails exact names and acronyms. RRF fusion combines both for maximum accuracy.

### 2. RAG Pipeline
```
User Query → Embed → Retrieve Top-5 chunks → Inject into Mistral prompt
→ Generate cited answer → Return with source documents + confidence score
```
Every answer is grounded in retrieved documents. Confidence threshold of 0.015 prevents hallucination, if no relevant chunks found, system says so.

### 3. Knowledge Graph Construction
```
Document chunk → Mistral entity extraction → {skills, tools, orgs, roles, topics}
→ NetworkX nodes (color-coded by type) → Typed edges (CONTAINS, VALIDATES_SKILL, USED_IN)
→ D3.js force-directed visualization → Click node → see all connections
```

### 4. Zero-Shot Categorization
Each chunk is classified into a 5-category taxonomy using Mistral with a structured JSON prompt. No training data required.

---

## Project Structure

```
memoryverse-ai/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Centralized settings
│   ├── api/
│   │   └── routes.py              # All API endpoints
│   ├── ingestion/
│   │   ├── router.py              # File type dispatcher
│   │   ├── pdf_parser.py          # PyMuPDF + OCR fallback
│   │   ├── ocr_engine.py          # Tesseract wrapper
│   │   ├── docx_parser.py         # DOCX extraction
│   │   ├── markdown_parser.py     # MD/TXT extraction
│   │   └── github_fetcher.py      # GitHub API integration
│   ├── embeddings/
│   │   ├── chunker.py             # Token-aware chunker (tiktoken)
│   │   └── generator.py           # sentence-transformers embeddings
│   ├── vector_store/
│   │   ├── qdrant_client.py       # Qdrant init + upsert
│   │   └── schema.py              # DocChunk payload schema
│   ├── graph/
│   │   ├── entity_extractor.py    # Mistral NER extraction
│   │   ├── knowledge_graph.py     # NetworkX graph engine
│   │   └── categorizer.py         # Zero-shot classification
│   ├── retrieval/
│   │   ├── hybrid_search.py       # Dense + BM25 + RRF fusion
│   │   └── rag_chain.py           # Full RAG pipeline
│   └── features/
│       ├── gap_analyst.py         # Skill gap analysis
│       └── interview_coach.py     # Personalized interview prep
└── frontend/
    └── src/
        ├── pages/
        │   ├── Dashboard.jsx      # AI search + suggested prompts
        │   ├── Upload.jsx         # Drag-and-drop with live log
        │   ├── Timeline.jsx       # Chronological journey view
        │   ├── Graph.jsx          # D3.js knowledge graph
        │   ├── GapAnalyst.jsx     # Skill gap + radar chart
        │   └── InterviewCoach.jsx # STAR-scored interview practice
        ├── App.js                 # Router + sidebar
        └── api.js                 # Axios API client
```

---

## Local Setup (5 Commands)

### Prerequisites
- Python 3.12
- Node.js 18+
- [Ollama](https://ollama.com) with Mistral: `ollama pull mistral`
- [Qdrant](https://qdrant.tech) binary for Windows

### Run

```bash
# 1. Clone and enter project
git clone https://github.com/YOUR_USERNAME/memoryverse-ai
cd memoryverse-ai

# 2. Backend setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. Start Qdrant (in a separate terminal)
D:\qdrant\qdrant.exe

# 4. Start backend
uvicorn backend.main:app --reload --port 8000

# 5. Start frontend (in a separate terminal)
cd frontend
npm install
npm start
```

Open `http://localhost:3000` — done.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/ingest` | Upload file or GitHub URL |
| POST | `/api/v1/search` | Natural language RAG search |
| POST | `/api/v1/graph/{user_id}/build` | Build knowledge graph |
| GET | `/api/v1/graph/{user_id}` | Get D3.js graph data |
| GET | `/api/v1/graph/{user_id}/node/{id}` | Get node neighbours |
| POST | `/api/v1/gap-analysis` | Skill gap vs target role |
| POST | `/api/v1/interview/question` | Generate interview question |
| POST | `/api/v1/interview/evaluate` | Score answer with STAR feedback |

---

## Innovation Highlights

### Why this wins

1. **No paid APIs** -> Mistral runs locally via Ollama. Embeddings run locally via sentence-transformers. Zero cost to run.

2. **Hybrid search beats pure vector search** -> exact names (companies, tools) are found by BM25; semantic concepts found by dense vectors. RRF fusion gets the best of both.

3. **Knowledge Graph is queryable** -> not just a pretty picture. Every node click reveals connections. The graph powers Gap Analysis by reading skill nodes directly.

4. **Gap Analyst is unique** -> no competing submission will compare student skills to job roles and generate a weekly learning roadmap. This turns a document organizer into a career growth tool.

5. **Interview Coach is personal** -> questions are grounded in the student's actual documents. A generic chatbot asks "tell me about yourself." MemoryVerse asks "why did you choose XGBoost over linear models in your specific project?"

---

## Team

Built for **MemoryVerse AI '26** hackathon on Wooble.org

---

*"I never have to search through folders again and this system actually helps me grow."*
