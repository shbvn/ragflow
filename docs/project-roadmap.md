# Project Development Roadmap

## Overview

RAGFlow v0.24.0 is a mature, production-ready RAG platform. This roadmap outlines completed phases, current work, and planned future features. Development follows agile methodology with 2-week sprints.

## Version History

| Version | Release Date | Status | Key Features |
|---------|--------------|--------|--------------|
| v0.10.0 | 2024-01-15 | ✓ Stable | Core RAG, document upload, semantic search |
| v0.15.0 | 2024-03-01 | ✓ Stable | Chat interface, multi-turn conversations |
| v0.20.0 | 2024-06-15 | ✓ Stable | Agent workflows (visual editor) |
| v0.22.0 | 2024-09-01 | ✓ Stable | Multi-tenant, team management |
| v0.23.0 | 2025-01-10 | ✓ Stable | Go backend (hybrid mode), GraphRAG |
| v0.24.0 | 2025-03-15 | ✓ Current | Advanced features, performance optimizations |
| v0.25.0 | 2026-Q2 | 🔄 Planning | Mobile app, offline mode, advanced memory |

## Completed Phases (v0.10 - v0.24)

### Phase 1: Core RAG (v0.10)
**Status:** ✓ Complete  
**Timeline:** 6 months  
**Key Achievements:**
- Document upload (15+ formats)
- Chunking strategies (13 variants)
- Semantic search (BM25 + vector)
- MinIO integration
- Elasticsearch support
- API endpoints (REST)

**Metrics:**
- Parse 10K+ documents/day
- Search latency <1s p95
- Support 100+ concurrent users

### Phase 2: Chat & Conversations (v0.15)
**Status:** ✓ Complete  
**Timeline:** 3 months  
**Key Achievements:**
- Multi-turn conversation interface
- Session persistence
- Message history
- SSE streaming
- Citation generation
- Chat memory (short-term)

**Metrics:**
- 95%+ citation accuracy
- Response latency <3s (including LLM)
- Support 1000+ active conversations

### Phase 3: Agent Workflows (v0.20)
**Status:** ✓ Complete  
**Timeline:** 4 months  
**Key Achievements:**
- Visual canvas editor (ReactFlow)
- 20+ pre-built components
- 20+ integrated tools
- DAG execution engine
- Real-time SSE feedback
- Workflow templates

**Metrics:**
- 100+ pre-built workflow templates
- Support complex 10+ node workflows
- Execute 1000+ workflows/day

### Phase 4: Multi-Tenant & Teams (v0.22)
**Status:** ✓ Complete  
**Timeline:** 3 months  
**Key Achievements:**
- Tenant isolation
- Team management
- Role-based access control (RBAC)
- Resource sharing
- Audit logging
- OAuth integration (OIDC, GitHub)

**Metrics:**
- Support 100+ tenants
- Enforce data isolation
- 99.9% API availability

### Phase 5: Go Backend & Hybrid Mode (v0.23)
**Status:** ✓ Complete  
**Timeline:** 5 months  
**Key Achievements:**
- Go API server (Gin)
- GORM ORM layer
- CGo tokenizer (C++ static lib)
- Hybrid proxy mode (Nginx routes)
- Progressive migration path
- Full compatibility with Python API

**Metrics:**
- 2-3x faster startup (compiled binary)
- Reduced memory footprint
- Zero breaking changes

### Phase 6: Advanced Features (v0.24)
**Status:** ✓ Current  
**Timeline:** 6 months  
**Key Achievements:**
- GraphRAG (entity extraction + communities)
- RAPTOR (hierarchical summarization)
- Advanced memory (knowledge graph)
- Vision language models (document understanding)
- 25+ data source connectors
- Webhook support
- Plugin system
- Admin CLI tool
- MCP server integration

**Metrics:**
- 40+ LLM providers supported
- 25+ data connectors
- VLM parsing accuracy >95%

---

## Current Status (v0.24.0 - In Progress)

**Release Date:** March 15, 2025  
**Progress:** 95% complete  

### Active Sprint: Document Parsing Enhancements

**Completed This Sprint:**
- ✓ VLM parsing mode for PDFs (Claude Vision, GPT-4V)
- ✓ Layout-aware chunking (preserve tables, headers)
- ✓ Resume extraction (section detection + entity recognition)
- ✓ Reject empty/space-only content in chunk update API
- ✓ Button to disable VLM parsing (fallback to plain text)

