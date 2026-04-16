"""service.py — CRUD + validation for SHBVN metadata tables.

Pure CRUD. No business side effects (no events, no ES sync, no audit emit);
callers compose these with higher-level logic.

Validation rules enforced here (mirror comments in migration 001):

shbvn_doc_meta:
    - access_roles: non-empty list on insert/update
    - status state machine: draft -> {active, archived};
                            active -> {superseded, archived};
                            superseded -> {archived}; archived is terminal
    - status='active' requires approved_by AND approved_at
    - exactly one status='active' row per shbvn_doc_id (enforced by
      activate_version() transaction that supersedes prior active)
    - effective_date <= expiry_date when both populated
    - tags: optional list; lowercase kebab-case; <=10 items; <=50 chars each
    - supersedes_doc_id references an existing shbvn_doc_meta.id
      (set by activate_version when auto-superseding)

shbvn_user_role:
    - granted_by required
    - no hard DELETE — revoke via revoked_at/revoked_by/revoke_reason
    - active = revoked_at IS NULL AND (expires_at IS NULL OR expires_at > NOW())
    - effective clearance = MAX(clearance_level) per ENUM order across active rows

shbvn_doc_relationships:
    - from_doc_id != to_doc_id (no self-loops)
    - from_doc_id and to_doc_id must reference existing shbvn_doc_meta.id rows
    - UNIQUE(from_doc_id, to_doc_id, relationship_type) enforced by DB

Role whitelist (``shbvn-config/roles.yaml``) is the responsibility of the
RoleResolver layer, not this module.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from peewee import DoesNotExist

from api.db.db_models import DB
from shbvn.metadata.schema import (
    CLASSIFICATION_CHOICES,
    ShbvnDocMeta,
    ShbvnDocRelationships,
    ShbvnUserRole,
)


# ─────────────────────────── Exceptions ───────────────────────────


class MetadataValidationError(ValueError):
    """Raised when input fails service-layer validation."""


class StateTransitionError(MetadataValidationError):
    """Raised when a status transition violates the state machine."""


# ─────────────────────────── Validators ───────────────────────────


_STATUS_TRANSITIONS = {
    "draft": {"active", "archived"},
    "active": {"superseded", "archived"},
    "superseded": {"archived"},
    "archived": set(),
}

_TAG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _require_access_roles(access_roles) -> None:
    if not isinstance(access_roles, list) or len(access_roles) == 0:
        raise MetadataValidationError("access_roles must be a non-empty list")


def _require_approved_when_active(status, approved_by, approved_at) -> None:
    if status == "active" and (not approved_by or not approved_at):
        raise MetadataValidationError(
            "status='active' requires approved_by and approved_at"
        )


def _require_date_order(effective_date, expiry_date) -> None:
    if effective_date and expiry_date and effective_date > expiry_date:
        raise MetadataValidationError("effective_date must be <= expiry_date")


def _validate_tags(tags) -> None:
    if tags is None:
        return
    if not isinstance(tags, list):
        raise MetadataValidationError("tags must be a list or None")
    if len(tags) > 10:
        raise MetadataValidationError("tags length must be <= 10")
    for t in tags:
        if not isinstance(t, str):
            raise MetadataValidationError(f"tag must be str, got {type(t).__name__}")
        if len(t) > 50:
            raise MetadataValidationError(f"tag {t!r} exceeds 50 chars")
        if not _TAG_PATTERN.match(t):
            raise MetadataValidationError(
                f"tag {t!r} must be lowercase kebab-case"
            )


def _validate_transition(old_status: str, new_status: str) -> None:
    if old_status == new_status:
        return
    if new_status not in _STATUS_TRANSITIONS.get(old_status, set()):
        raise StateTransitionError(
            f"illegal status transition {old_status!r} -> {new_status!r}"
        )


# ─────────────────────────── shbvn_doc_meta CRUD ───────────────────────────


def create_doc_meta(**fields) -> ShbvnDocMeta:
    """Create a doc meta row. Validates invariants before INSERT."""
    _require_access_roles(fields.get("access_roles"))
    _require_approved_when_active(
        fields.get("status", "draft"),
        fields.get("approved_by"),
        fields.get("approved_at"),
    )
    _require_date_order(fields.get("effective_date"), fields.get("expiry_date"))
    _validate_tags(fields.get("tags"))
    return ShbvnDocMeta.create(**fields)


def get_doc_meta(doc_id: str) -> Optional[ShbvnDocMeta]:
    """Return row or None."""
    try:
        return ShbvnDocMeta.get(ShbvnDocMeta.id == doc_id)
    except DoesNotExist:
        return None


def update_doc_meta(doc_id: str, **fields) -> ShbvnDocMeta:
    """Partial update. Re-validates affected invariants."""
    row = ShbvnDocMeta.get(ShbvnDocMeta.id == doc_id)

    new_status = fields.get("status", row.status)
    if new_status != row.status:
        _validate_transition(row.status, new_status)

    eff = fields.get("effective_date", row.effective_date)
    exp = fields.get("expiry_date", row.expiry_date)
    _require_date_order(eff, exp)

    if "access_roles" in fields:
        _require_access_roles(fields["access_roles"])
    if "tags" in fields:
        _validate_tags(fields["tags"])

    approved_by = fields.get("approved_by", row.approved_by)
    approved_at = fields.get("approved_at", row.approved_at)
    _require_approved_when_active(new_status, approved_by, approved_at)

    fields["updated_at"] = datetime.now()
    for k, v in fields.items():
        setattr(row, k, v)
    row.save()
    return row


def activate_version(
    doc_id: str,
    approved_by: str,
    approved_at: Optional[datetime] = None,
) -> ShbvnDocMeta:
    """Transition a row to ``active`` in a single transaction, superseding
    any prior active row of the same ``shbvn_doc_id``.

    Guarantees the invariant: at most one status='active' row per shbvn_doc_id.
    Side-effects within the same transaction:
      - prior active row(s) → status='superseded'
      - ``shbvn_doc_relationships`` row(s) inserted (``supersedes``)
      - activating row's ``supersedes_doc_id`` mirrors the last prior
        active row's ``id`` (stable per-row PK)
    """
    if approved_at is None:
        approved_at = datetime.now()
    now = datetime.now()
    with DB.atomic():
        target = ShbvnDocMeta.get(ShbvnDocMeta.id == doc_id)
        _validate_transition(target.status, "active")

        prior_query = ShbvnDocMeta.select().where(
            (ShbvnDocMeta.shbvn_doc_id == target.shbvn_doc_id)
            & (ShbvnDocMeta.status == "active")
            & (ShbvnDocMeta.id != doc_id)
        )
        last_prior_id: Optional[str] = None
        for prior in prior_query:
            prior.status = "superseded"
            prior.updated_at = now
            prior.save()

            already = ShbvnDocRelationships.select().where(
                (ShbvnDocRelationships.from_doc_id == doc_id)
                & (ShbvnDocRelationships.to_doc_id == prior.id)
                & (ShbvnDocRelationships.relationship_type == "supersedes")
            ).exists()
            if not already:
                ShbvnDocRelationships.create(
                    from_doc_id=doc_id,
                    to_doc_id=prior.id,
                    relationship_type="supersedes",
                    created_by="system",
                )
            last_prior_id = prior.id

        target.status = "active"
        target.approved_by = approved_by
        target.approved_at = approved_at
        if last_prior_id:
            target.supersedes_doc_id = last_prior_id
        target.updated_at = now
        target.save()
        return target


def archive_doc_meta(doc_id: str) -> ShbvnDocMeta:
    """Terminal soft-delete (status='archived'). No hard DELETE for docs."""
    return update_doc_meta(doc_id, status="archived")


# ─────────────────────────── shbvn_user_role CRUD ──────────────────────────


def grant_role(
    user_id: str,
    role: str,
    granted_by: str,
    clearance_level: str = "internal",
    expires_at: Optional[datetime] = None,
) -> ShbvnUserRole:
    """Create a role grant. ``granted_by`` is required (audit)."""
    if not granted_by:
        raise MetadataValidationError("granted_by is required")
    return ShbvnUserRole.create(
        user_id=user_id,
        role=role,
        clearance_level=clearance_level,
        granted_by=granted_by,
        expires_at=expires_at,
    )


def revoke_role(
    user_id: str, role: str, revoked_by: str, reason: str = ""
) -> ShbvnUserRole:
    """Soft-delete: set ``revoked_at``/``revoked_by``/``revoke_reason``."""
    row = ShbvnUserRole.get(
        (ShbvnUserRole.user_id == user_id) & (ShbvnUserRole.role == role)
    )
    now = datetime.now()
    row.revoked_at = now
    row.revoked_by = revoked_by
    row.revoke_reason = reason
    row.updated_at = now
    row.save()
    return row


def get_active_roles(user_id: str) -> list[ShbvnUserRole]:
    """Roles with ``revoked_at IS NULL`` and unexpired."""
    now = datetime.now()
    return list(
        ShbvnUserRole.select().where(
            (ShbvnUserRole.user_id == user_id)
            & ShbvnUserRole.revoked_at.is_null(True)
            & (
                ShbvnUserRole.expires_at.is_null(True)
                | (ShbvnUserRole.expires_at > now)
            )
        )
    )


def get_effective_clearance(user_id: str) -> Optional[str]:
    """Return MAX clearance per ENUM order across active rows, or None."""
    active = get_active_roles(user_id)
    if not active:
        return None
    order = {c: i for i, c in enumerate(CLASSIFICATION_CHOICES)}
    return max((r.clearance_level for r in active), key=order.__getitem__)


# ─────────────────────────── shbvn_doc_relationships CRUD ──────────────────


def create_relationship(
    from_doc_id: str,
    to_doc_id: str,
    relationship_type: str,
    created_by: Optional[str] = None,
) -> ShbvnDocRelationships:
    """Insert a directed relationship. Enforces no-self-loop + ref integrity."""
    if from_doc_id == to_doc_id:
        raise MetadataValidationError("from_doc_id == to_doc_id (self-loop)")
    if not ShbvnDocMeta.select().where(ShbvnDocMeta.id == from_doc_id).exists():
        raise MetadataValidationError(f"from_doc_id {from_doc_id!r} not found")
    if not ShbvnDocMeta.select().where(ShbvnDocMeta.id == to_doc_id).exists():
        raise MetadataValidationError(f"to_doc_id {to_doc_id!r} not found")
    return ShbvnDocRelationships.create(
        from_doc_id=from_doc_id,
        to_doc_id=to_doc_id,
        relationship_type=relationship_type,
        created_by=created_by,
    )


def get_relationships_from(
    doc_id: str, relationship_type: Optional[str] = None
) -> list[ShbvnDocRelationships]:
    """Outgoing relationships from ``doc_id`` (optionally filtered by type)."""
    q = ShbvnDocRelationships.select().where(
        ShbvnDocRelationships.from_doc_id == doc_id
    )
    if relationship_type is not None:
        q = q.where(ShbvnDocRelationships.relationship_type == relationship_type)
    return list(q)


def get_relationships_to(
    doc_id: str, relationship_type: Optional[str] = None
) -> list[ShbvnDocRelationships]:
    """Incoming relationships targeting ``doc_id``."""
    q = ShbvnDocRelationships.select().where(
        ShbvnDocRelationships.to_doc_id == doc_id
    )
    if relationship_type is not None:
        q = q.where(ShbvnDocRelationships.relationship_type == relationship_type)
    return list(q)


__all__ = [
    "MetadataValidationError",
    "StateTransitionError",
    # doc_meta
    "create_doc_meta",
    "get_doc_meta",
    "update_doc_meta",
    "activate_version",
    "archive_doc_meta",
    # user_role
    "grant_role",
    "revoke_role",
    "get_active_roles",
    "get_effective_clearance",
    # relationships
    "create_relationship",
    "get_relationships_from",
    "get_relationships_to",
]
