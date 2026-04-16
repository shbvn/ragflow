# BRD Errata — SHBVN_AI_Platform_BRD_v2.md

Running log of mismatches between the BRD and the actual codebase /
Session decisions, **discovered during implementation**. The BRD is
treated as read-only; corrections live here.

Format per entry:

- **Ref:** BRD section or phrase
- **Issue:** what the BRD says vs reality
- **Resolution:** authoritative answer used by the implementation

---

## E-001 — BRD §8.2 referenced but does not exist

**Ref:** BRD §8 Summary (line 581-602), "6-category metadata taxonomy",
several user prompts referencing "BRD §8.2 six-category taxonomy".

**Issue:** BRD v2 has only §8.1 (Summary). There is no §8.2 enumerating
the fields of each category. The phrase "~20 fields per chunk" in §8.1
gives a total count but no schema.

**Resolution:** Session 2A `shbvn_doc_meta` schema (27 columns) was
derived from banking-domain knowledge + Session 2A decisions record, not
from an authoritative BRD list. The six-category grouping in migration
001's header comment and in `shbvn/metadata/schema.py` is the canonical
Session 2A mapping until BRD v3 catches up.

---

## E-002 — BRD §7.2 referenced but does not exist

**Ref:** user prompt referencing "BRD §7.2 Module 3 DDL spec" for
`contains_pii` and `pii_masked`.

**Issue:** BRD v2 §7 is "Module 2: 5-Gate Security Layer" and contains
only §7.1 (Summary). No §7.2.

**Resolution:** `contains_pii` and `pii_masked` are kept in
`shbvn_doc_meta` as Module 5 (PDP Compliance) hooks regardless of BRD
location. They are set by the Module 5 PII detector / masking pipeline
at ingestion time (Gate 5 output validator reads `contains_pii`).

---

## E-003 — Reference to "v1.0 BRD" full DDL

**Ref:** BRD §8.1 line 588, "(full DDL in v1.0 BRD)".

**Issue:** No v1.0 BRD file exists in the repository. v2 is the only
version present.

**Resolution:** Treat migration 001
(`shbvn-migrations/001_shbvn_metadata.sql`) as the authoritative DDL.

---

## E-004 — Docs folder path: `shbvn-docs/` vs `shbvn/docs/`

**Ref:** BRD §4.1 (line 413-495) + existing directory
`shbvn-docs/` (with dash) + CLAUDE.md references.

**Issue:** The repo filesystem uses `shbvn-docs/` (with hyphen) and
contains `SHBVN_AI_Platform_BRD_v2.md`, `decisions/0001-*.md`, and
`progress.md`. Session 2A authoritative decision: `shbvn/docs/` (path
under `shbvn/`, no hyphen) is canonical.

**Resolution:** Session 2A wrote **new** docs (0003, 0004, this errata)
to `shbvn/docs/`. Migration completed in branch
`chore/docs-folder-migration` (2026-04-16): all contents of `shbvn-docs/`
moved to `shbvn/docs/`; CLAUDE.md + migration 001 SQL header references
updated.

**Residual drift:** BRD §4.1 still writes `shbvn-docs/`. Per BRD
read-only policy, BRD text is not edited; the path in BRD v2 should be
read as `shbvn/docs/`. Fix in BRD v3 revision.

---

## E-005 — `api/apps/conversation_app.py` does not exist

**Ref:** BRD §25 Dev Workflow mentions `conversation_app.py` as the chat
endpoint integration point for Module 2 security gates.

**Issue:** The file has been renamed/refactored upstream. The actual
chat endpoint is now `api/apps/restful_apis/chat_api.py:980`
(`session_completion`) with core pipeline in
`api/db/services/dialog_service.py:482` (`async_chat`).

**Resolution:** Module 2 integration points updated in Session 1
orientation report. BRD §25 wording "conversation_app.py" should be
read as "the chat endpoint" — the concrete upstream path may drift with
RAGFlow upgrades and belongs in the orientation report, not the BRD.

---

## E-006 — `doc_metadata_service.py` claims ES is sole source of truth

**Ref:** upstream `api/db/services/doc_metadata_service.py:20` comment:
"SOLE source of truth for document metadata — MySQL meta_fields column
has been removed".

**Issue:** This directly contradicts BRD §8 which mandates MySQL as
authoritative.

**Resolution:** Session 2A locks MySQL as authoritative via ADR-0003.
Upstream's ES-only stance is valid only for upstream's own
`meta_fields`; SHBVN's 3 metadata tables are independent and MySQL-
authoritative. The 2B projector will denormalise to ES with the
`shbvn_*` prefix so we never collide with upstream's projection.

---

## Follow-up work

1. ~~`git mv shbvn-docs shbvn/docs` (per E-004).~~ **Done 2026-04-16**
   in branch `chore/docs-folder-migration`.
2. ~~Update `CLAUDE.md` references from `shbvn-docs/` → `shbvn/docs/`.~~
   **Done** in same branch.
3. BRD v3 revision: either (a) remove the §8.2 / §7.2 references or
   (b) fill them in. Also update §4.1 path from `shbvn-docs/` to
   `shbvn/docs/`. Decide in a separate review.

---

*Last updated: 2026-04-16 (Session 2A + docs-folder migration).*
