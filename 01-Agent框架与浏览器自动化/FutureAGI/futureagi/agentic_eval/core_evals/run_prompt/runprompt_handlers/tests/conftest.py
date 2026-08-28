"""
Pytest configuration for RunPrompt Handler tests.

This conftest.py registers custom markers used throughout the test suite.
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line(
        "markers", "integration: Integration tests with mocked APIs"
    )
    config.addinivalue_line(
        "markers", "live: Tests that call live APIs (requires API keys)"
    )
