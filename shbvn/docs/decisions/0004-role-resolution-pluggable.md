# ADR-0004: Pluggable Role Resolution (Protocol + Table + Claim)

**Status:** Accepted
**Date:** 2026-04-16
**Deciders:** DuongLx (DDD)
**Supersedes:** —
**Related:** [ADR-0003](0003-metadata-storage-mysql-authoritative.md)

## Context

Session 1 flagged a tension (D3) in BRD §5 / §8: role codes drive the
mandatory retrieval filter (`role_allowed` on every query), but SHBVN's
authoritative source of identity is still undecided:

- Today: no corporate SSO integration on the RAGFlow stack. Roles must
  be administrable by DPD / Head ICT via a UI backed by the application
  database.
- Soon (Module 12, Q3 2026): SBI Holdings corporate SSO rollout planned.
  Roles will come from the SSO IdP (JWT / SAML attributes) and the local
  table becomes redundant.

If Module 3 hard-wires either source, the eventual flip becomes a
database migration + broad retrieval-path edit. We want the flip to be a
constructor swap.

## Decision

**Depend on a `RoleResolver` Protocol; ship two implementations.**

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class RoleResolver(Protocol):
    def resolve_roles(self, user_id: str) -> list[str]: ...
    def resolve_clearance(self, user_id: str) -> str | None: ...
```

Implementations (Session 2A):

1. **`TableRoleResolver`** — reads `shbvn_user_role` via
   `shbvn.metadata.service`. Default backend until Module 12 lands.
   Honours soft-delete (`revoked_at`) and expiry (`expires_at`)
   automatically.
2. **`ClaimRoleResolver`** — takes a `claim_lookup` callable that
   returns a pre-parsed `{roles, clearance}` dict per user id. Validates
   clearance against `CLASSIFICATION_CHOICES`. **Does NOT parse tokens**
   — token parsing belongs in the SSO middleware or Module 12
   orchestrator, not in the metadata layer.

Callers receive a `RoleResolver` via composition-root wiring (app
startup), not by importing a concrete class. This keeps the migration
path to SSO to "swap the binding, leave the call sites alone".

## Consequences

**Positive:**

- Module 12 SSO rollout becomes a one-line composition change + ship
  the `ClaimRoleResolver` wiring; no retrieval-path edits.
- Unit tests for role-dependent logic can substitute a trivial
  `ClaimRoleResolver(claim_lookup=fake.get)` without touching MySQL.
- `TableRoleResolver` remains a valid fallback even after SSO, useful
  for service accounts, break-glass admin roles, or systems that can't
  obtain a JWT.
- The Protocol is `runtime_checkable`, so tests / boot code can assert
  that the resolved binding satisfies the interface at startup.

**Negative / accepted:**

- Two code paths must stay behaviourally consistent. Mitigation: the
  `resolve_clearance` contract is identical (returns one of
  `CLASSIFICATION_CHOICES` or `None`), enforced by explicit validation
  in `ClaimRoleResolver`.
- Slightly more indirection than importing `service.get_active_roles`
  directly. Cost is low — the resolver is a thin adapter.

## Alternatives considered

- **Hard-code `service.get_active_roles` everywhere:** rejected. Module
  12 migration becomes a repo-wide find/replace.
- **Build SSO-first, skip the table:** rejected. SSO is quarters away;
  we need a working role admin UI now for DPD onboarding of Module 5
  DPIA workflows.
- **Abstract-base-class instead of Protocol:** rejected. Protocol gives
  structural subtyping (tests can use plain dicts with methods), plays
  nicely with duck-typed mocks, and avoids a new inheritance root.

## Related decisions

- [ADR-0003](0003-metadata-storage-mysql-authoritative.md) — MySQL as
  the authoritative store for `shbvn_user_role`.
- Module 12 (deferred): SSO integration. Will supply the `claim_lookup`
  callable implementation and change the composition root binding.
- Module 5 (deferred): PDP Compliance — uses `revoked_at` /
  `revoke_reason` audit fields populated by `service.revoke_role`.
