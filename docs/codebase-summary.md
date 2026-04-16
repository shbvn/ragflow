# RAGFlow Codebase Summary

## Repository Structure

```
ragflow/
├── api/                    # Python Flask/Quart HTTP server (34K LOC)
├── rag/                    # RAG pipeline & LLM integration (35K LOC)
├── agent/                  # Visual workflow engine (15K LOC)
├── deepdoc/                # Document parsing & vision models (13K LOC)
├── internal/               # Go backend (55K LOC)
├── web/                    # React/TypeScript frontend (165K LOC)
├── docker/                 # Docker & deployment configs
├── helm/                   # Kubernetes Helm charts
├── sdk/python/             # Python client SDK
├── mcp/                    # MCP (Model Context Protocol) server
├── admin/                  # Admin CLI tool
├── tools/                  # Utility tools & integrations
├── docker-compose.yml      # Full stack local development
└── pyproject.toml          # Python project metadata
```

## Python Backend (`api/` - 34K LOC)

### Entry Point: `api/ragflow_server.py`
- Quart (async Flask) application initialization
- Blueprint registration from `api/apps/`
- Middleware: CORS, error handlers, request logging
- Server runs on port 9380 (default)

### Application Blueprints (`api/apps/`)

| Module | Purpose | LOC |
|--------|---------|-----|
| `__init__.py` | App factory, JWT auth, API token validation | 350 |
| `api_app.py` | Quart setup, error handlers | 50 |
| `canvas_app.py` | Agent workflow endpoints | 850 |
| `chunk_app.py` | Chunk management CRUD | 750 |
| `connector_app.py` | Data source connectors | 650 |
| `document_app.py` | Document upload, parsing, deletion | 1100 |
| `evaluation_app.py` | Retrieval evaluation/testing | 500 |
| `file_app.py` | File management endpoints | 650 |
| `kb_app.py` | Knowledge base CRUD | 1300 |
| `llm_app.py` | LLM configuration endpoints | 400 |
| `system_app.py` | System health, stats | 200 |
| `tenant_app.py` | Multi-tenant management | 350 |
| `user_app.py` | User authentication, profile | 500 |
| `mcp_server/` | MCP tool exposure | 150 |
| `restful_apis/` | REST v1 endpoints | 2000 |
| `sdk/` | SDK endpoints (session SSE, agents) | 800 |
| `services/` | Business logic layer | 1500 |
| `auth/` | OAuth (OIDC, GitHub), password reset | 600 |

### Database Layer (`api/db/`)
- **ORM:** Peewee (SQLAlchemy alternative)
- **Models:** `db_models.py` (~700 LOC, 35+ tables)
- **Entities:**
  - User, Tenant, Team, Role, Permission
  - KnowledgeBase, Document, Chunk, DocumentRunStatus
  - Conversation, Message, Dialog
  - Canvas, CanvasRunStatus
  - LLM, FileObj
  - ConnectorTemplate, DataSource
  - Task (async job queue)
- **Services:** `db/services/` (document, kb, canvas, conversation, etc.)

### Authentication & Authorization (`api/apps/auth/`)
- JWT token generation & validation
- API token (Bearer token) support
- OAuth2 flows (OIDC, GitHub)
- Password reset via email
- Session management

### SDK Endpoints (`api/apps/sdk/`)
- **`session.py`:** SSE streaming for chat
- **`doc.py`:** Document listing, upload via SDK
- **`agents.py`:** Agent execution via SDK

## RAG Pipeline (`rag/` - 35K LOC)

### Chunking Strategies (`rag/app/`)
13 domain-specific chunkers:
1. **naive** — Fixed chunk size
2. **paper** — Academic paper (abstract, intro, conclusion)
3. **book** — Book structure (chapters, sections)
4. **laws** — Legal documents (articles, clauses)
5. **manual** — User-defined chunk points
6. **qa** — Question-answer pairs
7. **table** — Preserve table structure
8. **resume** — Extract sections (education, experience)
9. **picture** — Image-only documents
10. **presentation** — Slides (title, body, notes)
11. **audio** — Transcript with timestamps
12. **email** — Message threads
13. **tag** — User-defined tags
14. **one** — Single large chunk

