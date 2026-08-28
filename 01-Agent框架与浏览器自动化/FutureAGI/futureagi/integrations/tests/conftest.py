"""Shared fixtures for integrations module tests."""

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from integrations.models import (
    ConnectionStatus,
    IntegrationConnection,
    IntegrationPlatform,
    SyncLog,
    SyncStatus,
)
from integrations.services.credentials import CredentialManager
from model_hub.models.ai_model import AIModel
from tracer.models.project import Project

# ---------------------------------------------------------------------------
# Auto-use: ensure INTEGRATION_ENCRYPTION_KEY is set for all tests
# ---------------------------------------------------------------------------

import base64
import secrets as _secrets

TEST_ENCRYPTION_KEY = base64.urlsafe_b64encode(_secrets.token_bytes(32)).decode()


@pytest.fixture(autouse=True)
def _set_encryption_key(settings):
    """Set the encryption key for all integration tests."""
    settings.INTEGRATION_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


@pytest.fixture
def int_project(db, organization, workspace):
    """Project for integration sync target (observe type)."""
    return Project.objects.create(
        name="Langfuse Import Project",
        organization=organization,
        workspace=workspace,
        model_type=AIModel.ModelTypes.GENERATIVE_LLM,
        trace_type="observe",
    )


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_credentials():
    """Plain-text credential dict."""
    return {
        "public_key": "pk-lf-abcdef1234567890",
        "secret_key": "sk-lf-secretkey9876543210",
    }


@pytest.fixture
def encrypted_credentials(sample_credentials):
    """Fernet-encrypted credential bytes."""
    return CredentialManager.encrypt(sample_credentials)


# ---------------------------------------------------------------------------
# IntegrationConnection (various states)
# ---------------------------------------------------------------------------


@pytest.fixture
def integration_connection(
    db, organization, workspace, user, int_project, encrypted_credentials
):
    """Active IntegrationConnection linked to int_project."""
    return IntegrationConnection.no_workspace_objects.create(
        organization=organization,
        workspace=workspace,
        created_by=user,
        platform=IntegrationPlatform.LANGFUSE,
        display_name="Test Langfuse",
        host_url="https://langfuse.example.com",
        encrypted_credentials=encrypted_credentials,
        project=int_project,
        external_project_name="my-langfuse-project",
        status=ConnectionStatus.ACTIVE,
        sync_interval_seconds=300,
        backfill_completed=True,
    )


@pytest.fixture
def paused_connection(integration_connection):
    integration_connection.status = ConnectionStatus.PAUSED
    integration_connection.save(update_fields=["status"])
    return integration_connection


@pytest.fixture
def error_connection(integration_connection):
    integration_connection.status = ConnectionStatus.ERROR
    integration_connection.status_message = "Auth failed"
    integration_connection.save(update_fields=["status", "status_message"])
    return integration_connection


@pytest.fixture
def syncing_connection(integration_connection):
    integration_connection.status = ConnectionStatus.SYNCING
    integration_connection.save(update_fields=["status"])
    return integration_connection


@pytest.fixture
def backfilling_connection(integration_connection):
    integration_connection.status = ConnectionStatus.BACKFILLING
    integration_connection.backfill_completed = False
    integration_connection.save(update_fields=["status", "backfill_completed"])
    return integration_connection


# ---------------------------------------------------------------------------
# SyncLog
# ---------------------------------------------------------------------------


@pytest.fixture
def sync_log(db, integration_connection):
    """Completed success SyncLog."""
    now = datetime.now(timezone.utc)
    return SyncLog.objects.create(
        connection=integration_connection,
        status=SyncStatus.SUCCESS,
        started_at=now - timedelta(minutes=5),
        completed_at=now,
        traces_fetched=10,
        traces_created=8,
        traces_updated=2,
        spans_synced=25,
        scores_synced=5,
        sync_from=now - timedelta(hours=1),
        sync_to=now,
    )


# ---------------------------------------------------------------------------
# Mock Langfuse API responses
# ---------------------------------------------------------------------------


