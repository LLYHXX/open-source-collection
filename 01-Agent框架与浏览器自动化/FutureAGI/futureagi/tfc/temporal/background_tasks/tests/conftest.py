"""
Pytest configuration for Temporal background tasks tests.
"""

import pytest


@pytest.fixture(autouse=True)
def mock_django_setup():
    """Mock Django setup for tests that don't need full Django."""
    import sys
    from unittest.mock import MagicMock

    # Mock Django modules if not already configured
    if "django" not in sys.modules:
        sys.modules["django"] = MagicMock()
        sys.modules["django.db"] = MagicMock()
        sys.modules["django.conf"] = MagicMock()


@pytest.fixture
def mock_temporal_start_activity():
    """Mock start_activity for testing."""
    from unittest.mock import patch

    with patch("tfc.temporal.drop_in.start_activity") as mock:
        yield mock


@pytest.fixture
def thread_pool_executor():
    """Provide a thread pool executor for tests."""
    from concurrent.futures import ThreadPoolExecutor

    executor = ThreadPoolExecutor(max_workers=2)
    yield executor
    executor.shutdown(wait=True)