### New Processing Pipeline (`rag/flow/`)
Graph-based pipeline executor:
- **File → Parser** (detect file type, load)
- **Parser → Chunker** (split into logical units)
- **Chunker → Extractor** (extract metadata, keywords)
- **Extractor → Tokenizer** (count tokens)
- **Output:** Chunks with metadata, token count

### LLM Integration (`rag/llm/`)
Abstractions over 40+ providers via **litellm**:
- **Chat:** `chat_completion()`, `stream_chat_completion()`
- **Embedding:** `embedding()`, supports 30+ embedding models
- **Reranking:** `rerank()` with BGE, jina, Cohere
- **Vision:** OCR, layout analysis, image understanding
- **TTS/ASR:** Text-to-speech, speech-to-text
- Providers: OpenAI, Claude, DeepSeek, Moonshot, LLaMA, local models

### Hybrid Search (`rag/nlp/search.py`)
**Dealer class** combines three retrieval strategies:
1. **BM25 (lexical):** Elasticsearch's native full-text search
2. **Vector (semantic):** HNSW ANN from embedding index
3. **RRF (fusion):** Reciprocal Rank Fusion combines top-k results

Custom tokenizer in `rag/nlp/rag_tokenizer.py`:
- Chinese + English dual-mode
- Handles mixed text, punctuation, numbers
- Token count accurate for LLM context windows

### GraphRAG (`rag/graphrag/`)
- **Entity extraction:** Identify persons, orgs, locations, concepts
- **Community detection:** Leiden algorithm for hierarchical clustering
- **Graph search:** Find relationships between entities
- Builds knowledge graph from documents

### RAPTOR (`rag/raptor.py`)
**Recursive Abstractive Summarization Tree:**
- Hierarchical clustering of chunks
- Abstractive summaries at each level
- Enables retrieval at multiple granularities

### Task Worker (`rag/svr/task_executor.py`)
- Consumes tasks from Redis Streams
- Dispatches to chunking, embedding workers
- Handles retries, error logging
- Parallel processing with worker pools

### Storage Connectors (`rag/utils/`)
Pluggable storage backends:
- **Search engines:** Elasticsearch, OpenSearch, Infinity, OceanBase
- **Object storage:** MinIO, S3, GCS, Azure Blob, Alibaba OSS
- **Cache:** Redis/Valkey
- **Databases:** MySQL, PostgreSQL

## Agent System (`agent/` - 15K LOC)

### Core Graph Engine (`agent/canvas.py`)
- **Canvas:** Nodes (components) + edges (connections)
- **Graph executor:** DAG traversal, async execution
- **SSE streaming:** Real-time workflow feedback
- State persistence: save/load canvas definitions

### Components (`agent/component/` - 20+)

**Control Flow:**
- Begin, End, Invoke
- Switch (conditional branching)
- Iteration (loop with condition)
- Loop (for/while)
- AwaitResponse (pause for user input)

**Processing:**
- **LLM:** Chat with context
- **Agent:** Agentic reasoning with tool use
- **Categorize:** Classify text into categories
- **Message:** Format or transform text
- **Retrieval:** Query knowledge base
- **Reranker:** Reorder search results
- **WebCrawler:** Fetch web content

**Data Operations:**
- VariableAssignment, VariableSelector
- Variable operators (append, merge, filter)
- String transforms (split, join, regex)
- Data transforms (JSON, CSV parsing)

**Integration:**
- Http (call external APIs)
- ExecuteSQL (query databases)
- ExcelProcessor (read/write Excel)
- DocsGenerator (create markdown/HTML)
- EmailSend

### Tools (`agent/tools/` - 20+)
**Search & Web:**
- Retrieval (from knowledge base)
- WebCrawler, Tavily (web search)
- Google, DuckDuckGo, Bing search
- Wikipedia, ArXiv, PubMed