@pytest.fixture
def langfuse_validate_success():
    return {
        "valid": True,
        "projects": [
            {"id": "proj-1", "name": "my-langfuse-project"},
            {"id": "proj-2", "name": "another-project"},
        ],
        "total_traces": 1500,
    }


@pytest.fixture
def langfuse_validate_failure():
    return {
        "valid": False,
        "error": "Invalid credentials. Please check your public key and secret key.",
    }


# ---------------------------------------------------------------------------
# Raw Langfuse trace data (realistic)
# ---------------------------------------------------------------------------


@pytest.fixture
def raw_langfuse_trace():
    """Realistic Langfuse trace with GENERATION, SPAN, EVENT + scores."""
    return {
        "id": "lf-trace-001",
        "name": "my-chat-chain",
        "userId": "user-42",
        "sessionId": "sess-abc",
        "metadata": {"env": "production"},
        "tags": ["production", "chat"],
        "input": {"prompt": "Hello"},
        "output": {"response": "Hi there"},
        "observations": [
            {
                "id": "obs-gen-001",
                "type": "GENERATION",
                "name": "chat-completion",
                "parentObservationId": None,
                "startTime": "2024-01-15T10:00:00.000Z",
                "endTime": "2024-01-15T10:00:01.500Z",
                "model": "gpt-4",
                "modelParameters": {"temperature": 0.7, "max_tokens": 1024},
                "input": [
                    {"role": "system", "content": "You are helpful."},
                    {"role": "user", "content": "Hello"},
                ],
                "output": "Hi there!",
                "usageDetails": {"input": 15, "output": 5, "total": 20},
                "latency": 1.5,
                "calculatedTotalCost": 0.002,
                "level": "DEFAULT",
                "metadata": {"provider": "openai"},
            },
            {
                "id": "obs-span-001",
                "type": "SPAN",
                "name": "retrieval",
                "parentObservationId": "obs-gen-001",
                "startTime": "2024-01-15T10:00:00.100Z",
                "endTime": "2024-01-15T10:00:00.500Z",
                "input": {"query": "search term"},
                "output": {"docs": ["doc1"]},
                "usageDetails": {},
                "latency": 0.4,
                "level": "DEBUG",
                "metadata": {},
            },
            {
                "id": "obs-event-001",
                "type": "EVENT",
                "name": "user-feedback",
                "parentObservationId": None,
                "startTime": "2024-01-15T10:00:02.000Z",
                "input": {"rating": 5},
                "usageDetails": {},
                "level": "DEFAULT",
                "metadata": {},
            },
        ],
        "scores": [
            {
                "id": "score-001",
                "name": "helpfulness",
                "value": 0.9,
                "dataType": "NUMERIC",
                "observationId": "obs-gen-001",
                "comment": "Very helpful response",
            },
            {
                "id": "score-002",
                "name": "is_appropriate",
                "value": 1,
                "dataType": "BOOLEAN",
                "observationId": None,
                "comment": "",
            },
        ],
    }


@pytest.fixture
def raw_langfuse_trace_no_name():
    """Langfuse trace with empty name (tests fallback logic)."""
    return {
        "id": "lf-trace-noname",
        "name": "",
        "userId": None,
        "sessionId": None,
        "metadata": {},
        "tags": [],
        "input": None,
        "output": None,
        "observations": [
            {
                "id": "obs-root",
                "type": "GENERATION",
                "name": "root-gen",
                "parentObservationId": None,
                "startTime": "2024-01-15T10:00:00.000Z",
                "endTime": "2024-01-15T10:00:01.000Z",
                "model": "claude-3-opus-20240229",
                "input": "test",
                "output": "response",
                "usageDetails": {
                    "promptTokens": 10,
                    "completionTokens": 5,
                    "totalTokens": 15,
                },
                "latency": 1.0,
                "level": "DEFAULT",
                "metadata": {},
            },
        ],
        "scores": [],
    }