**In Progress:**
- 🔄 MinerU parser integration (advanced document understanding)
- 🔄 Docling parser (IBM universal format handler)
- 🔄 PaddleOCR fallback (Baidu alternative to Google Vision)

**Next Sprint (1-2 weeks):**
- Advanced table detection + extraction
- Excel to HTML conversion improvements
- Document quality scoring (completeness assessment)

### Bug Fixes & Stabilization

| Category | Count | Priority | Status |
|----------|-------|----------|--------|
| Document parsing | 12 | P1 | ✓ Fixed |
| Search quality | 8 | P1 | ✓ Fixed |
| UI/UX | 15 | P2 | ✓ Fixed |
| Performance | 6 | P1 | ✓ Fixed |
| API compatibility | 4 | P1 | ✓ Fixed |

### Performance Metrics (Current)

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Document parse latency | <5min | 3.2min (avg) | ✓ Good |
| Search latency (p95) | <1s | 800ms | ✓ Good |
| Embedding throughput | 10K/min | 8.5K/min | ⚠ Near target |
| API response time | <500ms | 320ms (avg) | ✓ Good |
| Frontend load time | <3s | 2.1s | ✓ Good |
| Memory per worker | <1GB | 850MB | ✓ Good |

---

## Planned Features (v0.25 & Beyond)

### Q2 2026: v0.25 Release (Advanced Memory & Offline)

**Timeline:** 4 months (April - July 2026)  
**Theme:** Enhanced knowledge retention and offline capabilities

#### Feature 1: Multi-Level Memory System
```
Short-term Memory (Session)
├── Current conversation context (in-memory)
├── Token budget: 8K tokens
└── Auto-clear on session end

Long-term Memory (Persistent)
├── Summarized conversation history (DB)
├── User profile + preferences
├── Interaction patterns
└── Retention: 12 months

Knowledge Graph Memory
├── Entity relationships from conversations
├── Automatic graph construction
├── Query via semantic edges
└── Cross-conversation knowledge reuse
```

**Implementation:**
- Vector storage of summarizations (semantic retrieval)
- Entity linking (extract entities from chat)
- Graph database (Neo4j or similar)
- Memory ranking (relevance scoring)

**Success Criteria:**
- Reduce context hallucination by 30%
- Support 10x longer conversations
- Entity extraction accuracy >90%

#### Feature 2: Offline-First Frontend
```
Offline Capability
├── Service Worker caching
├── IndexedDB for local storage
├── Sync queue for mutations
└── Background sync on reconnect

Offline Features
├── View cached documents/conversations
├── Compose messages (queued)
├── Search cached chunks locally
└── Read agent workflows

Sync Strategy
├── Conflict detection (last-write-wins)
├── Retry queue with exponential backoff
└── Offline indicator + notification
```

**Technical Approach:**
- Workbox (service workers)
- IndexedDB API (local database)
- Sync API (background sync)
- Conflict resolution middleware

**Success Criteria:**
- 90% feature availability offline
- <5s sync time for 100 messages
- Zero data loss on reconnect

#### Feature 3: Mobile App (Native)
```
Target Platforms
├── iOS (Swift, native UI)
├── Android (Kotlin, native UI)
└── React Native option (code sharing)

Features
├── View chat conversations
├── Search knowledge bases
├── Upload documents (camera, gallery)
├── Execute simple workflows
└── Offline chat (queued)

Push Notifications
├── New message alerts
├── Document parsing complete
├── Workflow execution status
└── Team invitations
```

**Technical Stack:**
- Swift (iOS) + Kotlin (Android)
- REST API (same as web)
- Firebase for push notifications
- LocalDatabase: SQLite

#### Feature 4: Advanced Evaluation Framework
```
Retrieval Evaluation
├── Precision@K metrics
├── NDCG (normalized discounted cumulative gain)
├── MRR (mean reciprocal rank)
├── MAP (mean average precision)

Generation Evaluation
├── BLEU, ROUGE scores
├── Factuality checking (with LLM)
├── Citation accuracy
├── Hallucination detection

User Feedback Loop
├── Thumbs up/down on responses
├── Explicit corrections
├── A/B testing framework
└── Continuous improvement loop
```

**Implementation:**
- Evaluation component in agent system
- Metrics dashboard in admin panel
- Export evaluation reports
- Auto-optimize based on metrics

---

### Q3 2026: v0.26 Release (Enterprise & Integrations)