**Data & APIs:**
- GitHub API (repo/issue queries)
- Yahoo Finance (stock data)
- SQL execution (database queries)
- Code execution (Python/JavaScript)

**Utilities:**
- DeepL (translation)
- Email (send via SMTP)
- PDF generator, CSV processor

### Plugin System (`agent/plugin/`)
- **GlobalPluginManager:** Registry for custom tools
- **LLM tool plugins:** Extend LLM with custom functions
- Auto-discovery from plugins directory

### Sandbox Execution (`agent/sandbox/`)
Isolated code execution:
- **Docker containers:** Kubernetes-compatible sandbox
- **E2B:** Secure cloud sandbox
- **Alibaba Cloud:** Managed code interpreter
- **Local executor:** FastAPI-based standalone service

## Document Processing (`deepdoc/` - 13K LOC)

### Vision Models (`deepdoc/vision/`)
ONNX-based neural models:
- **OCR:** Character recognition for scanned docs
- **Layout recognition:** 10 labels (text, title, image, table, list, footer, header, page number, formula, watermark)
- **Table detection:** Identify and extract tables
- **Structure analysis:** Understand document organization

### Parsers (`deepdoc/parser/`)

| Format | Mode | Handler |
|--------|------|---------|
| PDF | AI layout | Vision + layout analysis |
| PDF | Plain text | pdfplumber |
| PDF | VLM | Vision language model |
| DOCX | - | python-docx, mammoth |
| Excel | - | openpyxl, to HTML |
| PPT | - | python-pptx, XML extraction |
| Markdown | - | Regex + AST |
| HTML | - | BeautifulSoup, html2text |
| JSON | - | json library, flatten |
| TXT | - | Raw text, auto-detect encoding |
| EPUB | - | ebooklib |
| Image | - | VLM (Claude, GPT-4V) |
| PaddleOCR | - | Baidu OCR alternative |
| MinerU | - | Advanced layout parser |
| Docling | - | IBM universal parser |

### Resume Extraction (`deepdoc/parser/resume/`)
- **Section detection:** Identify resume sections
- **Entity extraction:** Extract structured data
- **Normalization:** Standardize dates, titles

## Go Backend (`internal/` - 55K LOC)

Progressive port of Python API. Full compatibility through CGo tokenizer.

### Entry Points (`cmd/`)
- **server_main.go:** Gin HTTP server (port 9380), 16 services
- **admin_server.go:** Admin API (port 9381)
- **ragflow_cli.go:** Interactive CLI tool

### Core Services (`internal/service/`)
1. **User** — Authentication, profile management
2. **Tenant** — Multi-tenancy, workspace isolation
3. **KB (Knowledge Base)** — Dataset CRUD
4. **Document** — Document management
5. **Chunk** — Chunk CRUD, batch operations
6. **Chat** — Conversation endpoints
7. **LLM** — LLM provider configuration
8. **File** — File upload/download
9. **Connector** — Data source integration
10. **Memory** — Conversation memory
11. **Search** — Hybrid search execution
12. **System** — Health checks, stats
13. **Evaluation** — RAG evaluation
14. **Canvas** — Agent workflow execution
15. **Task** — Async job tracking
16. **Admin** — System administration

### Document Engine Interface (`internal/engine/`)
Pluggable search backend:
- **Elasticsearch:** Production-grade full-text search
- **Infinity:** Lightweight alternative
- Both support BM25, vector, metadata filtering

### CGo Tokenizer (`internal/binding/` + `internal/cpp/`)
C++ static library wrapping:
- **PCRE2:** Regex engine for pattern matching
- **OpenCC:** Chinese character conversion
- **RE2:** Google's regex library
- **DART trie:** Efficient prefix matching
- **WordNet:** English word relationships

Tokenizer pool: 2×CPU to 16×CPU analyzers
Throughput: 10K+ chunks/minute

