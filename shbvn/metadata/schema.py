"""SHBVN Metadata — Peewee models.

Thin ORM wrappers over the 3 MySQL tables created by
`shbvn-migrations/001_shbvn_metadata.sql`. Schema is authoritative in SQL;
these models provide typed Python access. DO NOT call ``create_table()`` —
DDL is managed via migrations.

Tables:
    - ``shbvn_doc_meta`` (27 cols): document-level metadata.
    - ``shbvn_user_role`` (11 cols): role/clearance mapping (TableRoleResolver).
    - ``shbvn_doc_relationships`` (6 cols): directed doc-to-doc graph.

Connection: reuses upstream ``api.db.db_models.DB`` singleton
(PooledMySQLDatabase with retry).

Enum handling: MySQL ENUM columns are accessed via :class:`EnumField`
which wraps ``CharField`` with runtime choice validation. The DB already
enforces the constraint at schema level; app-layer validation is
belt-and-suspenders for clearer error messages.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Iterable

from peewee import (
    BigAutoField,
    CharField,
    DateField,
    DateTimeField,
    Field,
    IntegerField,
    Model,
)

from api.db.db_models import DB


# ─────────────────────────── Custom field types ───────────────────────────


class JSONField(Field):
    """MySQL native JSON column. Serialises list/dict to/from JSON string."""

    field_type = "JSON"

    def db_value(self, value):
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False)

    def python_value(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, (list, dict)):
            return value
        return json.loads(value)


class EnumField(CharField):
    """CharField restricted to a tuple of allowed values.

    DB enforces via ENUM column type; this provides early validation with
    a helpful error before hitting the DB round-trip.

    Note: stored as ``_allowed`` (not ``choices``) to avoid clobber by
    Peewee's ``Field.__init__``, which resets ``self.choices = None``.
    """

    def __init__(self, allowed: Iterable[str], *args, **kwargs):
        self._allowed = tuple(allowed)
        kwargs.setdefault("max_length", max(len(c) for c in self._allowed) + 16)
        super().__init__(*args, **kwargs)

    def db_value(self, value):
        if value is not None and value not in self._allowed:
            raise ValueError(
                f"{value!r} not in allowed values {self._allowed}"
            )
        return super().db_value(value)


class TinyIntField(IntegerField):
    """TINYINT(1) for boolean semantics. Stored as 0/1."""

    field_type = "TINYINT"


# ─────────────────────────── ENUM value constants ───────────────────────────

DOMAIN_CHOICES = (
    "retail_banking", "corporate_banking", "treasury", "risk",
    "compliance", "hr", "operations", "ict", "general",
)
DOC_TYPE_CHOICES = (
    "policy", "circular", "form", "guideline", "sop",
    "training", "announcement",
)
STATUS_CHOICES = ("draft", "active", "superseded", "archived")
CLASSIFICATION_CHOICES = ("public", "internal", "confidential", "restricted")
SOURCE_SYSTEM_CHOICES = (
    "s-basic", "swing-portal", "department-upload",
    "external", "data-warehouse", "manual",
)
CLEARANCE_LEVEL_CHOICES = CLASSIFICATION_CHOICES
RELATIONSHIP_TYPE_CHOICES = (
    "supersedes", "references", "implements",
    "amends", "parent_of", "related_to",
)


# ─────────────────────────── Base model ───────────────────────────


class SHBVNBaseModel(Model):
    """Base for SHBVN tables.

    Does NOT inherit upstream ``DataBaseModel`` — we avoid the auto-injected
    ``create_time``/``create_date``/``update_time``/``update_date`` columns
    (upstream's BigInteger-epoch convention). SHBVN tables use standard SQL
    ``TIMESTAMP created_at``/``updated_at``.
    """

    class Meta:
        database = DB


# ─────────────────────────── Tables ───────────────────────────


class ShbvnDocMeta(SHBVNBaseModel):
    """Document-level metadata. See migration 001 for column semantics."""

    # Identity (4)
    id = CharField(max_length=64, primary_key=True)
    shbvn_doc_id = CharField(max_length=32, null=False)
    title = CharField(max_length=500, null=False)
    language = CharField(max_length=5, null=False, default="vi")

    # Business Domain (5)
    domain = EnumField(DOMAIN_CHOICES, null=False)
    doc_type = EnumField(DOC_TYPE_CHOICES, null=False)
    sub_topic = CharField(max_length=100, null=True)
    department_owner = CharField(max_length=200, null=True)
    regulatory_reference = CharField(max_length=200, null=True)

    # Version Control (7)
    version = CharField(max_length=20, null=False, default="1.0")
    status = EnumField(STATUS_CHOICES, null=False, default="draft")
    effective_date = DateField(null=True)
    expiry_date = DateField(null=True)
    supersedes_doc_id = CharField(max_length=64, null=True)
    approved_by = CharField(max_length=100, null=True)
    approved_at = DateTimeField(null=True)

    # Structure (1) — chunk-level deferred to 3B
    source_system = EnumField(SOURCE_SYSTEM_CHOICES, null=False, default="manual")

    # Security (2)
    classification = EnumField(
        CLASSIFICATION_CHOICES, null=False, default="internal"
    )
    access_roles = JSONField(null=False, default=list)

    # PII hooks (2) — Module 5
    contains_pii = TinyIntField(null=False, default=0)
    pii_masked = TinyIntField(null=False, default=0)

    # Tags (1)
    tags = JSONField(null=True)

    # Content integrity (1) — Module 2 Gate 2
    content_hash = CharField(max_length=64, null=True)

    # Audit (4) — DB provides CURRENT_TIMESTAMP defaults
    uploaded_by = CharField(max_length=100, null=False)
    upload_ip = CharField(max_length=45, null=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        database = DB
        table_name = "shbvn_doc_meta"


class ShbvnUserRole(SHBVNBaseModel):
    """Table-based role/clearance mapping (TableRoleResolver backend)."""

    id = BigAutoField()
    user_id = CharField(max_length=100, null=False)
    role = CharField(max_length=50, null=False)
    clearance_level = EnumField(
        CLEARANCE_LEVEL_CHOICES, null=False, default="internal"
    )
    granted_by = CharField(max_length=100, null=False)
    granted_at = DateTimeField(default=datetime.now)
    expires_at = DateTimeField(null=True)
    revoked_at = DateTimeField(null=True)
    revoked_by = CharField(max_length=100, null=True)
    revoke_reason = CharField(max_length=500, null=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        database = DB
        table_name = "shbvn_user_role"


class ShbvnDocRelationships(SHBVNBaseModel):
    """Directed doc-to-doc relationship graph."""

    id = BigAutoField()
    from_doc_id = CharField(max_length=64, null=False)
    to_doc_id = CharField(max_length=64, null=False)
    relationship_type = EnumField(RELATIONSHIP_TYPE_CHOICES, null=False)
    created_by = CharField(max_length=100, null=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        database = DB
        table_name = "shbvn_doc_relationships"


__all__ = [
    "ShbvnDocMeta",
    "ShbvnUserRole",
    "ShbvnDocRelationships",
    "EnumField",
    "JSONField",
    "TinyIntField",
    "DOMAIN_CHOICES",
    "DOC_TYPE_CHOICES",
    "STATUS_CHOICES",
    "CLASSIFICATION_CHOICES",
    "SOURCE_SYSTEM_CHOICES",
    "CLEARANCE_LEVEL_CHOICES",
    "RELATIONSHIP_TYPE_CHOICES",
]
