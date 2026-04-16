# ADR-0001: Use RAGFlow as Baseline RAG Framework

**Status:** Accepted
**Date:** 2026-04-16
**Deciders:** DuongLx (DDD), Head of ICT Division

## Context

SHBVN needs to build an AI platform covering 3 tracks (internal chatbot,
customer chatbot on SOL, financial analytics). Decision needed: build from
scratch using libraries (LangChain/LlamaIndex) vs fork an existing complete
framework.

## Decision

Fork RAGFlow (github.com/infiniflow/ragflow, Apache-2.0, v0.24.0) as baseline.
Build SHBVN-specific features in isolated `shbvn/`, `shbvn-track-*/` folders.

## Consequences

**Easier:**
- ~70% of required features (DeepDoc, hybrid retrieval, reranker, citations,
  local LLM deployment) available day one
- Production-tested by 73K+ community users
- Cut Phase 1 delivery from 12-18 months to ~4 months
- Inherit ongoing bug fixes and features via upstream merges

**Harder:**
- Must maintain compatibility with upstream — mitigation: isolate changes in
  `shbvn/` subdirs, use `# === SHBVN CUSTOMIZATION ===` markers for any
  upstream edits
- Dependent on upstream for core RAG improvements — acceptable given 483
  contributors and active development
- Learning curve for team — mitigation: Claude Code-assisted onboarding,
  architecture reading sessions

## Alternatives considered

- **LangChain + custom app:** Too much from-scratch effort (UI, admin,
  ingestion, monitoring). 12-18 months vs 4.
- **Dify:** Generic RAG, weaker document parsing (no DeepDoc equivalent),
  less suited to complex Vietnamese banking documents.
- **Haystack:** Strong but code-first, less out-of-box UI — still 50%+ custom
  build needed.
- **Commercial (Cohere, Azure AI Search):** Violates data localization
  (Cybersecurity Law 2026, SBV Circulars). Cost prohibitive.