### NLP Services (`internal/service/nlp/`)
- **QueryBuilder:** Construct search queries
- **TermWeightDealer:** TF-IDF weight calculation
- **Synonym expansion:** Expand query terms
- **Reranker:** Reorder results by relevance

### Data Access (`internal/dao/`)
**GORM ORM** with 35+ models:
- Auto-migration: create/update tables
- **Tolerance:** Works with Python-created tables
- Transactions, soft deletes, indices

### Cache Layer (`internal/cache/`)
**Redis wrapper:**
- Lua scripts for atomic operations
- Token bucket (rate limiting)
- Streams consumer groups (task distribution)
- Key-value caching

### Admin Service (`internal/admin/`)
- License validation
- User management
- Heartbeat store (node discovery)
- System statistics

### CLI Tool (`internal/cli/`)
**Lark-style parser:**
- Interactive REPL with readline
- Provider-based context engine
- Command history, auto-completion

### Storage (`internal/storage/`)
Multiple backend support:
- MinIO (local S3-compatible)
- S3 (AWS)
- OSS (Alibaba)
- GCS (Google Cloud)
- Azure Blob

## Frontend (`web/` - 165K LOC)

React 18 + TypeScript 5.9 + Vite 7 single-page application.

### Architecture
- **Routing:** react-router v7 (lazy-loaded pages)
- **State:** TanStack Query v5 (server) + Zustand (canvas UI)
- **UI:** shadcn/ui (60+ Radix primitives) + Ant Design 5 (migration in progress)
- **Styling:** Tailwind CSS 3
- **API Clients:** umi-request (legacy) + Axios (new)
- **i18n:** react-i18next (15 languages)

### Key Pages

| Page | LOC | Purpose |
|------|-----|---------|
| Agent Editor | 35K | Build workflows, test execution |
| Dataset Management | 11K | Upload docs, configure chunking |
| Chat Interface | 3K | Query knowledge base |
| Admin Dashboard | 5K | System settings, user management |
| User Settings | 12K | Profile, API keys, preferences |
| Search | 3K | Full-text search interface |
| Agent Canvas | 8K | Visual workflow editor (ReactFlow) |

### Component Library
- **shadcn/ui:** 60+ Radix UI components (Dialog, Select, Tabs, etc.)
- **Ant Design 5:** 50+ business components (Table, Form, Modal, etc.)
- **Custom components:** Layout, navigation, workflow visualization

### State Management
- **TanStack Query:** Server state (API responses, caching, invalidation)
- **Zustand:** Client state (canvas UI, sidebar toggles, theme)
- **localStorage:** Persistence (JWT token, preferences)

### API Integration
- **Dual clients:** Legacy umi-request + modern Axios
- **SSE:** eventsource-parser for streaming chat responses
- **Error handling:** Centralized error boundary
- **Auth:** RSA-encrypted login, JWT token in localStorage

### i18n (Internationalization)
- 15 supported languages (EN, ZH, ES, FR, DE, JA, KO, etc.)
- Lazy-loaded translation files
- Language switcher in settings

## Infrastructure & Deployment

### Docker Compose
**Local development stacks:**
- `docker-compose.yml` — RAGFlow server + all services (CPU/GPU profiles)
- `docker-compose-base.yml` — Just backing services (MySQL, Redis, MinIO, ES)

**Services:**
- **ragflow-server:** Python API (port 9380) or Go (9384)
- **ragflow-admin:** Admin API (port 9381)
- **nginx:** Reverse proxy (80, 443)
- **MySQL:** Database
- **MinIO:** Object storage
- **Redis/Valkey:** Cache, task queue
- **Elasticsearch/OpenSearch/Infinity:** Search engine
- **OceanBase:** Distributed database (optional)

**Profiles:**
- `cpu` — CPU-only inference
- `gpu` — NVIDIA CUDA support

### Dockerfile
- **Base:** Ubuntu 24.04
- **Python:** 3.12
- **Node.js:** 20
- **Tools:** Java (Tika), Chrome, FFmpeg
- **Multi-stage build:** Optimized image size

