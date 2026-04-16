"""Global test config for SHBVN test suite.

Responsibilities:
    - Make the repo root importable (``from shbvn.metadata import ...``).
    - Stub ``api.db.db_models`` BEFORE :mod:`shbvn.metadata.schema` is
      imported, so tests don't need the full RAGFlow runtime (settings,
      configs, env). We bind a dedicated :class:`MySQLDatabase` pointing
      at the same migrated dev container.
    - Rebind each model's Meta.database to the test DB.
    - Provide a session-scoped ``db`` fixture and an autouse
      function-scoped row cleanup.

Test data convention: every test prefixes identifiers with ``test-`` so
cleanup is prefix-scoped and doesn't touch any real data.

Connection target: ``ragflow-test-mysql-1`` on localhost:5457. Adjust via
env vars ``SHBVN_TEST_DB_*`` if needed.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

import pytest
from peewee import MySQLDatabase

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


_DB = MySQLDatabase(
    os.environ.get("SHBVN_TEST_DB_NAME", "rag_flow"),
    host=os.environ.get("SHBVN_TEST_DB_HOST", "127.0.0.1"),
    port=int(os.environ.get("SHBVN_TEST_DB_PORT", "5457")),
    user=os.environ.get("SHBVN_TEST_DB_USER", "root"),
    password=os.environ.get("SHBVN_TEST_DB_PASSWORD", "infini_rag_flow"),
    charset="utf8mb4",
)


_stub = types.ModuleType("api.db.db_models")
_stub.DB = _DB
sys.modules.setdefault("api", types.ModuleType("api"))
sys.modules.setdefault("api.db", types.ModuleType("api.db"))
sys.modules["api.db.db_models"] = _stub


from shbvn.metadata import schema  # noqa: E402


for _m in (schema.ShbvnDocMeta, schema.ShbvnUserRole, schema.ShbvnDocRelationships):
    _m._meta.database = _DB


def _wipe_test_rows() -> None:
    schema.ShbvnDocRelationships.delete().where(
        schema.ShbvnDocRelationships.from_doc_id.startswith("test-")
        | schema.ShbvnDocRelationships.to_doc_id.startswith("test-")
    ).execute()
    schema.ShbvnDocMeta.delete().where(
        schema.ShbvnDocMeta.id.startswith("test-")
    ).execute()
    schema.ShbvnUserRole.delete().where(
        schema.ShbvnUserRole.user_id.startswith("test-")
    ).execute()


@pytest.fixture(scope="session")
def db():
    _DB.connect(reuse_if_open=True)
    yield _DB
    _DB.close()


@pytest.fixture(autouse=True)
def _clean_test_rows(db):
    _wipe_test_rows()
    yield
    _wipe_test_rows()
