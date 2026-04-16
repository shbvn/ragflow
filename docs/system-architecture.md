# System Architecture

## High-Level Overview

RAGFlow is a distributed, multi-tenant RAG platform with three independently deployable layers:

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React/TS)                      │
│  Agent Editor | Dataset Manager | Chat | Admin Dashboard    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/SSE
┌─────────────────────────┴────────────────────────────────────┐
│                    Nginx Reverse Proxy                        │
│  Routes /api/v1/* to Python (9380) or Go (9384) [configurable]
│         /admin/* to Admin API (9381)
│         /mcp to MCP Server (9382)
└────────────┬───────────────────────┬────────────────────────┘
             │                       │
     ┌───────▼──────────┐  ┌────────▼─────────┐
     │   Python API     │  │     Go API       │
     │   (Quart)        │  │     (Gin)        │
     │   Port 9380      │  │   Port 9384      │
     └───────┬──────────┘  └────────┬─────────┘
             │                      │
             └──────────┬───────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
    ┌───▼───┐      ┌───▼───┐      ┌───▼──────┐
    │ MySQL │      │ Redis │      │MinIO/S3  │
    │   8   │      │Valkey │      │          │
    └───────┘      └───┬───┘      └──────────┘
                       │
                   ┌───▼──────────┐
                   │ES/OpenSearch/│
                   │Infinity      │
                   └──────────────┘

Task Queue:
  ┌─────────────────┐
  │ Redis Streams   │
  │ (Task Queue)    │
  └────────┬────────┘
           │
      ┌────▼─────────────────┐
      │ Task Workers         │
      │ (rag/svr/task_executor)
      │ - Chunking           │
      │ - Embedding          │
      └──────────────────────┘
```

## Architecture Layers

### 1. Presentation Layer (Frontend)

**Technology Stack:**
- React 18 + TypeScript 5.9
- Vite 7 (build tool)
- React Router v7 (SPA routing)
- TanStack Query v5 (server state management)
- Zustand (UI state management)

**Key Components:**
- **Agent Editor** (35K LOC) — Visual workflow builder with ReactFlow
- **Dataset Manager** — Document upload, chunking strategy config
- **Chat Interface** — Multi-turn conversations with SSE streaming
- **Admin Dashboard** — System settings, user management
- **User Settings** — Profile, API keys, preferences
- **Search** — Full-text search interface

**Styling:**
- Tailwind CSS 3
- shadcn/ui (60+ Radix primitives)
- Ant Design 5 (gradual migration from)

**State Management Pattern:**
```
Server State (TanStack Query)
├── API responses cached automatically
├── Automatic refetch on focus/interval
└── Invalidation on mutations

UI State (Zustand)
├── Sidebar collapse/expand
├── Theme (light/dark)
├── Canvas zoom/pan
└── Form input values
```

**API Integration:**
- Dual HTTP clients: umi-request (legacy) + Axios (new)
- SSE streaming via `eventsource-parser` for chat
- Automatic token refresh via interceptors
- Error boundary for graceful degradation

---

### 2. API Layer

Two implementations (Python + Go) fronted by Nginx:

#### Python API (`api/` - 34K LOC)

**Framework:** Quart (async Flask)  
**Port:** 9380  
**Startup:** `api/ragflow_server.py`

**Architecture:**
```
Quart App (ASGI)
│
├── Blueprint: canvas_app.py
│   └── /api/v1/canvas/* (agent workflow endpoints)
│
├── Blueprint: kb_app.py
│   └── /api/v1/knowledgebases/* (knowledge base CRUD)
│
├── Blueprint: document_app.py
│   └── /api/v1/documents/* (upload, parse, delete)
│
├── Blueprint: chunk_app.py
│   └── /api/v1/chunks/* (chunk retrieval, update)
│
├── Blueprint: dialog_app.py
│   └── /api/v1/dialogs/* (chat endpoints)
│
├── Service Layer (Business Logic)
│   ├── DocumentService (chunking, parsing)
│   ├── KnowledgeBaseService (CRUD)
│   ├── CanvasService (workflow execution)
│   ├── SearchService (hybrid search)
│   └── LLMService (model inference)
│
└── Data Access Layer (Peewee ORM)
    ├── Models: User, Tenant, Document, Chunk, Conversation, etc.
    └── Database: MySQL 8 / PostgreSQL / OceanBase
```

**Request Flow (Example: Upload Document):**
```
POST /api/v1/documents
│
├── 1. Auth Middleware (JWT/API token)
├── 2. Validation (file size, format)
├── 3. Save to MinIO (object storage)
├── 4. Create Document record (DB)
├── 5. Enqueue parse task (Redis Streams)
└── 6. Return Document object (200 OK)

Async Processing:
task_executor.py reads from Redis Streams queue
└── Parse file (deepdoc/parser)
└── Extract chunks (rag/app/chunker)
└── Embed chunks (rag/llm/embedding)
└── Store in ES/Infinity (search index)
└── Update Document.status = "DONE" (DB)
```

#### Go API (`internal/` - 55K LOC)

**Framework:** Gin (HTTP router)  
**Port:** 9384  
**Startup:** `cmd/server_main.go`

**Architecture (mirrors Python):**
```
Gin Router
│
├── Handler: UserHandler
│   └── GET /api/v1/users (list), POST (create), etc.
│
├── Handler: DocumentHandler
│   └── POST /api/v1/documents, DELETE, GET, etc.
│
├── Service Layer
│   ├── UserService (interfaces defined in service/)
│   ├── DocumentService
│   ├── SearchService
│   └── CanvasService
│
└── Data Access Layer (GORM ORM)
    ├── Models: User, Document, Chunk, etc.
    └── Database: MySQL 8 / PostgreSQL (auto-migration)
```

**Key Differences from Python:**
- Compiled binary (faster startup)
- Statically typed (less runtime errors)
- CGo binding for C++ tokenizer (consistent with Python)
- GORM tolerates Python-created tables
- Can coexist with Python during migration

#### Proxy Modes

**Configured via `API_PROXY_SCHEME` environment variable:**

| Mode | Default | Behavior |
|------|---------|----------|
| `python` | ✓ | All routes → Python API (9380) |
| `go` | | All routes → Go API (9384) |
| `hybrid` | | Nginx routes between both APIs (feature-dependent) |

---

### 3. Backend Services Layer

#### RAG Pipeline (`rag/` - 35K LOC)

**Purpose:** Document processing, semantic search, LLM integration

**Components:**

**A. Document Processing**
```
deepdoc/parser/ (file format handlers)
├── PDF (pdfplumber, pypdf, VLM)
├── DOCX (python-docx)
├── Excel (openpyxl)
├── PPT (python-pptx)
└── Plain text (markdown, JSON, HTML, TXT, EPUB)

deepdoc/vision/ (neural models)
├── OCR (ONNX-based character recognition)
├── Layout analysis (10 labels: text, title, image, table, etc.)
└── Table detection (extract table cells)
```

**B. Chunking Strategies** (`rag/app/`)
- Naive (fixed size)
- Paper (academic structure)
- Book (chapters + sections)
- Laws (legal articles)
- Manual (user-defined points)
- QA (question-answer pairs)
- Table (preserve structure)
- Resume (section extraction)
- Presentation (slide-aware)
- Audio (transcript + timestamps)
- Email (message threads)
- Tag (user-defined tags)
- One (single chunk)

**C. LLM Integration** (`rag/llm/`)
```
Providers: 40+ via litellm
├── Chat (completion, streaming)
├── Embedding (30+ models)
├── Reranking (BGE, jira, Cohere)
├── Vision (OCR, layout, understanding)
└── TTS/ASR (speech)

Example: OpenAI, Claude, DeepSeek, Moonshot, LLaMA, local models
```

**D. Hybrid Search** (`rag/nlp/search.py`)
```
Dealer class combines three strategies:

1. BM25 (Lexical)
   Input: Query tokens
   Process: TF-IDF ranking in Elasticsearch
   Output: Top-k documents by keyword match
   
2. Vector (Semantic)
   Input: Query embedding (from LLM)
   Process: HNSW ANN in vector index
   Output: Top-k documents by semantic similarity
   
3. RRF Fusion
   Input: BM25 results + Vector results
   Process: Combine rankings (reciprocal rank fusion)
   Output: Merged, reranked top-k results
```

**E. Advanced Features**
- **GraphRAG:** Entity extraction + Leiden communities + graph search
- **RAPTOR:** Recursive abstractive summarization tree
- **Custom Tokenizer:** Chinese + English dual-mode, accurate token counts

**F. Task Execution** (`rag/svr/task_executor.py`)
```
Redis Streams Consumer
├── Read task from queue
├── Dispatch to chunker/embedding worker
├── Handle retries + exponential backoff
├── Log progress to database
└── Update Document.status on completion
```

#### Agent System (`agent/` - 15K LOC)

**Purpose:** Visual workflow engine for multi-step AI processes

**Architecture:**

```
Canvas (directed acyclic graph)
├── Nodes (components)
│   ├── Begin, End (flow control)
│   ├── LLM, Agent (inference)
│   ├── Switch, Iteration, Loop (logic)
│   ├── Retrieval, WebCrawler (data sources)
│   ├── Message, VariableAssignment (data ops)
│   └── Http, ExecuteSQL, EmailSend (integration)
│
└── Edges (data flow)
    └── Variables passed between nodes

Execution Model:
│
├── DAG validation (no cycles)
├── Topological sort
├── Async execution (nodes run in parallel if possible)
├── SSE streaming (real-time feedback)
└── State persistence (save/resume)
```

**Components:**
- 20+ pre-built components for common tasks
- Plugin system for custom components
- Type-safe input/output validation

**Tools Integration:**
```
agent/tools/ (20+)
├── Retrieval (query knowledge base)
├── WebCrawler (fetch URLs)
├── Search engines (Google, DuckDuckGo, ArXiv, Wikipedia)
├── APIs (GitHub, Yahoo Finance, DeepL)
├── Code execution (Python, JavaScript, SQL)
└── Email, PDF generation
```

**Sandbox Execution:**
- Docker containers (Kubernetes-compatible)
- E2B (secure cloud sandbox)
- Alibaba Cloud code interpreter
- Local FastAPI executor

---

### 4. Data Storage Layer

#### Database (`MySQL 8` / `PostgreSQL`)

**Multi-Tenant Schema:**
```
Users & Auth
├── user (id, email, password_hash, created_at)
├── tenant (id, name, created_by_id)
├── team (id, tenant_id, name)
└── role_permission (role, permission)

Knowledge Management
├── knowledgebase (id, tenant_id, name, status)
├── document (id, kb_id, name, file_path, status)
├── chunk (id, doc_id, content, embedding, metadata)
└── document_run_status (doc_id, status, error_msg)

Conversations
├── conversation (id, kb_id, name, created_at)
├── message (id, conv_id, role, content, created_at)
└── dialog (id, tenant_id, kb_id, name)

Workflows
├── canvas (id, tenant_id, name, definition)
├── canvas_run_status (canvas_id, status, output)
└── task (id, type, status, created_at)

Configuration
├── llm_conf (id, tenant_id, provider, api_key)
├── file_obj (id, tenant_id, path, size)
└── connector_template (id, connector_type, config)
```

**Key Indexes:**
```
knowledgebase: tenant_id, status
document: kb_id, status, created_at
chunk: doc_id, kb_id (for search filtering)
message: conversation_id, created_at
canvas: tenant_id, status
user: email (unique)
```

#### Search Engine (`Elasticsearch` / `OpenSearch` / `Infinity`)

**Index Schema:**
```
Logical chunk
├── id (unique identifier)
├── doc_id (reference to source document)
├── kb_id (reference to knowledge base)
├── content (full text, BM25-indexed)
├── embedding (vector, HNSW-indexed)
├── metadata (JSON, filterable)
│   ├── page_number
│   ├── section_title
│   ├── chunk_order
│   └── custom_fields
└── created_at (timestamp)
```

**Search Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "content": "machine learning" } },
        { "range": { "embedding": { "vector_distance": 0.5 } } }
      ],
      "filter": [
        { "term": { "kb_id": "kb-123" } }
      ]
    }
  }
}
```

**Document Engines:**
- **Elasticsearch:** Full-featured, proven (default)
- **OpenSearch:** AWS fork, compatible
- **Infinity:** Lightweight alternative, lower resource usage

#### Object Storage (`MinIO` / `S3` / `GCS` / `Azure Blob`)

**Bucket Structure:**
```
ragflow-bucket/
├── uploads/
│   ├── {tenant_id}/{document_id}/{filename} (original files)
│   └── ...
└── exports/
    ├── {tenant_id}/export-{timestamp}.zip
    └── ...
```

**Multipart upload for large files:**
- Client initiates upload
- Server generates presigned URLs
- Client uploads chunks in parallel
- Server completes multipart upload

#### Cache Layer (`Redis` / `Valkey`)

**Key Patterns:**
```
user:{user_id}:token         → JWT token (TTL: token expiry)
session:{session_id}         → Session data (TTL: 24h)
embedding:{hash}             → Cached embeddings (TTL: 7d)
search:{query_hash}          → Search results (TTL: 1h)
task:{task_id}:progress      → Task execution state (TTL: 1h)
rate_limit:{user_id}:{time}  → Token bucket (TTL: 60s)
```

**Streams (Task Queue):**
```
Queue: tasks:pending
├── Entry: {task_id, type, payload, created_at}
└── Consumer groups: {chunking_workers, embedding_workers}

Processing:
├── Worker reads from stream
├── Processes task
├── ACKs to mark complete (or NACKs on error)
└── Tasks retained for 24h (configurable)
```

---

### 5. Deployment Architecture

#### Docker Compose (Local Development)

**File:** `docker-compose.yml`

**Services:**
```
ragflow-server (Python or Go, configurable)
├── Env: API_PROXY_SCHEME=python
├── Depends on: mysql, redis, es, minio
└── Port: 9380 (HTTP)

ragflow-admin (Flask admin API)
├── Port: 9381
└── Provides: User mgmt, system config

nginx (Reverse proxy)
├── Port: 80, 443
└── Routes: /api/* → API, /admin/* → Admin, static → Frontend

mysql:8 (Relational database)
├── Volume: mysql-data
├── Env: MYSQL_ROOT_PASSWORD, MYSQL_DATABASE
└── Port: 3306

redis:7 (Cache + task queue)
├── Volume: redis-data
└── Port: 6379

minio (Object storage)
├── Volume: minio-data
├── Console: Port 9001
└── API: Port 9000

elasticsearch:8 (or opensearch:2, infinity)
├── Volume: es-data
├── Env: discovery.type=single-node
└── Port: 9200
```

**Profiles:**
- `cpu` — Default (CPU inference)
- `gpu` — NVIDIA CUDA for faster embeddings

**Full startup:**
```bash
docker compose -f docker-compose.yml --profile gpu up -d
```

#### Kubernetes (Production)

**Helm Charts:** `helm/`

**Components:**
```
Deployment: ragflow-api (3+ replicas)
├── Image: infiniflow/ragflow:v0.24.0
├── Env: API_PROXY_SCHEME, database creds
├── Resources: CPU 1000m, RAM 2Gi
└── Liveness/readiness probes

StatefulSet: mysql-8 (1 master, optional replicas)
├── Volume: PVC (persistent)
├── Port: 3306
└── Init container: schema migration

StatefulSet: redis (1 master)
├── Volume: PVC
├── Port: 6379
└── ConfigMap: sentinel config

StatefulSet: elasticsearch (3 nodes)
├── Volume: PVC per node
├── Port: 9200
└── ConfigMap: elasticsearch.yml

Deployment: task-worker (2-4 replicas)
├── Env: WORKER_ROLE=chunker (or embedding)
├── Depends on: Redis, MySQL
└── Auto-scales based on queue depth
```

**Networking:**
```
Service: ragflow-api (ClusterIP)
├── Port: 9380
└── Internal DNS: ragflow-api.default.svc.cluster.local

Ingress: ragflow (nginx-ingress)
├── Host: ragflow.example.com
├── TLS: cert-manager (Let's Encrypt)
└── Routes: /* → ragflow-api Service
```

---

## Data Flow Diagrams

### 1. Document Upload & Parsing

```
User Upload
    │
    ├─→ Frontend
    │   └─→ POST /api/v1/documents (multipart/form-data)
    │
    ├─→ API (document_app.py)
    │   ├─→ Validate (size, format)
    │   ├─→ Save to MinIO
    │   ├─→ Create Document record (DB)
    │   ├─→ Enqueue task to Redis Streams
    │   └─→ Return Document object
    │
    ├─→ Task Worker (task_executor.py)
    │   ├─→ Read task from Redis Streams
    │   ├─→ deepdoc/parser: Detect format, extract text
    │   ├─→ deepdoc/vision: OCR, layout analysis (if PDF)
    │   ├─→ rag/app/chunker: Split into chunks
    │   ├─→ rag/llm/embedding: Generate embeddings
    │   ├─→ Store chunks in Elasticsearch
    │   └─→ Update Document.status = "DONE" (DB)
    │
    └─→ Frontend (Poll or SSE)
        └─→ Display Document.status
```

### 2. Semantic Search Query

```
User Query: "machine learning algorithms"
    │
    ├─→ Frontend: POST /api/v1/search
    │
    ├─→ API (search handler)
    │   ├─→ Parse query
    │   ├─→ Call SearchService.hybrid_search()
    │   │
    │   └─→ rag/nlp/search.py (Dealer class)
    │       ├─→ BM25 search (Elasticsearch)
    │       │   └─→ TF-IDF ranking
    │       │
    │       ├─→ Vector search (Elasticsearch)
    │       │   ├─→ Embed query (rag/llm/embedding)
    │       │   └─→ HNSW ANN search
    │       │
    │       └─→ RRF Fusion
    │           ├─→ Combine BM25 + Vector scores
    │           └─→ Return top-10 chunks
    │
    ├─→ API: Augment with source metadata
    │   └─→ Return {chunk, score, doc_id, page_number}
    │
    └─→ Frontend: Display with highlighting + citations
```

### 3. Agent Workflow Execution

```
User: Execute Agent Canvas
    │
    ├─→ Frontend: POST /api/v1/canvas/{canvas_id}/run
    │
    ├─→ API (canvas_app.py)
    │   ├─→ Create CanvasRunStatus record (DB)
    │   ├─→ Deserialize canvas definition (JSON)
    │   └─→ Call agent/canvas.py (workflow engine)
    │
    ├─→ Workflow Executor (agent/canvas.py)
    │   ├─→ DAG validation (topological sort)
    │   ├─→ Identify parallelizable nodes
    │   │
    │   └─→ Execute nodes in order:
    │       ├─→ Begin node
    │       │   └─→ Initialize variables
    │       │
    │       ├─→ LLM node (async)
    │       │   ├─→ Build prompt
    │       │   ├─→ Call rag/llm/chat_completion()
    │       │   └─→ Stream response via SSE
    │       │
    │       ├─→ Retrieval node (async)
    │       │   ├─→ Query knowledge base
    │       │   └─→ Return top chunks
    │       │
    │       ├─→ Switch node
    │       │   ├─→ Evaluate condition
    │       │   └─→ Route to next node
    │       │
    │       └─→ Tool node (e.g., Code Execution)
    │           ├─→ Sandbox executor
    │           └─→ Return result
    │
    ├─→ SSE Streaming
    │   └─→ Send node output to frontend in real-time
    │
    └─→ Final: Update CanvasRunStatus with output
```

### 4. Multi-Tenant Data Isolation

```
Tenant-1 Data         Tenant-2 Data
├── KB-A              ├── KB-C
│   ├── Docs          │   ├── Docs
│   └── Chunks        │   └── Chunks
└── Canvas-X          └── Canvas-Y

Database Level:
├── Tenant_id in all tables
├── DB user with limited access (optional)
└── Row-level security (optional)

Search Engine Level:
├── Index: tenant-1_chunks
├── Index: tenant-2_chunks
└── Prefix all queries with tenant_id filter

Cache Level:
├── Key: tenant-1:user:1234:token
├── Key: tenant-2:user:5678:token
└── Redis slot isolation (optional)

API Level:
├── Extract tenant_id from JWT
├── Pass to all database queries
└── Filter all results by tenant
```

---

## Integration Points

### External LLM APIs

**Supported Providers (40+):**
```
OpenAI (ChatGPT, GPT-4)
Anthropic (Claude)
Google (Gemini)
DeepSeek, Moonshot, Zhipu AI
LLaMA (local or cloud)
Cohere, Groq, SiliconFlow
And 30+ others via litellm
```

**Integration Pattern:**
```python
# Abstracted interface
response = llm_service.chat(
    provider="openai",
    model="gpt-4",
    messages=[...],
    temperature=0.7
)

# Handled internally:
# - API key management
# - Rate limiting
# - Retry logic
# - Streaming support
```

### Data Source Connectors

**25+ Connectors:**
```
GitHub (repos, issues, discussions)
Jira (issues, comments)
Confluence (pages, attachments)
Slack (channels, threads)
Google Drive, OneDrive (documents)
Notion, Airtable (databases)
Shopify, Stripe (e-commerce)
Salesforce, HubSpot (CRM)
Zendesk (tickets, KB)
And more...
```

**Connector Flow:**
```
User: Add Data Source
    ├─→ Select connector type (e.g., GitHub)
    ├─→ Provide credentials (OAuth or API key)
    ├─→ Authorize connector
    ├─→ API calls connector to fetch data
    ├─→ Transform data to Document/Chunk format
    ├─→ Enqueue for processing
    └─→ Auto-sync on schedule
```

### Webhook Notifications

**Trigger:** Document parsing complete, agent execution done, etc.

**Payload:**
```json
{
  "event_type": "document_parsed",
  "document_id": "doc-123",
  "kb_id": "kb-456",
  "status": "DONE",
  "chunk_count": 150,
  "timestamp": "2026-04-16T10:30:00Z"
}
```

---

## Scaling

**Stateless (add replicas):** API servers, task workers  
**Stateful (more complex):** MySQL, Redis, Elasticsearch

**Bottlenecks & Solutions:**
- Database slow: add indexes, read replicas
- Search slow: more workers, batch embeddings
- LLM rate limit: queue requests, cheaper models
- Disk full: archive old documents

---

**Version:** 0.24.0
