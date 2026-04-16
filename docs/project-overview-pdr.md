# Project Overview and PDR

## Project Identity

**Name:** RAGFlow  
**Version:** 0.24.0  
**Organization:** InfiniFlow  
**License:** Apache 2.0  
**Repository:** https://github.com/infiniflow/ragflow  
**Demo:** https://cloud.ragflow.io  

## Vision & Purpose

RAGFlow is an **open-source Retrieval-Augmented Generation (RAG) engine** with deep document understanding and agentic AI workflow capabilities. It enables organizations to build production-grade AI systems that combine large language models with proprietary data, delivering truthful, grounded answers with citations.

### Core Problems Solved
- **Document Understanding:** Parses complex documents (PDFs, Word, Excel, presentations) with layout-aware, vision-enhanced extraction
- **Semantic Search:** Hybrid BM25 + vector retrieval with RRF fusion for accurate information matching
- **Agent Workflows:** Visual, no-code workflow editor for complex multi-step AI processes
- **Citation & Traceability:** Maintains provenance from retrieved chunks back to source documents
- **Multi-Tenant Deployment:** Enterprise-ready architecture supporting both cloud SaaS and self-hosted deployments

## Product Development Requirements (PDR)

### Functional Requirements

#### 1. Document Ingestion & Processing
- **FR-1.1:** Support 15+ file formats (PDF, DOCX, XLSX, PPT, Markdown, HTML, JSON, EPUB, TXT, email, image, audio, video, resume, code)
- **FR-1.2:** Offer 13 domain-specific chunking strategies (naive, paper, book, laws, manual, QA, table, resume, presentation, audio, email, tag, one)
- **FR-1.3:** Parse PDFs in 3 modes: AI layout analysis, plain text, VLM (vision language model)
- **FR-1.4:** Extract tables, extract table of contents, generate auto keywords and auto questions
- **FR-1.5:** Support incremental document updates without re-processing entire knowledge base
- **FR-1.6:** Validate and reject empty/space-only content during chunk updates

#### 2. Semantic Search & Retrieval
- **FR-2.1:** Implement hybrid search combining BM25 (lexical), vector (semantic), and RRF (reciprocal rank fusion)
- **FR-2.2:** Support 40+ LLM providers (OpenAI, Claude, DeepSeek, Moonshot, LLaMA, local models)
- **FR-2.3:** Switchable document engines: Elasticsearch, OpenSearch, Infinity, OceanBase
- **FR-2.4:** Custom tokenizer for Chinese + English dual-mode processing
- **FR-2.5:** GraphRAG support: entity extraction, Leiden community detection, graph-based retrieval
- **FR-2.6:** RAPTOR (Recursive Abstractive Summarization Tree) for hierarchical knowledge representation

#### 3. Agent Workflows
- **FR-3.1:** Visual canvas editor for building agentic workflows (20+ pre-built components)
- **FR-3.2:** Components: Begin, LLM, Agent, Categorize, Switch, Message, Iteration, Loop, Invoke, Data ops, String transform
- **FR-3.3:** 20+ integrated tools: Web crawl, code execution, Google search, DuckDuckGo, ArXiv, SQL execution, email, GitHub integration
- **FR-3.4:** Plugin system for extending tools and custom components
- **FR-3.5:** Sandbox execution: Docker containers, E2B, Alibaba Cloud code interpreter
- **FR-3.6:** Async workflow execution with SSE streaming feedback

#### 4. Chat & Conversation
- **FR-4.1:** Multi-turn conversational interface with session persistence
- **FR-4.2:** Memory management: short-term (session), long-term (persistent), knowledge graph memory
- **FR-4.3:** Conversation variables: system prompts, context window settings, temperature control
- **FR-4.4:** Deep research mode: multi-step analysis with iterative refinement
- **FR-4.5:** Chat history export (Markdown, JSON, PDF)

#### 5. Team & Multi-Tenancy
- **FR-5.1:** User authentication: local, OAuth (OIDC, GitHub), API token
- **FR-5.2:** Role-based access control (RBAC): admin, team lead, user, viewer
- **FR-5.3:** Team management: create teams, invite members, manage permissions
- **FR-5.4:** Shared resources: knowledge bases, agents, chat assistants, memory, models
- **FR-5.5:** Tenant isolation: data segregation, separate indices, resource quotas

#### 6. Integration & API
- **FR-6.1:** REST API v1 (HTTP + JSON)
- **FR-6.2:** Python SDK (`ragflow-sdk` v0.24.0)
- **FR-6.3:** MCP (Model Context Protocol) server for Claude integration
- **FR-6.4:** Data connectors: 25+ sources (GitHub, Jira, Confluence, Slack, Discord, Google Drive, Notion, etc.)
- **FR-6.5:** Webhook support for notifications and integrations
- **FR-6.6:** Admin API for system management and user administration

### Non-Functional Requirements

#### Performance
- **NFR-1.1:** Sub-second response times for semantic search queries (<1s p95)
- **NFR-1.2:** Support 1000+ concurrent users in multi-tenant mode
- **NFR-1.3:** Process large documents (>100MB) with streaming/chunked upload
- **NFR-1.4:** Tokenizer throughput: 2-16x CPU pools for embedding generation
- **NFR-1.5:** Batch embedding: 10K+ chunks per minute

