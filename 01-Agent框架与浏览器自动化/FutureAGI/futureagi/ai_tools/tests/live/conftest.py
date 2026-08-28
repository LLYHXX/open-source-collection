"""
Conftest for live integration tests.

Overrides django_db_setup so pytest-django does NOT create/migrate a separate
test database. Tests in this directory hit the real local dev database (tfc)
directly — the same data used by run_real_integration_tests.py.

Run with:
    PG_DB=tfc PG_USER=user PG_PASSWORD=password PG_HOST=localhost PG_PORT=5432 \
    uv run pytest ai_tools/tests/live/ -m live_llm -v -s
"""

import pytest


@pytest.fixture(scope="session")
def django_db_setup():
    """Use the real database as-is — no test DB creation."""
    pass
