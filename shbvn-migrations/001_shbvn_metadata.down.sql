-- ============================================================================
-- Rollback of 001_shbvn_metadata.sql
-- Order: reverse of creation. No DB FKs (all refs are plain columns),
--        but disable FK checks as safety against future FK additions.
-- ============================================================================
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS shbvn_doc_relationships;
DROP TABLE IF EXISTS shbvn_user_role;
DROP TABLE IF EXISTS shbvn_doc_meta;
SET FOREIGN_KEY_CHECKS = 1;