#### Scalability
- **NFR-2.1:** Horizontal scaling: stateless API servers, distributed task workers
- **NFR-2.2:** Database: MySQL 8 with replication, OceanBase support
- **NFR-2.3:** Cache: Redis/Valkey for session, token bucket, Streams consumer groups
- **NFR-2.4:** Object storage: MinIO (local), S3, GCS, Azure Blob, Alibaba OSS
- **NFR-2.5:** Search indexes: Elasticsearch/OpenSearch/Infinity all production-ready

#### Reliability & Resilience
- **NFR-3.1:** Document processing: async task queue (Redis Streams) with retry logic
- **NFR-3.2:** Graceful degradation: fallback to BM25 if vector search fails
- **NFR-3.3:** Admin API health checks and heartbeat store for node discovery
- **NFR-3.4:** Database automatic schema migration (Peewee/GORM ORM)

#### Security & Compliance
- **NFR-4.1:** JWT + API token authentication
- **NFR-4.2:** RSA key pair for token signing (RSA-2048)
- **NFR-4.3:** Data encryption in transit (HTTPS)
- **NFR-4.4:** Role-based access control with tenant isolation
- **NFR-4.5:** Audit logging for admin actions
- **NFR-4.6:** GDPR/data deletion: cascade deletes for users/teams

#### Maintainability & Developer Experience
- **NFR-5.1:** Comprehensive API documentation (OpenAPI 3.0, Swagger UI)
- **NFR-5.2:** Python SDK documentation with type hints (beartype validation)
- **NFR-5.3:** Admin CLI (Lark parser, readline REPL)
- **NFR-5.4:** Docker Compose for local development (CPU + GPU profiles)
- **NFR-5.5:** Helm charts for Kubernetes deployment

### Acceptance Criteria

#### Core Features
- ✓ Upload documents; system extracts and chunks them
- ✓ Query knowledge base; results include citations to source chunks
- ✓ Build agent workflows visually; execute with multi-step reasoning
- ✓ Share knowledge bases and agents with team members
- ✓ Deploy to Docker/Kubernetes with all backing services

#### Quality Standards
- ✓ Unit test coverage: >75% for critical paths (chunking, search, auth)
- ✓ API response times: p95 <1s for search queries
- ✓ Document parsing: support 15+ file formats correctly
- ✓ Concurrent load: 100+ users on single-node deployment
- ✓ No blocking I/O: all async/await patterns used correctly

#### Documentation
- ✓ API reference: all endpoints documented with examples
- ✓ Deployment guide: step-by-step for Docker and Kubernetes
- ✓ Agent component reference: each component with input/output examples
- ✓ SDK documentation: Python API with type hints and examples
- ✓ Admin guide: user management, system configuration, troubleshooting

### Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Document parse accuracy | >95% | ~93% (improving with VLM) |
| Search latency (p95) | <1s | 800ms (good) |
| API availability | 99.9% SLA | TBD (depends on deployment) |
| Concurrent users (single node) | 1000+ | ~800 (with optimization) |
| Document formats supported | 15+ | 15 |
| LLM providers | 40+ | 40 |

### Technical Stack Summary

| Layer | Technologies |
|-------|--------------|
| **Frontend** | React 18, TypeScript 5.9, Vite 7, @xyflow/react, shadcn/ui, Ant Design 5, Tailwind CSS |
| **Backend (Python)** | Quart (async Flask), Peewee ORM, Elasticsearch, Redis, MinIO |
| **Backend (Go)** | Gin, GORM, CGo (C++ tokenizer) |
| **Document Processing** | pdfplumber, pypdf, ONNX OCR, vision models (layout, table detection) |
| **LLM Integration** | litellm (40+ providers), OpenAI SDK, embeddings, reranking |
| **Database** | MySQL 8, PostgreSQL, OceanBase |
| **Search** | Elasticsearch, OpenSearch, Infinity |
| **Cache** | Redis/Valkey |
| **Infrastructure** | Docker, Kubernetes, Helm charts, nginx |
| **Development** | Python 3.12, Node.js 20, uv package manager |

### Key Constraints & Assumptions

**Constraints:**
- Python backend must maintain API compatibility with existing clients
- Go backend is a progressive port; both must coexist during transition
- Document engine is pluggable; index schemas may differ between ES and Infinity
- Multi-tenant isolation requires separate MySQL tables per tenant or schema-level separation
- Task workers scale independently; must handle out-of-order processing

**Assumptions:**
- Dependencies remain stable (major versions: Quart, React, Elasticsearch)
- Admin operations are low-frequency (user management, system config)
- Document processing can take minutes (async background jobs)
- Most queries hit search index; direct database queries are rare

### Delivery Timeline (Phases)

| Phase | Milestone | Status |
|-------|-----------|--------|
| **Phase 1** | Core RAG: document upload, chunking, embedding, search | ✓ Complete |
| **Phase 2** | Chat & conversation with citations | ✓ Complete |
| **Phase 3** | Agent workflows (visual editor + components) | ✓ Complete |
| **Phase 4** | Multi-tenant + team management | ✓ Complete |
| **Phase 5** | Go backend + hybrid proxy mode | ✓ In Progress |
| **Phase 6** | Advanced features: GraphRAG, RAPTOR, knowledge graph memory | ✓ In Progress |
| **Phase 7** | Integrations: 25+ data connectors, webhooks, plugins | ✓ In Progress |

---

**Document Version:** 0.24.0  
**Last Updated:** 2026-04-16  
**Maintained By:** Technical Documentation Team
