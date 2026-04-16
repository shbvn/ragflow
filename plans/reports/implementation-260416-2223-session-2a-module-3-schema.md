# Session 2A Wrap — Module 3A: SHBVN Metadata Schema

**Date:** 2026-04-16
**Branch:** `feat/module-3a-metadata-schema` (6 commits ahead of `main`)
**Status:** ✅ All Session 2A deliverables shipped + 15/15 tests green

## Deliverables

| # | Artifact | Status | File |
|---|---|---|---|
| 1 | Migration SQL (up) | ✅ | `shbvn-migrations/001_shbvn_metadata.sql` |
| 2 | Migration SQL (down) | ✅ | `shbvn-migrations/001_shbvn_metadata.down.sql` |
| 3 | Peewee models | ✅ | `shbvn/metadata/schema.py` (241 LOC) |
| 4 | CRUD + validation service | ✅ | `shbvn/metadata/service.py` (363 LOC) |
| 5 | Pluggable role resolver | ✅ | `shbvn/metadata/role_resolver.py` (106 LOC) |
| 6 | Pytest suite | ✅ | `shbvn-tests/unit/test_module_3_schema.py` + `conftest.py` |
| 7 | ADR-0003 (MySQL authoritative) | ✅ | `shbvn/docs/decisions/0003-*.md` |
| 8 | ADR-0004 (pluggable role resolution) | ✅ | `shbvn/docs/decisions/0004-*.md` |
| 9 | BRD errata log | ✅ | `shbvn/docs/brd-errata.md` (6 items) |
| 10 | progress.md update | ✅ | `shbvn-docs/progress.md` |

## Commit history (branch)

```
a114d5126 docs(metadata): add ADR-0003, ADR-0004, and BRD errata log
f751d278b test(metadata): add 15 pytest tests for Module 3A metadata layer
801da2e29 feat(metadata): add pluggable role resolver (Protocol + Table + Claim)
a8b735daa feat(metadata): add CRUD + validation service for metadata tables
f2cdfc41d feat(metadata): add Peewee models for SHBVN metadata tables
fd3378746 feat(metadata): add Module 3A MySQL migration 001 for SHBVN metadata schema
```

## Database artefacts verified

| Table | Columns | Indices | Row format |
|---|---|---|---|
| `shbvn_doc_meta` | 27 | 8 (PK + UNIQUE + 6 BTREE) | DYNAMIC |
| `shbvn_user_role` | 11 | 4 (PK + UNIQUE + 2 BTREE) | DYNAMIC |
| `shbvn_doc_relationships` | 6 | 4 (PK + UNIQUE + 2 BTREE) | DYNAMIC |

Total 44 cols, 16 logical indices. `ENGINE=InnoDB`, `utf8mb4` /
`utf8mb4_unicode_ci`, `ROW_FORMAT=DYNAMIC`.

## Migration idempotency — 4/4 scenarios PASS

| # | Scenario | Result |
|---|---|---|
| 1 | Fresh apply | 3 tables created, 0 errors |
| 2 | Rollback via `.down.sql` | 3 tables dropped cleanly |
| 3 | Reapply after rollback | identical schema |
| 4 | Double-apply (no rollback between) | `IF NOT EXISTS` no-op, exit 0 |

## Test coverage — 15/15 PASS (0.29s)

```
pytest shbvn-tests/unit/test_module_3_schema.py -v
```

| Layer | Tests |
|---|---|
| Schema (EnumField, JSONField, UNIQUE) | 3 |
| Service validators (access_roles, active-approver, date-order, tags) | 4 |
| Version lifecycle (activate transaction, transition, archive) | 3 |
| User role (soft-delete, effective_clearance MAX) | 2 |
| Relationships (self-loop, UNIQUE triple) | 2 |
| Role resolver (claim invalid clearance) | 1 |

Smoke test coverage during development: schema (6), service (15),
role_resolver (8) — 29 scenarios validated against live DB.

