-- ============================================================================
-- SHBVN Module 3 — Metadata Schema (Session 2A, migration 001)
-- Author: SHBVN AI Platform — Module 3A
-- Apply:    mysql -h ... -u ... -p ... rag_flow < 001_shbvn_metadata.sql
-- Rollback: mysql -h ... -u ... -p ... rag_flow < 001_shbvn_metadata.down.sql
--
-- BRD ref:  shbvn-docs/SHBVN_AI_Platform_BRD_v2.md §8 (Module 3)
-- ADR ref:  shbvn/docs/decisions/0003-metadata-storage-mysql-authoritative.md
--           shbvn/docs/decisions/0004-role-resolution-pluggable.md
-- Errata:   shbvn/docs/brd-errata.md — BRD §8.2 referenced but absent; six-category
--           taxonomy per §8.1 summary + Session 2A decisions record.
--
-- BRD §8.2 six-category mapping (reviewer aid):
--   1. Identity         : id, shbvn_doc_id, title, doc_type, source_system, language
--   2. Business Domain  : domain, department_owner, sub_topic, tags, regulatory_reference
--   3. Version Control  : version, status, effective_date, expiry_date,
--                         supersedes_doc_id, approved_at, approved_by
--   4. Structure        : (empty at doc level; chunk-level deferred to Session 3B)
--   5. Security         : classification, access_roles, contains_pii, pii_masked,
--                         uploaded_by, upload_ip
--   6. Relationships    : (via shbvn_doc_relationships table — 1-to-N)
--   + Timestamps        : created_at, updated_at
--   + Content integrity : content_hash (Module 2 Gate 2 consumer — NOT in BRD §8.2
--                         six-category but essential for ingestion pipeline)
--
-- Column count:  27 total in shbvn_doc_meta (Identity 4 + Business Domain 5 +
--                Version Control 7 + Structure 1 + Security 2 + PII 2 + Tags 1 +
--                Content integrity 1 + Audit 4 = 27).
-- Index count:   16 total (8 shbvn_doc_meta + 4 shbvn_user_role + 4 shbvn_doc_relationships).
-- ============================================================================


-- ============================================================================
-- Table 1: shbvn_doc_meta
-- Purpose: Authoritative document-level metadata. ES is denormalized read copy
--          (projection deferred to Session 2B).
-- Versioning: Option C — id = stable per-row PK; shbvn_doc_id = natural group key
--             shared across versions; UNIQUE(shbvn_doc_id, version).
-- BRD ref:   §8 (Module 3). See header for six-category mapping.
-- ============================================================================

