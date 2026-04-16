"""Unit / integration tests for SHBVN Module 3 metadata layer.

Covers:
    - :mod:`shbvn.metadata.schema` (Peewee models + EnumField / JSONField)
    - :mod:`shbvn.metadata.service` (CRUD + validators + state machine)
    - :mod:`shbvn.metadata.role_resolver` (Protocol + both implementations)

Backed by the real MySQL instance created via migration 001. The
``_clean_test_rows`` autouse fixture in ``conftest.py`` handles row
cleanup around each test using the ``test-`` identifier prefix.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from peewee import IntegrityError

from shbvn.metadata import role_resolver, schema, service


# ─────────────────────────── schema-level tests ───────────────────────────


def test_doc_meta_happy_path_roundtrip():
    """Insert a doc row, read back, verify JSON/ENUM/defaults preserved."""
    service.create_doc_meta(
        id="test-doc-1",
        shbvn_doc_id="TEST-SHBVN-1",
        title="Happy path",
        domain="retail_banking",
        doc_type="policy",
        access_roles=["analyst"],
        tags=["happy-path", "unit-test"],
        uploaded_by="pytest",
    )
    row = service.get_doc_meta("test-doc-1")
    assert row is not None
    assert row.domain == "retail_banking"
    assert row.doc_type == "policy"
    assert row.access_roles == ["analyst"]
    assert row.tags == ["happy-path", "unit-test"]
    # Defaults materialised
    assert row.language == "vi"
    assert row.classification == "internal"
    assert row.status == "draft"
    assert row.contains_pii == 0
    assert row.pii_masked == 0


def test_doc_meta_enum_rejected_pre_db():
    """EnumField raises ValueError before hitting DB for invalid domain."""
    with pytest.raises(ValueError):
        schema.ShbvnDocMeta.create(
            id="test-doc-enum",
            shbvn_doc_id="TEST-ENUM",
            title="bad enum",
            domain="not_a_real_domain",
            doc_type="policy",
            access_roles=["x"],
            uploaded_by="pytest",
        )


def test_doc_meta_unique_docid_version_enforced():
    """DB-level UNIQUE(shbvn_doc_id, version) rejects duplicate version."""
    service.create_doc_meta(
        id="test-doc-uq-a",
        shbvn_doc_id="TEST-UQ",
        title="v1",
        domain="retail_banking",
        doc_type="policy",
        version="1.0",
        access_roles=["x"],
        uploaded_by="pytest",
    )
    with pytest.raises(IntegrityError):
        service.create_doc_meta(
            id="test-doc-uq-b",
            shbvn_doc_id="TEST-UQ",
            title="duplicate v1",
            domain="retail_banking",
            doc_type="policy",
            version="1.0",
            access_roles=["x"],
            uploaded_by="pytest",
        )


# ─────────────────────────── service validators ───────────────────────────


def test_service_rejects_empty_access_roles():
    with pytest.raises(service.MetadataValidationError):
        service.create_doc_meta(
            id="test-doc-empty-roles",
            shbvn_doc_id="TEST-X",
            title="x",
            domain="retail_banking",
            doc_type="policy",
            access_roles=[],
            uploaded_by="pytest",
        )


def test_service_rejects_active_without_approver():
    with pytest.raises(service.MetadataValidationError):
        service.create_doc_meta(
            id="test-doc-active-no-appr",
            shbvn_doc_id="TEST-X",
            title="x",
            domain="retail_banking",
            doc_type="policy",
            status="active",
            access_roles=["x"],
            uploaded_by="pytest",
        )


def test_service_rejects_inverted_date_range():
    with pytest.raises(service.MetadataValidationError):
        service.create_doc_meta(
            id="test-doc-bad-dates",
            shbvn_doc_id="TEST-X",
            title="x",
            domain="retail_banking",
            doc_type="policy",
            access_roles=["x"],
            effective_date=date(2026, 5, 1),
            expiry_date=date(2026, 4, 1),
            uploaded_by="pytest",
        )


def test_service_rejects_bad_tag_format():
    with pytest.raises(service.MetadataValidationError):
        service.create_doc_meta(
            id="test-doc-bad-tag",
            shbvn_doc_id="TEST-X",
            title="x",
            domain="retail_banking",
            doc_type="policy",
            access_roles=["x"],
            tags=["UPPER_CASE"],
            uploaded_by="pytest",
        )


# ─────────────────────────── version lifecycle ───────────────────────────


def test_activate_version_supersedes_prior_active_in_same_transaction():
    """Two versions of one doc: activating v2 must flip v1 to superseded
    AND create a 'supersedes' relationship row AND mirror supersedes_doc_id."""
    service.create_doc_meta(
        id="test-doc-life-v1",
        shbvn_doc_id="TEST-LIFE",
        title="v1",
        domain="retail_banking",
        doc_type="policy",
        version="1.0",
        access_roles=["x"],
        uploaded_by="pytest",
    )
    service.activate_version("test-doc-life-v1", approved_by="mgr")
    service.create_doc_meta(
        id="test-doc-life-v2",
        shbvn_doc_id="TEST-LIFE",
        title="v2",
        domain="retail_banking",
        doc_type="policy",
        version="2.0",
        access_roles=["x"],
        uploaded_by="pytest",
    )

    v2 = service.activate_version("test-doc-life-v2", approved_by="mgr")

    v1 = service.get_doc_meta("test-doc-life-v1")
    assert v1.status == "superseded"
    assert v2.status == "active"
    assert v2.supersedes_doc_id == "test-doc-life-v1"
    rels = service.get_relationships_from("test-doc-life-v2", "supersedes")
    assert len(rels) == 1
    assert rels[0].to_doc_id == "test-doc-life-v1"


def test_service_rejects_illegal_state_transition():
    service.create_doc_meta(
        id="test-doc-trans",
        shbvn_doc_id="TEST-TRANS",
        title="x",
        domain="retail_banking",
        doc_type="policy",
        access_roles=["x"],
        uploaded_by="pytest",
    )
    with pytest.raises(service.StateTransitionError):
        # draft -> superseded is illegal (must go via active)
        service.update_doc_meta("test-doc-trans", status="superseded")


def test_archive_from_active_is_permitted():
    service.create_doc_meta(
        id="test-doc-archive",
        shbvn_doc_id="TEST-ARCH",
        title="x",
        domain="retail_banking",
        doc_type="policy",
        access_roles=["x"],
        uploaded_by="pytest",
    )
    service.activate_version("test-doc-archive", approved_by="mgr")
    archived = service.archive_doc_meta("test-doc-archive")
    assert archived.status == "archived"


# ─────────────────────────── user_role ───────────────────────────


def test_revoke_role_is_soft_delete():
    service.grant_role("test-user-rev", "analyst", granted_by="admin")
    service.revoke_role(
        "test-user-rev", "analyst", revoked_by="admin", reason="rotation"
    )
    # Still exists in the table (audit trail)
    row = schema.ShbvnUserRole.get(
        (schema.ShbvnUserRole.user_id == "test-user-rev")
        & (schema.ShbvnUserRole.role == "analyst")
    )
    assert row.revoked_at is not None
    assert row.revoked_by == "admin"
    assert row.revoke_reason == "rotation"
    # But filtered out of active queries
    assert service.get_active_roles("test-user-rev") == []


def test_effective_clearance_is_max_across_active_rows():
    """Two grants with different clearances. Effective = MAX per ENUM order."""
    service.grant_role(
        "test-user-cl", "analyst", granted_by="admin", clearance_level="internal"
    )
    service.grant_role(
        "test-user-cl",
        "reviewer",
        granted_by="admin",
        clearance_level="confidential",
    )
    assert service.get_effective_clearance("test-user-cl") == "confidential"
    # Revoke the higher clearance grant; effective drops to the remaining one
    service.revoke_role("test-user-cl", "reviewer", revoked_by="admin")
    assert service.get_effective_clearance("test-user-cl") == "internal"


# ─────────────────────────── relationships ───────────────────────────


def _make_doc(suffix: str) -> str:
    doc_id = f"test-rel-{suffix}"
    service.create_doc_meta(
        id=doc_id,
        shbvn_doc_id=f"TEST-REL-{suffix}",
        title=f"rel {suffix}",
        domain="retail_banking",
        doc_type="policy",
        access_roles=["x"],
        uploaded_by="pytest",
    )
    return doc_id


def test_relationship_self_loop_rejected():
    doc = _make_doc("self")
    with pytest.raises(service.MetadataValidationError):
        service.create_relationship(doc, doc, "references")


def test_relationship_unique_triple_enforced():
    a = _make_doc("a")
    b = _make_doc("b")
    service.create_relationship(a, b, "references")
    with pytest.raises(IntegrityError):
        service.create_relationship(a, b, "references")


# ─────────────────────────── role resolver ───────────────────────────


def test_claim_resolver_rejects_invalid_clearance():
    claims = {"test-user-bad": {"roles": ["x"], "clearance": "TOP_SECRET"}}
    resolver = role_resolver.ClaimRoleResolver(claims.get)
    with pytest.raises(ValueError):
        resolver.resolve_clearance("test-user-bad")