## Locked decisions (this session)

1. **Versioning Option C** — `id` stable per-row PK, `shbvn_doc_id`
   natural group key, `UNIQUE(shbvn_doc_id, version)`. `supersedes_doc_id`
   references `id` (not `shbvn_doc_id`).
2. **Hybrid PK convention** — VARCHAR(64) where FK-target; BIGINT
   AUTO_INCREMENT elsewhere.
3. **No DB-level foreign keys** — ref integrity is a service-layer
   concern (ADR-0003). Soft-delete and standalone migration win.
4. **MySQL authoritative, ES denorm** (ADR-0003). ES projector deferred
   to Session 2B.
5. **Pluggable role resolution** via Protocol + 2 impls (ADR-0004).
6. **Module 3 split into 3A / 3B** — chunk-level metadata, extractor,
   version_manager, query_filter all moved to 3B (depends on Module 1
   parser output spec).
7. **PII flags + content_hash** retained in `shbvn_doc_meta` as Module 5
   / Module 2 hooks (not in BRD §8.1 but explicitly confirmed as
   business requirement — see `brd-errata.md` E-002).
8. **`tenant_id` dropped** — deferred to Module 13 phase 2 to avoid
   premature multi-tenant design lock-in.

## BRD drift caught (logged in `brd-errata.md`)

- E-001: BRD §8.2 referenced but absent.
- E-002: BRD §7.2 referenced but absent.
- E-003: "v1.0 BRD full DDL" not in repo.
- E-004: `shbvn-docs/` vs `shbvn/docs/` path inconsistency.
- E-005: `api/apps/conversation_app.py` renamed to
  `api/apps/restful_apis/chat_api.py`.
- E-006: Upstream `doc_metadata_service.py:20` claim contradicts BRD §8.

## Self-flagged issues

1. **`shbvn/metadata/service.py` 363 LOC** — above the 200-line guideline
   but cohesive for 3 tables × CRUD × validators. Splitting would
   fragment related operations; YAGNI-compliant as is.
2. **`EnumField` name clash with Peewee's `Field.choices`** — caught by
   smoke-test before unit tests were written; fixed by renaming to
   `_allowed`. Documented in `schema.py` docstring.
3. **Column count discrepancy** — my earlier arithmetic said 26, actual
   is 27 (4+5+7+1+2+2+1+1+4=27). The column LIST was correct and
   approved; header comment updated to reflect reality. No schema
   change.
4. **Arithmetic verification lesson** — add a `SELECT COUNT(*) FROM
   information_schema.columns` step earlier in future schema reviews.

## Session 2B scope (explicit)

- ES projection of `shbvn_doc_meta` with `shbvn_*` prefix
- Chunk-level metadata propagation hook in
  `rag/svr/task_executor.py:246` (`build_chunks`)
- `shbvn_chunk_metadata` MySQL table (if Module 1 parser spec requires)
- Query filter pushdown in `rag/nlp/search.py:63`
- `version_manager.py` (lifecycle orchestration beyond `activate_version`)
- `extractor.py` (LLM-assisted metadata extraction from parsed docs)
- Connector integration (Module 4) reading through service CRUD

## Follow-up work (non-2A)

1. `git mv shbvn-docs shbvn/docs` — resolve E-004 path inconsistency.
   Includes `CLAUDE.md` reference updates.
2. BRD v3 revision — either fill in §7.2 / §8.2 or remove references.
3. Module 2 consumes `content_hash` (Gate 2 integrity check).
4. Module 5 writes `contains_pii` / `pii_masked` from PII detector.

## Unresolved questions

- None blocking Session 2A completion. All open items documented in
  `brd-errata.md` or `progress.md`.
- Stakeholder decision needed before Module 3B: does BRD v3 want a
  dedicated `shbvn_chunk_metadata` table, or is chunk-level metadata
  purely an ES projection?