CREATE TABLE IF NOT EXISTS shbvn_doc_meta (

  -- ────── Identity (4) ──────
  id                    VARCHAR(64)  NOT NULL COMMENT 'Stable per-row PK. Service-generated UUID/hash. Target of FK references.',
  shbvn_doc_id          VARCHAR(32)  NOT NULL COMMENT 'Natural group key shared across all versions of the same logical doc.',
  title                 VARCHAR(500) NOT NULL,
  language              VARCHAR(5)   NOT NULL DEFAULT 'vi' COMMENT 'BCP 47 language tag (vi, en, vi-VN, etc.). Not ENUM to support extended tags.',

  -- ────── Business Domain (5) ──────
  -- ENUM extension requires ALTER TABLE migration with downtime consideration.
  -- Adding new value: ALTER TABLE shbvn_doc_meta MODIFY COLUMN domain ENUM(<existing values>, 'new_value') NOT NULL;
  domain                ENUM('retail_banking','corporate_banking','treasury','risk',
                             'compliance','hr','operations','ict','general') NOT NULL,
  -- ENUM extension requires ALTER TABLE migration with downtime consideration.
  -- Adding new value: ALTER TABLE shbvn_doc_meta MODIFY COLUMN doc_type ENUM(<existing values>, 'new_value') NOT NULL;
  doc_type              ENUM('policy','circular','form','guideline','sop',
                             'training','announcement') NOT NULL,
  sub_topic             VARCHAR(100) NULL COMMENT 'Free-form sub-category within domain (e.g. "credit_card" under retail_banking).',
  department_owner      VARCHAR(200) NULL COMMENT 'SHBVN department responsible for maintenance.',
  regulatory_reference  VARCHAR(200) NULL COMMENT 'External regulator ref (e.g. "Thông tư 77/2025/TT-NHNN ngày 15/03/2025").',

  -- ────── Version Control (7) ──────
  version               VARCHAR(20)  NOT NULL DEFAULT '1.0' COMMENT 'Version string. Format consistency enforced in service.py, not DB.',
  -- ENUM extension requires ALTER TABLE migration with downtime consideration.
  -- Adding new value: ALTER TABLE shbvn_doc_meta MODIFY COLUMN status ENUM(<existing values>, 'new_value') NOT NULL;
  status                ENUM('draft','active','superseded','archived') NOT NULL DEFAULT 'draft',
  effective_date        DATE         NULL COMMENT 'Date doc becomes authoritative. Used by mandatory 2B filter.',
  expiry_date           DATE         NULL COMMENT 'Date doc ceases to be authoritative. service.py enforces effective_date <= expiry_date.',
  supersedes_doc_id     VARCHAR(64)  NULL COMMENT 'References shbvn_doc_meta.id (stable PK) of the specific version this row supersedes. Plain column, no DB FK (see ADR-0003).',
  approved_by           VARCHAR(100) NULL COMMENT 'Approver identifier. service.py rule: status=active => approved_by + approved_at NOT NULL.',
  approved_at           TIMESTAMP    NULL COMMENT 'Approval timestamp. Paired with approved_by (see above).',

  -- ────── Structure (1) — doc level only; chunk-level Structure deferred to 3B ──────
  -- ENUM extension requires ALTER TABLE migration with downtime consideration.
  -- Adding new value: ALTER TABLE shbvn_doc_meta MODIFY COLUMN source_system ENUM(<existing values>, 'new_value') NOT NULL DEFAULT 'manual';
  source_system         ENUM('s-basic','swing-portal','department-upload','external',
                             'data-warehouse','manual') NOT NULL DEFAULT 'manual',

  -- ────── Security (2) ──────
  -- ENUM extension requires ALTER TABLE migration with downtime consideration.
  -- Adding new value: ALTER TABLE shbvn_doc_meta MODIFY COLUMN classification ENUM(<existing values>, 'new_value') NOT NULL DEFAULT 'internal';
  classification        ENUM('public','internal','confidential','restricted') NOT NULL DEFAULT 'internal' COMMENT 'Fail-safe default: internal (not public).',
  access_roles          JSON         NOT NULL COMMENT 'Deny-by-default JSON array of role codes. Reserved values: "*" (any authenticated), "public" (unauthenticated). service.py rejects empty array.',

  -- ────── PII flags (2) — Module 5 PDP Compliance hooks ──────
  contains_pii          TINYINT(1)   NOT NULL DEFAULT 0 COMMENT 'Set by Module 5 PII detector at ingestion. Used by Gate 5 output validator.',
  pii_masked            TINYINT(1)   NOT NULL DEFAULT 0 COMMENT 'Set by Module 5 masking pipeline when PII is replaced with placeholders.',

  -- ────── Tags (1) ──────
  tags                  JSON         NULL DEFAULT NULL COMMENT 'Free-form tag list. App convention (service.py docstring): lowercase kebab-case, max 10 tags/doc, max 50 chars/tag.',

  -- ────── Content integrity (1) — Module 2 Gate 2 hook ──────
  content_hash          VARCHAR(64)  NULL COMMENT 'SHA-256 hex, populated by ingestion pipeline Module 2 Gate 2. Index deferred until Module 2 defines query pattern.',

  -- ────── Audit (4) ──────
  uploaded_by           VARCHAR(100) NOT NULL,
  upload_ip             VARCHAR(45)  NULL COMMENT 'IPv4 or IPv6. Captured at upload time for audit trail (PDP Law).',
  created_at            TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at            TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  -- ────── Indices (8) ──────
  PRIMARY KEY (id),
  UNIQUE KEY uq_shbvn_doc_meta_docid_version (shbvn_doc_id, version),
  KEY idx_shbvn_doc_meta_status_effective (status, effective_date),
  KEY idx_shbvn_doc_meta_domain_type (domain, doc_type),
  KEY idx_shbvn_doc_meta_classification (classification),
  KEY idx_shbvn_doc_meta_department_owner (department_owner),
  KEY idx_shbvn_doc_meta_supersedes (supersedes_doc_id),
  KEY idx_shbvn_doc_meta_uploaded_by (uploaded_by)

  -- Service-layer validation (not enforced at DB; see shbvn/metadata/service.py module docstring):
  --   - access_roles: must be non-empty JSON array on insert/update
  --   - status state machine: draft -> active -> superseded | archived (no backward transitions)
  --   - status='active' requires approved_by AND approved_at populated
  --   - exactly one row with status='active' per shbvn_doc_id (enforced by transaction)
  --   - effective_date <= expiry_date when both populated
  --   - version format consistency per shbvn_doc_id (e.g. semver or numeric)
  --   - tags: lowercase kebab-case, <=10 items, <=50 chars each
  --   - supersedes_doc_id must reference an existing row's id (not shbvn_doc_id)
  --   - chunk count: if needed, compute on-the-fly via ES or JOIN to upstream document table
  --     (not stored here — denorm dropped per YAGNI + no clean update hook)

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  ROW_FORMAT=DYNAMIC
  COMMENT='SHBVN authoritative document-level metadata. ES is denorm read copy (2B).';


-- ============================================================================
-- Table 2: shbvn_user_role
-- Purpose: Table-based role/clearance mapping (TableRoleResolver backend).
--          Pluggable: ClaimRoleResolver (SSO) will bypass this table.
-- Soft delete: revoked_at/revoked_by/revoke_reason (no hard DELETE — PDP audit).
-- BRD ref:   §8 (Module 3 Security category) + ADR-0004 pluggable role resolution.
--
-- PK convention: Hybrid — VARCHAR(64) cho tables có FK reference (shbvn_doc_meta),
--                BIGINT UNSIGNED AUTO_INCREMENT cho tables standalone (user_role,
--                relationships). Rationale: UUID overhead không cần cho tables
--                không được referenced.
-- ============================================================================

CREATE TABLE IF NOT EXISTS shbvn_user_role (

  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id         VARCHAR(100) NOT NULL COMMENT 'Matches upstream user.id shape (SSO subject id or internal user id).',
  role            VARCHAR(50)  NOT NULL COMMENT 'Role code. Free-form at DB layer; validated against shbvn-config/roles.yaml in app.',
  -- ENUM extension requires ALTER TABLE migration with downtime consideration.
  -- Adding new value: ALTER TABLE shbvn_user_role MODIFY COLUMN clearance_level ENUM(<existing values>, 'new_value') NOT NULL DEFAULT 'internal';
  clearance_level ENUM('public','internal','confidential','restricted') NOT NULL DEFAULT 'internal' COMMENT 'Orthogonal to role. Compared vs doc.classification at query time (user clearance >= doc classification required).',
  granted_by      VARCHAR(100) NOT NULL,
  granted_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at      TIMESTAMP    NULL COMMENT 'NULL = no expiry.',
  revoked_at      TIMESTAMP    NULL COMMENT 'Soft-delete marker. NULL = active. Never hard DELETE (PDP audit).',
  revoked_by      VARCHAR(100) NULL,
  revoke_reason   VARCHAR(500) NULL,
  created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  -- ────── Indices (4) ──────
  PRIMARY KEY (id),
  UNIQUE KEY uq_shbvn_user_role_user_role (user_id, role),
  KEY idx_shbvn_user_role_active (user_id, revoked_at, expires_at),
  KEY idx_shbvn_user_role_role (role)

  -- Service-layer validation (not enforced at DB; see shbvn/metadata/service.py):
  --   - Active role query: WHERE revoked_at IS NULL AND (expires_at IS NULL OR expires_at > NOW())
  --   - No hard DELETE — always soft-delete via revoked_at for PDP audit trail
  --   - Revoking a row: set revoked_at = CURRENT_TIMESTAMP, revoked_by, revoke_reason
  --   - granted_by required (no self-grant unless service principal)
  --   - role code must be in shbvn-config/roles.yaml whitelist (app-layer)
  --   - Effective clearance computation: user có thể có multiple role grants;
  --     effective clearance = MAX(clearance_level) theo ENUM ordering
  --     (public < internal < confidential < restricted).
  --     SELECT MAX(clearance_level) FROM shbvn_user_role
  --       WHERE user_id=? AND revoked_at IS NULL
  --         AND (expires_at IS NULL OR expires_at > NOW())

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  ROW_FORMAT=DYNAMIC
  COMMENT='TableRoleResolver backend. Soft-delete via revoked_at for PDP audit trail.';


-- ============================================================================
-- Table 3: shbvn_doc_relationships
-- Purpose: Directed doc-to-doc graph (supersedes, references, implements,
--          amends, parent_of, related_to). Authoritative for relation queries.
-- No FK to shbvn_doc_meta: keeps table standalone + soft-delete friendly +
--          avoids ON DELETE CASCADE complications (see ADR-0003).
-- BRD ref:   §8 (Module 3 Relationships category — 6th category, 1-to-N).
--
-- PK convention: Hybrid — VARCHAR(64) cho tables có FK reference (shbvn_doc_meta),
--                BIGINT UNSIGNED AUTO_INCREMENT cho tables standalone (user_role,
--                relationships). Rationale: UUID overhead không cần cho tables
--                không được referenced.
-- ============================================================================

CREATE TABLE IF NOT EXISTS shbvn_doc_relationships (

  id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  from_doc_id       VARCHAR(64)  NOT NULL COMMENT 'Source side. References shbvn_doc_meta.id (stable PK). Plain column, no DB FK.',
  to_doc_id         VARCHAR(64)  NOT NULL COMMENT 'Target side. References shbvn_doc_meta.id (stable PK). Plain column, no DB FK.',
  -- ENUM extension requires ALTER TABLE migration with downtime consideration.
  -- Adding new value: ALTER TABLE shbvn_doc_relationships MODIFY COLUMN relationship_type ENUM(<existing values>, 'new_value') NOT NULL;
  relationship_type ENUM('supersedes','references','implements','amends',
                         'parent_of','related_to') NOT NULL,
  created_by        VARCHAR(100) NULL COMMENT 'User who created relationship. NULL = system-generated (e.g., auto-created on version upload).',
  created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  -- ────── Indices (4) ──────
  PRIMARY KEY (id),
  UNIQUE KEY uq_shbvn_rel_triple (from_doc_id, to_doc_id, relationship_type),
  KEY idx_shbvn_rel_from_type (from_doc_id, relationship_type),
  KEY idx_shbvn_rel_to_type (to_doc_id, relationship_type)

  -- Service-layer validation (not enforced at DB; see shbvn/metadata/service.py):
  --   - from_doc_id != to_doc_id (no self-loops)
  --   - Uniqueness: (from_doc_id, to_doc_id, relationship_type) enforced via UNIQUE index.
  --     If historical re-creation needed, use soft-delete pattern (add revoked_at column)
  --     rather than allowing duplicates.
  --   - from_doc_id and to_doc_id must reference existing shbvn_doc_meta.id rows
  --   - supersedes relationship should mirror shbvn_doc_meta.supersedes_doc_id
  --     (service.py writes both atomically on version transition)

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  ROW_FORMAT=DYNAMIC
  COMMENT='Directed doc-to-doc relationship graph. Authoritative for relation queries.';
