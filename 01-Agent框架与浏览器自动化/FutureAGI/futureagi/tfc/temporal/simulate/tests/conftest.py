"""
Pytest configuration for Temporal simulate tests.
"""

import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def mock_django_setup():
    """Mock Django setup for tests that don't need full Django."""
    # Mock Django modules if not already configured
    if "django" not in sys.modules or not hasattr(sys.modules.get("django"), "setup"):
        sys.modules["django"] = MagicMock()
        sys.modules["django.db"] = MagicMock()
        sys.modules["django.conf"] = MagicMock()


@pytest.fixture(autouse=True)
def mock_temporal_activity():
    """Mock Temporal activity module."""
    from unittest.mock import patch

    mock_activity = MagicMock()
    mock_activity.logger = MagicMock()

    with patch.dict(sys.modules, {"temporalio.activity": mock_activity}):
        yield mock_activity