**Timeline:** 4 months (July - October 2026)  
**Theme:** Enterprise features and expanded ecosystem

#### Feature 1: Fine-Tuning Pipeline
```
Dataset Curation
├── Collect query-answer pairs from interactions
├── User feedback loop (good/bad responses)
├── Manual annotation interface
└── Quality filtering (remove duplicates, low-quality)

Fine-Tuning Service
├── Adapter-based fine-tuning (LoRA)
├── Minimal retraining (hours, not days)
├── Version management
└── A/B test against base model

Custom Models
├── Deploy fine-tuned model
├── Use in chat, agents, retrieval reranking
└── Fallback to base model
```

**Providers:**
- OpenAI Fine-tuning API
- Hugging Face (open models)
- vLLM (local inference)

#### Feature 2: Enterprise Compliance & Audit
```
Audit Logging
├── User actions (login, data access, changes)
├── API audit trail
├── Data lineage (chunk → source → citations)
└── Tamper-proof logs (immutable append-only)

Compliance Features
├── GDPR right-to-deletion (cascade deletes)
├── Data residency enforcement (regional storage)
├── Encryption at rest + in transit
├── Key rotation policies

Access Control
├── Fine-grained permissions (per KB, per agent)
├── IP allowlisting
├── SSO/SAML integration
└── 2FA enforcement
```

**Standards:**
- SOC 2 Type II certification
- GDPR compliance
- HIPAA ready

#### Feature 3: Advanced Retrieval Reranking
```
Cross-Encoder Reranker
├── Fine-tuned cross-encoder model
├── Query-chunk pair scoring
├── Multi-query rewriting (generate sub-queries)
├── Diversity ranking (avoid duplicate chunks)

Hybrid Reranking
├── Combine BM25, vector, cross-encoder
├── Learning-to-rank (LTR) model
├── User feedback incorporation
└── Personalization (user profile)

Cost Optimization
├── Rerank only top-100 (not all chunks)
├── Cache popular query results
└── Batch reranking
```

#### Feature 4: Expanded Data Connectors
```
New Connectors (10+ additional)
├── Databricks, Snowflake (data warehouses)
├── Stripe, Square (e-commerce transactions)
├── Twilio, SendGrid (communication logs)
├── AWS S3, DynamoDB (AWS native)
├── Hugging Face Datasets (ML datasets)
└── More...

Connector Capabilities
├── Real-time sync (webhooks)
├── Incremental updates (delta sync)
├── Transformation rules (custom extraction)
└── Scheduling (cron-style)
```

---

### Q4 2026 & Beyond: v0.27+

#### Planned (High Priority)
- **Real-time Collaboration:** Multiple users editing same canvas/KB simultaneously
- **Advanced Visualization:** Knowledge graph visualization, document network analysis
- **Custom Embeddings:** Fine-tune embedding models for domain-specific tasks
- **Multi-Modal RAG:** Images, videos, audio as first-class citizens
- **Chain-of-Thought Reasoning:** Explicit reasoning steps in responses
- **Local LLM Optimization:** Quantization, pruning for faster inference

#### Exploring (Medium Priority)
- **Browser Extension:** In-page RAG queries, document snippets
- **Slack/Teams Bot:** Conversational access to knowledge bases
- **GraphQL API:** Alternative to REST for complex queries
- **WebAssembly:** Client-side tokenization, lightweight workers
- **Federated Learning:** Train models across multiple tenants (privacy-preserving)

#### Long-Term Vision (Exploratory)
- **Autonomous Agent Swarms:** Multiple agents collaborating on complex tasks
- **Neuro-Symbolic AI:** Integrate symbolic reasoning with neural networks
- **Continuous Learning:** Model continuously improves from conversations
- **Quantum-Ready:** Preparation for quantum computing integration

---

## Success Metrics & KPIs

### Product Metrics

| Metric | Current | Target (v0.25) | Status |
|--------|---------|-----------------|--------|
| Active users | 5,000+ | 20,000 | On track |
| Deployments | 100+ | 500+ | On track |
| Data sources indexed | 500M+ documents | 5B+ | On track |
| API requests/month | 100M+ | 500M+ | On track |
| System uptime | 99.9% | 99.99% | On track |

### Quality Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Search accuracy (NDCG@10) | 0.82 | 0.90 | In progress |
| Citation accuracy | 94% | 97% | In progress |
| Hallucination rate | 6% | <2% | In progress |
| API test coverage | 78% | >85% | On track |
| Frontend test coverage | 65% | >75% | On track |

