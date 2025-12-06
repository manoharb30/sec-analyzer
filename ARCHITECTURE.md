# SEC Filing Analyzer - System Architecture

## Overview
A multi-agent AI system for analyzing SEC 10-K/10-Q filings with real-time progress streaming.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   USER                                          │
│                              (Web Browser)                                      │
└─────────────────────────────────┬───────────────────────────────────────────────┘
                                  │
                                  │ HTTP/SSE
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js 14)                                   │
│                         Port: 3000                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │   Home Page     │  │  Analysis Page  │  │  API Routes     │                 │
│  │   (page.tsx)    │  │  ([ticker])     │  │  /api/analyze/* │                 │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘                 │
│           │                    │                    │                           │
│           │    ┌───────────────┴───────────────┐    │                           │
│           │    │     EventSource (SSE)         │    │                           │
│           │    │   Real-time Progress Bar      │    │                           │
│           │    └───────────────┬───────────────┘    │                           │
└───────────┼────────────────────┼────────────────────┼───────────────────────────┘
            │                    │                    │
            │                    │ SSE Stream         │
            │                    ▼                    │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (FastAPI)                                       │
│                         Port: 8000                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        API Endpoints                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │   │
│  │  │ GET /        │  │POST /analyze │  │GET /analyze/ │  │POST         │  │   │
│  │  │ Health Check │  │ Sync Mode    │  │   stream     │  │ /question   │  │   │
│  │  └──────────────┘  └──────────────┘  └──────┬───────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────┼───────────────────────────┘   │
│                                                 │                               │
│  ┌──────────────────────────────────────────────┼───────────────────────────┐   │
│  │                    SSE STREAMING ENGINE                                  │   │
│  │                                              │                           │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌─▼────────────┐              │   │
│  │   │   Download   │───▶│    Index     │───▶│   Analyze    │              │   │
│  │   │   (Thread)   │    │   (Thread)   │    │   (Thread)   │              │   │
│  │   └──────────────┘    └──────────────┘    └──────────────┘              │   │
│  │          │                   │                    │                      │   │
│  │          ▼                   ▼                    ▼                      │   │
│  │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │   │              Progress Queue (Thread-Safe)                       │   │   │
│  │   │   {"step": "downloading", "progress": 5, "message": "..."}     │   │   │
│  │   │   {"step": "indexed", "progress": 25, "message": "..."}        │   │   │
│  │   │   {"step": "complete", "progress": 100, "result": {...}}       │   │   │
│  │   └─────────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
            │                    │                    │
            │                    │                    │
            ▼                    ▼                    ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│    SEC EDGAR      │  │     Pinecone      │  │      OpenAI       │
│  (Data Source)    │  │  (Vector Store)   │  │   (LLM/Embed)     │
│                   │  │                   │  │                   │
│ • 10-K Filings    │  │ • Chunk Storage   │  │ • GPT-4o-mini     │
│ • 10-Q Filings    │  │ • Semantic Search │  │ • text-embedding  │
│ • Company Data    │  │ • Namespace/Ticker│  │   -3-small        │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

---

## Component Details

### 1. Frontend (Next.js 14)

```
lookinsight-frontend/
├── app/
│   ├── page.tsx                    # Home page with search
│   ├── analysis/[ticker]/page.tsx  # Analysis page with SSE
│   └── api/
│       └── analyze/
│           ├── route.ts            # POST /api/analyze (sync)
│           └── stream/route.ts     # GET /api/analyze/stream (SSE proxy)
├── components/
│   ├── SearchBar.tsx               # Ticker input
│   ├── MetricsBar.tsx              # Financial metrics display
│   ├── MarkdownDisplay.tsx         # Report renderer
│   └── TabNavigation.tsx           # Tab switching
└── lib/
    └── api.ts                      # API client functions
```

**Key Technologies:**
- Next.js 14 (App Router)
- React 18 with Hooks
- SWR for data fetching
- Framer Motion for animations
- EventSource for SSE

---

### 2. Backend (FastAPI)

```
api/
├── main.py                         # FastAPI app & endpoints
├── __init__.py
│
agents/
├── direct_analyzer.py              # RAG-based analyzer (main)
├── sec_crew.py                     # CrewAI multi-agent (legacy)
│
tools/
├── sec_downloader.py               # SEC EDGAR downloader
│
rag/
├── pinecone_rag.py                 # Pinecone RAG system
```

**Key Technologies:**
- FastAPI with async support
- Uvicorn ASGI server
- LangChain for LLM orchestration
- Pinecone for vector storage

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ANALYSIS PIPELINE                                  │
└─────────────────────────────────────────────────────────────────────────────┘

   User enters "AAPL"
         │
         ▼
┌─────────────────┐
│  1. DOWNLOAD    │ ─────────────────────────────────────────────────────────┐
│                 │                                                           │
│  SEC Downloader │◀──── GET company_tickers.json ◀──── SEC.gov              │
│  Tool           │◀──── GET CIK{cik}.json        ◀──── data.sec.gov         │
│                 │◀──── GET 10-K HTML/PDF        ◀──── SEC EDGAR            │
└────────┬────────┘                                                           │
         │                                                                    │
         │ filing_text (HTML parsed)                                          │
         ▼                                                                    │
┌─────────────────┐                                                           │
│  2. CHUNK       │                                                           │
│                 │                                                           │
│  Smart Chunking │ ─── Preserves tables                                      │
│  • 1500 chars   │ ─── Detects SEC sections (Item 1, 1A, 7, 8...)           │
│  • 200 overlap  │ ─── Tags content type (financial_table, risk_factor)     │
└────────┬────────┘                                                           │
         │                                                                    │
         │ chunks[] with metadata                                             │
         ▼                                                                    │
┌─────────────────┐      ┌─────────────────┐                                  │
│  3. EMBED       │      │    OpenAI       │                                  │
│                 │─────▶│  Embeddings     │                                  │
│  OpenAI         │◀─────│  API            │                                  │
│  Embeddings     │      │                 │                                  │
└────────┬────────┘      └─────────────────┘                                  │
         │                                                                    │
         │ vectors[] (1536 dimensions)                                        │
         ▼                                                                    │
┌─────────────────┐      ┌─────────────────┐                                  │
│  4. INDEX       │      │    Pinecone     │                                  │
│                 │─────▶│  Vector DB      │                                  │
│  Pinecone       │      │                 │                                  │
│  Upsert         │      │  namespace=AAPL │                                  │
└────────┬────────┘      └─────────────────┘                                  │
         │                                                                    │
         │ indexed (156 chunks)                                               │
         ▼                                                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. RAG QUERIES (Retrieval-Augmented Generation)                            │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Financials    │  │     Risks       │  │    Business     │             │
│  │                 │  │                 │  │                 │             │
│  │ • Revenue?      │  │ • Top 5 risks?  │  │ • Description?  │             │
│  │ • Net income?   │  │ • Legal issues? │  │ • Products?     │             │
│  │ • Gross margin? │  │ • Competition?  │  │ • Competitors?  │             │
│  │ • Cash flow?    │  │                 │  │                 │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           ▼                    ▼                    ▼                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      PINECONE SEMANTIC SEARCH                        │   │
│  │                                                                      │   │
│  │   Query ──▶ Embed ──▶ Search (top_k=5) ──▶ Relevant Chunks          │   │
│  └──────────────────────────────────┬──────────────────────────────────┘   │
│                                     │                                       │
│                                     ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         GPT-4o-mini                                  │   │
│  │                                                                      │   │
│  │   Context: [retrieved chunks]                                        │   │
│  │   Question: "What is the total revenue?"                            │   │
│  │   ──────────────────────────────────────                            │   │
│  │   Answer: "Total revenue for fiscal 2024 was $391 billion..."       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         │ financials, risks, business
         ▼
┌─────────────────┐
│  6. REPORT      │
│                 │
│  GPT-4o-mini    │ ─── Synthesizes all extracted data
│  Report Writer  │ ─── Generates structured markdown report
│                 │ ─── Includes: Executive Summary, Financials,
│                 │     Business Overview, Risk Assessment, Key Takeaways
└────────┬────────┘
         │
         │ Investment Report (Markdown)
         ▼
┌─────────────────┐
│  7. RESPONSE    │
│                 │
│  SSE Stream     │ ─── {"step": "complete", "progress": 100, "result": {...}}
│  to Frontend    │
└─────────────────┘
```

---

## SSE (Server-Sent Events) Flow

```
┌──────────────┐                    ┌──────────────┐
│   Browser    │                    │   Backend    │
│  EventSource │                    │   FastAPI    │
└──────┬───────┘                    └──────┬───────┘
       │                                   │
       │ GET /analyze/stream?ticker=AAPL   │
       │──────────────────────────────────▶│
       │                                   │
       │   data: {"step":"downloading",    │
       │◀──────── "progress":5}            │
       │                                   │
       │   data: {"step":"downloaded",     │
       │◀──────── "progress":10}           │
       │                                   │
       │   data: {"step":"indexing",       │
       │◀──────── "progress":10}           │
       │                                   │
       │   data: {"step":"indexed",        │
       │◀──────── "progress":25}           │
       │                                   │
       │   data: {"step":"financials",     │
       │◀──────── "progress":35}           │
       │                                   │
       │   data: {"step":"risks",          │
       │◀──────── "progress":55}           │
       │                                   │
       │   data: {"step":"business",       │
       │◀──────── "progress":75}           │
       │                                   │
       │   data: {"step":"report",         │
       │◀──────── "progress":90}           │
       │                                   │
       │   data: {"step":"complete",       │
       │◀──────── "progress":100,          │
       │          "result":{...}}          │
       │                                   │
       │ Connection closed                 │
       │◀─────────────────────────────────│
```

---

## AI Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DIRECT SEC ANALYZER (RAG-Based)                        │
│                                                                             │
│  This is NOT a traditional multi-agent system with autonomous agents.      │
│  Instead, it uses a structured RAG pipeline with specialized query steps.  │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────┐
                    │      DirectSECAnalyzer          │
                    │      (Orchestrator)             │
                    └─────────────────┬───────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│  _extract_        │     │  _extract_        │     │  _extract_        │
│  financials()     │     │  risks()          │     │  business()       │
│                   │     │                   │     │                   │
│  Queries:         │     │  Query:           │     │  Queries:         │
│  • Revenue        │     │  • Top 5 risks    │     │  • Description    │
│  • Net income     │     │                   │     │  • Products       │
│  • Gross margin   │     │  Uses:            │     │  • Competition    │
│  • Operating inc  │     │  top_k=8 chunks   │     │                   │
│  • Cash           │     │                   │     │  Uses:            │
│  • Debt           │     │                   │     │  top_k=5 chunks   │
│  • EPS            │     │                   │     │                   │
│                   │     │                   │     │                   │
│  Uses:            │     │                   │     │                   │
│  top_k=5 chunks   │     │                   │     │                   │
└─────────┬─────────┘     └─────────┬─────────┘     └─────────┬─────────┘
          │                         │                         │
          │                         │                         │
          └─────────────────────────┼─────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │      _generate_report()         │
                    │                                 │
                    │  Combines all extracted data    │
                    │  into structured investment     │
                    │  report using GPT-4o-mini       │
                    │                                 │
                    │  Sections:                      │
                    │  1. Executive Summary           │
                    │  2. Financial Highlights        │
                    │  3. Business Overview           │
                    │  4. Risk Assessment             │
                    │  5. Key Takeaways               │
                    └─────────────────────────────────┘
```

---

## RAG (Retrieval-Augmented Generation) System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SECFilingRAG Class                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  INDEXING PIPELINE                                                          │
│                                                                             │
│  Filing Text ──▶ Smart Chunking ──▶ Embedding ──▶ Pinecone Upsert          │
│                                                                             │
│  Smart Chunking Features:                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  • Chunk size: 1500 chars with 200 overlap                         │    │
│  │  • Preserves financial tables intact (markdown format)             │    │
│  │  • Detects SEC sections: Item 1, 1A, 1B, 2, 3, 7, 7A, 8, 9...     │    │
│  │  • Tags content type: financial_table, financial_data, risk_factor│    │
│  │  • Stores rich metadata with each chunk                            │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Metadata per chunk:                                                        │
│  {                                                                          │
│    "ticker": "AAPL",                                                        │
│    "filing_type": "10-K",                                                   │
│    "filing_date": "2024-10-31",                                            │
│    "section": "financial_statements",                                       │
│    "has_table": true,                                                       │
│    "content_type": "financial_table",                                       │
│    "chunk_index": 42,                                                       │
│    "text": "| Revenue | $391B | ... |"                                     │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  QUERY PIPELINE                                                             │
│                                                                             │
│  Question ──▶ Embed ──▶ Pinecone Search ──▶ Context ──▶ GPT-4o-mini ──▶ Answer │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Query Enhancement:                                                   │  │
│  │  • Filter by section (e.g., "risk_factors", "financial_statements") │  │
│  │  • Filter by content_type (e.g., "financial_table")                 │  │
│  │  • Namespace isolation per ticker                                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Prompt Template:                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  "You are an expert financial analyst. Answer based ONLY on the     │  │
│  │   provided context from {ticker}'s SEC filing.                      │  │
│  │                                                                      │  │
│  │   IMPORTANT: Extract EXACT numbers from financial tables.           │  │
│  │   Cite SEC sections (e.g., 'From Item 7 - MD&A').                   │  │
│  │                                                                      │  │
│  │   Context: {retrieved_chunks}                                        │  │
│  │   Question: {question}"                                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
sec-analyzer/
│
├── api/
│   ├── __init__.py
│   └── main.py                 # FastAPI endpoints
│
├── agents/
│   ├── direct_analyzer.py      # Main RAG-based analyzer
│   └── sec_crew.py             # CrewAI multi-agent (legacy)
│
├── tools/
│   └── sec_downloader.py       # SEC EDGAR download tool
│
├── rag/
│   └── pinecone_rag.py         # Pinecone RAG system
│
├── lookinsight-frontend/       # Next.js frontend
│   ├── app/
│   │   ├── page.tsx            # Home
│   │   ├── analysis/[ticker]/
│   │   │   └── page.tsx        # Analysis with SSE
│   │   └── api/
│   │       └── analyze/
│   │           ├── route.ts    # Sync analyze
│   │           └── stream/
│   │               └── route.ts # SSE proxy
│   ├── components/
│   │   ├── SearchBar.tsx
│   │   ├── MetricsBar.tsx
│   │   ├── MarkdownDisplay.tsx
│   │   └── TabNavigation.tsx
│   └── lib/
│       └── api.ts
│
├── requirements.txt
├── .env                        # API keys
└── ARCHITECTURE.md             # This file
```

---

## Environment Variables

```
# OpenAI
OPENAI_API_KEY=sk-...

# Pinecone
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1

# Backend URL (for frontend)
PYTHON_API_URL=http://localhost:8000
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/analyze` | POST | Synchronous analysis |
| `/analyze/stream` | GET | SSE streaming analysis |
| `/analyze/async` | POST | Start async job |
| `/analysis/{job_id}` | GET | Get async job status |
| `/question` | POST | Follow-up question (RAG) |
| `/suggested-questions/{ticker}` | GET | Get suggested questions |
| `/filing/{ticker}` | DELETE | Delete indexed filing |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.13, Uvicorn |
| LLM | OpenAI GPT-4o-mini |
| Embeddings | OpenAI text-embedding-3-small |
| Vector DB | Pinecone (Serverless) |
| Data Source | SEC EDGAR |
| Streaming | Server-Sent Events (SSE) |

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Download time | ~3-5 seconds |
| Indexing time | ~10-20 seconds |
| RAG queries | ~30 seconds |
| Report generation | ~10 seconds |
| **Total time** | **~60-90 seconds** |
| Chunks per filing | 100-300 |
| Model | GPT-4o-mini (fast, high rate limit) |

---

*Generated by SEC Filing Analyzer System*
