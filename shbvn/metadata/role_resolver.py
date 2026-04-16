"""role_resolver.py — Pluggable role / clearance resolution.

Defines a :class:`RoleResolver` Protocol with two concrete implementations:

- :class:`TableRoleResolver`: reads ``shbvn_user_role`` via
  :mod:`shbvn.metadata.service`. Default backend for Session 2A.
- :class:`ClaimRoleResolver`: reads roles and clearance from a pre-parsed
  SSO claim dict (JWT/SAML attributes). Stub for future Module 12 / SSO
  integration — callers must supply the claim dict themselves; this module
  does NOT parse tokens.

Callers pick the implementation at composition root (app startup).
Code that needs roles should depend on the :class:`RoleResolver` Protocol,
not a concrete class, to keep the switch cheap.
"""

from __future__ import annotations

from typing import Mapping, Protocol, Sequence, runtime_checkable

from shbvn.metadata import service
from shbvn.metadata.schema import CLASSIFICATION_CHOICES


# ─────────────────────────── Protocol ───────────────────────────


@runtime_checkable
class RoleResolver(Protocol):
    """Anything that can answer "what roles / clearance does this user have?".

    Implementations MUST return:
      - ``resolve_roles``: a list of role-code strings (possibly empty).
      - ``resolve_clearance``: one of ``CLASSIFICATION_CHOICES`` or ``None``
        when the user has no active role grants.
    """

    def resolve_roles(self, user_id: str) -> list[str]: ...

    def resolve_clearance(self, user_id: str) -> str | None: ...


# ─────────────────────────── TableRoleResolver ───────────────────────────


class TableRoleResolver:
    """Resolver backed by the ``shbvn_user_role`` table.

    Delegates to :func:`service.get_active_roles` and
    :func:`service.get_effective_clearance`, so revocation + expiry rules
    are respected automatically.
    """

    def resolve_roles(self, user_id: str) -> list[str]:
        return [r.role for r in service.get_active_roles(user_id)]

    def resolve_clearance(self, user_id: str) -> str | None:
        return service.get_effective_clearance(user_id)


# ─────────────────────────── ClaimRoleResolver ───────────────────────────


class ClaimRoleResolver:
    """Resolver that reads pre-parsed SSO claims.

    The constructor takes a callable ``claim_lookup`` that, given a user id,
    returns a mapping with:

      - ``roles``: iterable of role-code strings
      - ``clearance``: optional clearance-level string (one of
        ``CLASSIFICATION_CHOICES``)

    Missing keys mean "no roles / no clearance".

    Session 2A stub: the caller is responsible for supplying the
    ``claim_lookup`` (typically wrapping a JWT / SAML context). No token
    parsing here — that belongs in Module 12 (orchestrator) or the SSO
    middleware.
    """

    def __init__(self, claim_lookup):
        self._lookup = claim_lookup

    def resolve_roles(self, user_id: str) -> list[str]:
        claim = self._lookup(user_id) or {}
        roles = claim.get("roles") or []
        return [str(r) for r in roles]

    def resolve_clearance(self, user_id: str) -> str | None:
        claim = self._lookup(user_id) or {}
        cl = claim.get("clearance")
        if cl is None:
            return None
        if cl not in CLASSIFICATION_CHOICES:
            raise ValueError(
                f"claim clearance {cl!r} not in {CLASSIFICATION_CHOICES}"
            )
        return cl


__all__ = [
    "RoleResolver",
    "TableRoleResolver",
    "ClaimRoleResolver",
]
