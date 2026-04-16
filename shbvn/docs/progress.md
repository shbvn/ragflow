# SHBVN AI Platform — Progress Tracker

Living document. Update after each work session.

## Status by Track

### Foundation (cross-track)
- [x] Module 3A: SHBVN Metadata Schema — MySQL authoritative layer (2026-04-16)
- [ ] Module 3B: SHBVN Metadata Schema — ES projector + chunk-level + query filter
- [ ] Module 5: PDP Law Compliance Layer
- [ ] Module 12: Unified AI Orchestrator
- [ ] Module 13: Multi-tenant KB Management

### Track A — Internal Chatbot
- [ ] Module 1: Vietnamese Document Parser
- [ ] Module 2: 5-Gate Security Layer
- [ ] Module 4: SHBVN System Connectors
- [ ] Module 6: Internal UI Skin

### Track B — Customer Chatbot on SOL
- [ ] Module 7: Customer-facing Chatbot Service
- [ ] Module 8: SOL App Integration
- [ ] Module 14: Customer Security & Privacy Layer

### Track C — Analytics
- [ ] Module 9: Text-to-SQL Analytics Engine
- [ ] Module 10: Financial Dashboards
- [ ] Module 11: Data Governance Layer

## Current Sprint

**Goal:** Module 3A metadata foundation (MySQL authoritative layer)

**In progress:**
- Follow-up: `git mv shbvn-docs shbvn/docs` + update CLAUDE.md references

**Blocked:**
- ...

**Completed this sprint:**
- Module 3A: migration 001 (3 tables, 16 indices) applied + rollback-tested
- Module 3A: Peewee models (`shbvn/metadata/schema.py`)
- Module 3A: CRUD + validation service (`shbvn/metadata/service.py`)
- Module 3A: Pluggable role resolver (`shbvn/metadata/role_resolver.py`)
- Module 3A: 15 pytest tests — 15/15 PASS
- ADR-0003 (MySQL authoritative) + ADR-0004 (pluggable role resolver)
- `shbvn/docs/brd-errata.md` — 6 BRD v2 mismatches logged
- Branch `feat/module-3a-metadata-schema`, 6 commits, ready for review

## Decisions Log

| Date | Decision | Rationale | Revisit date |
|------|----------|-----------|--------------|
| 2026-04-16 | Fork RAGFlow v0.24.0 as baseline (ADR-0001) | ~70% feature coverage day one; Apache-2.0 | N/A |
| 2026-04-16 | MySQL authoritative for SHBVN metadata; ES denorm read copy (ADR-0003) | Version lifecycle needs transactions; retrieval needs index pushdown | After Module 3B ships projector |
| 2026-04-16 | Pluggable RoleResolver: Table (2A) + Claim stub (SSO future) (ADR-0004) | Keep SSO migration to a composition swap, not a repo rewrite | When Module 12 SSO lands |
| 2026-04-16 | Split Module 3 → 3A (doc-level MySQL) / 3B (chunk-level + ES projector + query filter) | 3B tightly coupled to Module 1 parser output (not yet defined) — dead-code risk | When Module 1 parser spec is defined |
| 2026-04-16 | No DB-level FKs across SHBVN tables; ref integrity in service layer | Standalone-testable migration; soft-delete friendly; no cascade coupling | — |
| 2026-04-16 | Option C versioning: id (stable per-row PK) + shbvn_doc_id (natural group key) + UNIQUE(shbvn_doc_id, version) | Per-version FK targets stay stable; lineage queries simple | — |

## Open Questions

- Q: _question waiting for stakeholder answer_
  - Owner: _who's getting the answer_
  - Deadline: _when_

