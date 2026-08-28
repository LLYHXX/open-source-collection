"""
Agentcc Models Tests

Tests for AgentccProject, AgentccAPIKey, AgentccRequestLog models.
"""

import pytest
from django.db import IntegrityError

from agentcc.models import AgentccAPIKey, AgentccProject, AgentccRequestLog


@pytest.fixture
def project(organization, workspace):
    """Create a test AgentccProject."""
    return AgentccProject.objects.create(
        name="test-project",
        organization=organization,
        workspace=workspace,
    )


@pytest.fixture
def api_key(organization, workspace):
    """Create a test AgentccAPIKey."""
    return AgentccAPIKey.objects.create(
        gateway_key_id="gw-key-123",
        key_prefix="pk-abc",
        name="test-key",
        owner="test-owner",
        organization=organization,
        workspace=workspace,
    )


@pytest.mark.integration
class TestAgentccProject:
    def test_create_project(self, project):
        assert project.name == "test-project"
        assert project.description == ""
        assert project.config == {}

    def test_project_str(self, project):
        assert str(project) == "test-project"

    def test_project_unique_per_org(self, project, organization, workspace):
        with pytest.raises(IntegrityError):
            AgentccProject.objects.create(
                name="test-project",
                organization=organization,
                workspace=workspace,
            )


@pytest.mark.integration
class TestAgentccAPIKey:
    def test_create_api_key(self, api_key):
        assert api_key.gateway_key_id == "gw-key-123"
        assert api_key.key_prefix == "pk-abc"
        assert api_key.status == AgentccAPIKey.ACTIVE
        assert api_key.allowed_models == []
        assert api_key.allowed_providers == []

    def test_api_key_str(self, api_key):
        assert str(api_key) == "test-key (pk-abc...)"

    def test_api_key_unique_key_id(self, api_key, organization, workspace):
        with pytest.raises(IntegrityError):
            AgentccAPIKey.objects.create(
                gateway_key_id="gw-key-123",
                name="another-key",
                organization=organization,
                workspace=workspace,
            )

    def test_api_key_revoke(self, api_key):
        api_key.status = AgentccAPIKey.REVOKED
        api_key.save(update_fields=["status"])
        api_key.refresh_from_db()
        assert api_key.status == AgentccAPIKey.REVOKED


@pytest.mark.integration
class TestAgentccRequestLog:
    def test_create_request_log(self, organization, workspace):
        log = AgentccRequestLog.objects.create(
            organization=organization,
            workspace=workspace,
            request_id="req-001",
            model="gpt-4",
            provider="openai",
            latency_ms=150,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost="0.005000",
            status_code=200,
        )
        assert log.request_id == "req-001"
        assert log.model == "gpt-4"
        assert log.provider == "openai"
        assert log.latency_ms == 150
        assert log.is_error is False
        assert log.is_stream is False

    def test_request_log_str(self, organization, workspace):
        log = AgentccRequestLog.objects.create(
            organization=organization,
            workspace=workspace,
            request_id="req-002",
            model="claude-3",
        )
        assert str(log) == "req-002 (claude-3)"