### Kubernetes & Helm
Full Helm charts in `helm/`:
- StatefulSets for databases
- Deployments for API servers
- ConfigMaps for service_conf.yaml
- Secrets for credentials
- Persistent volumes for MinIO

### Configuration
- **`docker/.env`:** Environment variables
- **`docker/service_conf.yaml`:** Backend config (shared by Python + Go)
  - LLM provider credentials
  - Database connection strings
  - Search engine endpoints
  - Task worker settings
- **`conf/llm_factories.json`:** LLM provider catalog (40+ entries)
- **`conf/mapping.json`:** Elasticsearch index schemas

## SDK & Client Libraries

### Python SDK (`sdk/python/`)
**Package:** `ragflow-sdk` v0.24.0

Entities:
- **RAGFlow:** Client initialization
- **DataSet:** Knowledge base CRUD
- **Document:** Upload, list, retrieve
- **Chunk:** Query, update metadata
- **Chat:** Session, message history
- **Session:** Conversation session
- **Agent:** Workflow execution
- **Memory:** Knowledge graph memory

Features:
- Type hints (beartype validation)
- Async support (requests)
- Retry logic, error handling
- Context managers for resources

### MCP Server (`mcp/`)
**Model Context Protocol** integration:
- Starlette/uvicorn ASGI
- Tool exposure: `ragflow_retrieval`
- SSE + Streamable HTTP transports
- Self-host or multi-tenant modes

### Admin CLI (`admin/`)
Interactive command-line tool:
- **Lark parser:** Command parsing
- **readline REPL:** History, auto-completion
- **Provider context:** Dynamic command context
- Features: user mgmt, system config, troubleshooting

## Testing & CI/CD

### Python Tests
- **Framework:** pytest
- **Markers:** p1, p2, p3 (priority levels)
- **Coverage:** >75% for critical paths
- **Location:** `test/` directory

### Frontend Tests
- **Framework:** Jest + React Testing Library
- **Snapshot tests:** UI component structure
- **Integration tests:** API mocking

### API Tests
- HTTP API tests in `test/` (requests library)
- SDK tests in `sdk/python/test/`

### GitHub Actions
- Pre-commit hooks (linting, type checks)
- Unit test runs on PR
- Docker image build & push on merge to main

## Key Dependencies

### Python (pyproject.toml)
**Web Framework:** Quart, Flask-CORS, Flask-Mail  
**Database:** Peewee, SQLAlchemy (admin), psycopg2, PyMySQL, pymongo  
**LLM:** openai, anthropic, litellm, cohere, groq  
**Search:** elasticsearch-dsl, redis, minio-client  
**Document Parsing:** pdfplumber, pypdf, python-docx, openpyxl, mammoth  
**Vision:** onnxruntime, PIL, opencv-python, torch, timm  
**NLP:** scikit-learn, networkx, umap-learn, pandas, numpy  
**Async:** aiohttp, asyncio, websockets  
**CLI:** Lark, Typer, Rich  

### Go (go.mod)
**Framework:** Gin, GORM  
**Database:** go-sql-driver/mysql, lib/pq, go-mysql-org/go-mysql  
**Search:** go-elasticsearch, go-redis, minio-go  
**LLM:** openai-go, anthropic-sdk-go  
**Utilities:** zap (logging), viper (config), spf13/cobra (CLI)  

### Frontend (package.json)
**Framework:** React 18, react-router 7, Vite 7  
**State:** @tanstack/react-query 5, zustand  
**UI:** shadcn/ui, @radix-ui/*, antd 5, tailwindcss 3  
**Visualization:** @xyflow/react (ReactFlow 12)  
**API:** axios, umi-request, eventsource-parser  
**i18n:** react-i18next  
**Editor:** monaco-editor, lexical (rich text)  
**Visualization:** recharts (charts)  

---

**Document Version:** 0.24.0  
**Last Updated:** 2026-04-16  
**Scope:** Complete codebase overview for developers and documentation purposes