### Performance Metrics

| Metric | Current | Target (v0.25) | Status |
|--------|---------|-----------------|--------|
| Search latency (p95) | 800ms | <500ms | On track |
| API response time | 320ms | <250ms | In progress |
| Frontend load time | 2.1s | <1.5s | Planned |
| Embedding throughput | 8.5K/min | 15K/min | Planned |
| Concurrent users | 1000+ | 10,000+ | Planned |

### Business Metrics

| Metric | Current | Target (2026) | Status |
|--------|---------|--------------|--------|
| GitHub stars | 8,000+ | 20,000+ | On track |
| Community contributors | 150+ | 500+ | On track |
| Enterprise customers | 20+ | 100+ | On track |
| Revenue (SaaS) | $2M ARR | $50M ARR | On track |

---

## Risk Assessment & Mitigation

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| LLM API rate limits | 🔴 High | Medium | Implement queue, fallback models, local inference |
| Search index outages | 🔴 High | Low | Replica shards, snapshot backup, fallback to DB search |
| Embedding model changes | 🟠 Medium | High | Version control embeddings, re-embed on upgrade, mapping layer |
| Tokenizer accuracy drift | 🟠 Medium | Low | Continuous testing, benchmark suite, version locks |

### Operational Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| Data loss (corruption) | 🔴 Critical | Low | Daily backups, point-in-time recovery, audit logs |
| Security breach | 🔴 Critical | Low | Regular audits, penetration testing, bug bounty, SoC 2 |
| Dependent library vulnerabilities | 🔴 High | Medium | Automated dependency scanning, rapid patching, vendor support |

### Market Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| Incumbent competition | 🟠 Medium | High | Differentiation (VLM, GraphRAG, agents), community strength |
| AI model commoditization | 🟠 Medium | Medium | Focus on RAG + agents, not just search; integrate all models |
| Open-source sustainability | 🟡 Low | Medium | Commercial support offering, enterprise features, grants |

---

## Dependencies & Blockers

### External Dependencies
- **LLM Provider APIs:** OpenAI, Anthropic, Google (API stability)
- **Search Engines:** Elasticsearch, Infinity (version compatibility)
- **Package Managers:** npm, pip (security + availability)
- **Cloud Providers:** AWS, Azure, GCP (service reliability)

### Internal Blockers (None Currently)
- All critical paths unblocked
- Team bandwidth sufficient for roadmap
- Infrastructure stable

---

## Community & Contribution Goals

### 2026 Milestones
- 20K+ GitHub stars
- 500+ active community contributors
- 50+ third-party integrations
- 100+ published workflows/templates
- Established special interest groups (SIGs)

### Contributing Opportunities
- **Documentation:** Guides, tutorials, API docs
- **Connectors:** New data source integrations
- **Components:** Custom agent workflow components
- **Tools:** Utility scripts, monitoring, deployment tools
- **Localizations:** Translate UI/docs to 20+ languages
- **Testing:** Bug reports, test case contributions
- **Examples:** Sample projects, reference implementations

---

## Release Schedule

| Version | Planned Date | Status | Focus |
|---------|--------------|--------|-------|
| v0.24.2 | May 2026 | 🔄 In progress | Bug fixes, minor features |
| v0.25.0 | July 2026 | 📋 Planning | Memory, offline, mobile |
| v0.26.0 | October 2026 | 📋 Planning | Enterprise, fine-tuning |
| v0.27.0 | January 2027 | 📋 Exploring | Collaboration, optimization |

---

## How to Get Involved

**For Users:**
- Join [Discord community](https://discord.gg/ragflow)
- Follow [GitHub discussions](https://github.com/infiniflow/ragflow/discussions)
- Submit feature requests via GitHub issues
- Vote on planned features

**For Contributors:**
- Check [good first issues](https://github.com/infiniflow/ragflow/issues?q=label:"good+first+issue")
- Join development community calls (bi-weekly)
- Review pull requests
- Help with documentation

**For Enterprise:**
- Commercial support: sales@infiniflow.io
- Custom deployments, training
- Priority feature requests
- SLA guarantees

---

**Document Version:** 0.24.0  
**Last Updated:** 2026-04-16  
**Next Review:** 2026-05-15  
**Maintained By:** Product & Engineering Team
