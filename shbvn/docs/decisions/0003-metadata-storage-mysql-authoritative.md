# ADR-0003: MySQL as Authoritative Store for SHBVN Metadata

**Status:** Accepted
**Date:** 2026-04-16
**Deciders:** DuongLx (DDD)
**Supersedes:** —
**Related:** [ADR-0001](0001-use-ragflow-as-baseline.md), [ADR-0004](0004-role-resolution-pluggable.md)

## Context

Module 3 (SHBVN Metadata Schema) requires a place to store ~26 fields per
document across 6 logical categories (Identity, Business Domain, Version
Control, Structure, Security, Relationships). Three candidate stores were
considered:

| Store | Shape | Query needs |
|---|---|---|
| MySQL (upstream RAGFlow already uses it) | Relational | Version lineage, state machine transactions, audit log joins |
| Elasticsearch (upstream chunk index) | Document | Retrieval-time filter pushdown (status='active' AND effective_date <= today AND role_allowed) |
| Both | Denormalised | Both query types, at sync cost |

Constraints that shape the decision:

- Version lifecycle ("at most one active row per logical doc") requires
  transactional semantics. ES has no multi-document transactions.
- Mandatory filter (BRD §8.1) runs at retrieval time on every chunk query
  — needs to be in the search index for pushdown.
- PDP compliance requires immutable audit trail on role grants/revokes and
  version transitions — relational is the natural fit.
- Upstream RAGFlow's `doc_metadata_service.py:20` comment claims ES
  `meta_fields` JSON is already the sole source of truth; BRD §8 disagrees
  and asserts MySQL authoritative. The BRD wins for SHBVN.

## Decision

**MySQL is the authoritative store. Elasticsearch gets a denormalised
read copy, projected from MySQL.**

1. All 3 SHBVN tables (`shbvn_doc_meta`, `shbvn_user_role`,
   `shbvn_doc_relationships`) live in the upstream `rag_flow` MySQL
   database alongside RAGFlow's own tables.
2. Writes go to MySQL first; ES is updated by a projector (Session 2B).
3. Retrieval-time mandatory filter runs against the ES projection (keeps
   the hot path in the search index).
4. **No database-level foreign keys** across SHBVN tables or to upstream
   RAGFlow tables. Reasons: (a) avoids cascade coupling during soft-delete;
   (b) keeps migration 001 standalone-testable without upstream schema;
   (c) referential integrity is enforced in the service layer instead.
5. **PK convention:** `VARCHAR(64)` for tables whose id is referenced
   (`shbvn_doc_meta.id`); `BIGINT UNSIGNED AUTO_INCREMENT` for standalone
   tables (`shbvn_user_role`, `shbvn_doc_relationships`). Rationale: UUID
   overhead only where external references exist.

## Consequences

**Positive:**

- Version lifecycle transactions are trivial (`DB.atomic()` wraps the
  supersede + mirror + relationship writes).
- Audit trail survives soft-deletes in both `shbvn_user_role` and
  `shbvn_doc_meta` (archived rows stay queryable for PDP data-subject
  requests).
- Session 2A is shippable as a standalone deliverable — no ES changes
  required. The ES projection is a separate, reviewable 2B concern.
- Matches upstream Peewee ORM and the shared MySQL container — no new
  datastore to operate.

**Negative / accepted:**

- Two systems of record for read paths (MySQL authoritative, ES denorm).
  Eventual consistency window during projection. Mitigation: writer
  publishes to both in-transaction where possible, otherwise an outbox
  + tail pattern in 2B.
- Lack of DB-level FKs means the service layer must enforce reference
  integrity (see `service.create_relationship`). This is a tradeoff for
  soft-delete ergonomics and standalone testability.
- Extra migration burden when a schema change requires both MySQL DDL
  and an ES mapping update.

## Alternatives considered

- **ES-only (upstream's apparent stance):** rejected. No transactions,
  weaker audit semantics, and any MySQL-side needs (joins, version
  lineage queries) would push us back to a second store anyway.
- **MySQL-only (no ES projection):** rejected. Retrieval-time filtering
  must run on every chunk query against the ES index; pulling the filter
  back through MySQL JOINs per query is not viable for latency.
- **Denormalised only in ES + MySQL as cache:** inverts the authority and
  loses transaction guarantees where we actually need them.

## Related decisions

- [ADR-0004](0004-role-resolution-pluggable.md) — pluggable role
  resolution, chosen so the same schema survives an eventual SSO migration.
- 2B (deferred): ES projector + query_filter pushdown.
- Module 13 (deferred): multi-tenant isolation — `tenant_id` was
  deliberately NOT added to the 2A schema (see Session 2A decision log).
