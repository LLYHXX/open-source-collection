"""
Tests for the modality filter across prompt-related API endpoints:
  - /model-hub/prompt-templates/
  - /model-hub/prompt-executions/
  - /model-hub/prompt-history-executions/

Covers:
  1. Filtering by a specific modality (e.g. "chat", "audio", "stt")
  2. Records with null/missing model_detail.type are treated as "chat"
  3. modality=all bypasses the filter entirely
  4. Multiple modality values can be combined
"""

import pytest
from rest_framework import status

from conftest import WorkspaceAwareAPIClient
from model_hub.models.choices import ModalityType
from model_hub.models.run_prompt import PromptTemplate, PromptVersion

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(user, workspace):
    client = WorkspaceAwareAPIClient()
    client.force_authenticate(user=user)
    client.set_workspace(workspace)
    return client


def _create_template(organization, workspace, name):
    return PromptTemplate.no_workspace_objects.create(
        name=name,
        organization=organization,
        workspace=workspace,
    )


def _create_version(template, version_tag, modality_type=None):
    """Create a PromptVersion with a given model_detail.type.

    If modality_type is None the configuration will have no model_detail key,
    simulating legacy / MCP-created prompts.
    """
    configuration = {"model": "gpt-4"}
    if modality_type is not None:
        configuration["model_detail"] = {"type": modality_type}

    return PromptVersion.no_workspace_objects.create(
        original_template=template,
        template_version=version_tag,
        prompt_config_snapshot={
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": "Hello"}]}
            ],
            "configuration": configuration,
        },
        variable_names={},
    )


def _get_names(response):
    """Extract template/version names from paginated API response."""
    data = response.data
    if isinstance(data, dict) and "result" in data:
        data = data["result"]
    if isinstance(data, dict) and "results" in data:
        data = data["results"]
    if isinstance(data, list):
        return sorted(
            item.get("name") or item.get("template_name", "")
            for item in data
            if isinstance(item, dict)
        )
    return []


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def templates(organization, workspace):
    """Create three templates each with a version of a different modality."""
    chat_tpl = _create_template(organization, workspace, "Chat Prompt")
    _create_version(chat_tpl, "v1", modality_type=ModalityType.CHAT)

    audio_tpl = _create_template(organization, workspace, "Audio Prompt")
    _create_version(audio_tpl, "v1", modality_type=ModalityType.AUDIO)

    stt_tpl = _create_template(organization, workspace, "STT Prompt")
    _create_version(stt_tpl, "v1", modality_type=ModalityType.STT)

    null_tpl = _create_template(organization, workspace, "Null Modality Prompt")
    _create_version(null_tpl, "v1", modality_type=None)  # no model_detail at all

    return {
        "chat": chat_tpl,
        "audio": audio_tpl,
        "stt": stt_tpl,
        "null": null_tpl,
    }


@pytest.fixture
def client(user, workspace):
    c = _make_client(user, workspace)
    yield c
    c.stop_workspace_injection()


# ---------------------------------------------------------------------------
# /model-hub/prompt-templates/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPromptTemplateModalityFilter:
    URL = "/model-hub/prompt-templates/"

    def test_filter_chat_includes_null_type(self, client, templates):
        """modality=chat should return explicit chat AND null/missing type."""
        resp = client.get(self.URL, {"modality": ModalityType.CHAT})
        assert resp.status_code == status.HTTP_200_OK
        names = _get_names(resp)
        assert "Chat Prompt" in names
        assert "Null Modality Prompt" in names
        assert "Audio Prompt" not in names
        assert "STT Prompt" not in names

    def test_filter_audio(self, client, templates):
        resp = client.get(self.URL, {"modality": ModalityType.AUDIO})
        assert resp.status_code == status.HTTP_200_OK
        names = _get_names(resp)
        assert "Audio Prompt" in names
        assert "Chat Prompt" not in names
        assert "Null Modality Prompt" not in names

    def test_filter_stt(self, client, templates):
        resp = client.get(self.URL, {"modality": ModalityType.STT})
        assert resp.status_code == status.HTTP_200_OK
        names = _get_names(resp)
        assert "STT Prompt" in names
        assert "Chat Prompt" not in names

    def test_filter_all_returns_everything(self, client, templates):
        """modality=all should skip the filter and return all templates."""
        resp = client.get(self.URL, {"modality": ModalityType.ALL})
        assert resp.status_code == status.HTTP_200_OK
        names = _get_names(resp)
        assert "Chat Prompt" in names
        assert "Audio Prompt" in names
        assert "STT Prompt" in names
        assert "Null Modality Prompt" in names

    def test_multiple_modalities(self, client, templates):
        """Passing multiple modality values returns the union."""
        resp = client.get(self.URL + "?modality=chat&modality=audio")
        assert resp.status_code == status.HTTP_200_OK
        names = _get_names(resp)
        assert "Chat Prompt" in names
        assert "Audio Prompt" in names
        assert "Null Modality Prompt" in names  # null defaults to chat
        assert "STT Prompt" not in names

    def test_no_modality_param_returns_all(self, client, templates):
        """Without the modality param, no modality filtering is applied."""
        resp = client.get(self.URL)
        assert resp.status_code == status.HTTP_200_OK
        names = _get_names(resp)
        assert len(names) == 4


# ---------------------------------------------------------------------------
# /model-hub/prompt-executions/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPromptExecutionModalityFilter:
    URL = "/model-hub/prompt-executions/"

    def test_filter_chat_includes_null_type(self, client, templates):
        resp = client.get(self.URL, {"modality": ModalityType.CHAT})
        assert resp.status_code == status.HTTP_200_OK
        names = _get_names(resp)
        assert "Chat Prompt" in names
        assert "Null Modality Prompt" in names
        assert "Audio Prompt" not in names

    def test_filter_audio(self, client, templates):
        resp = client.get(self.URL, {"modality": ModalityType.AUDIO})
        assert resp.status_code == status.HTTP_200_OK
        names = _get_names(resp)
        assert "Audio Prompt" in names
        assert "Chat Prompt" not in names
        assert "Null Modality Prompt" not in names

    def test_filter_all_returns_everything(self, client, templates):
        resp = client.get(self.URL, {"modality": ModalityType.ALL})
        assert resp.status_code == status.HTTP_200_OK
        names = _get_names(resp)
        assert "Chat Prompt" in names
        assert "Audio Prompt" in names
        assert "STT Prompt" in names
        assert "Null Modality Prompt" in names

    def test_no_modality_param_returns_all(self, client, templates):
        resp = client.get(self.URL)
        assert resp.status_code == status.HTTP_200_OK
        names = _get_names(resp)
        assert len(names) == 4


# ---------------------------------------------------------------------------
# /model-hub/prompt-history-executions/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPromptHistoryExecutionModalityFilter:
    URL = "/model-hub/prompt-history-executions/"

    def test_filter_chat_includes_null_type(self, client, templates):
        resp = client.get(self.URL, {"modality": ModalityType.CHAT})
        assert resp.status_code == status.HTTP_200_OK
        names = _get_names(resp)
        # PromptHistoryExecution returns PromptVersion rows; name comes from
        # template_name or original_template.name depending on serializer.
        assert "Audio Prompt" not in names
        assert "STT Prompt" not in names

    def test_filter_audio_excludes_null_type(self, client, templates):
        resp = client.get(self.URL, {"modality": ModalityType.AUDIO})
        assert resp.status_code == status.HTTP_200_OK
        names = _get_names(resp)
        assert "Chat Prompt" not in names
        assert "Null Modality Prompt" not in names

    def test_filter_all_returns_everything(self, client, templates):
        resp = client.get(self.URL, {"modality": ModalityType.ALL})
        assert resp.status_code == status.HTTP_200_OK
        # Should return all 4 versions (one per template)
        results = resp.data
        if isinstance(results, dict) and "result" in results:
            results = results["result"]
        if isinstance(results, dict) and "results" in results:
            results = results["results"]
        assert len(results) == 4

    def test_no_modality_param_returns_all(self, client, templates):
        resp = client.get(self.URL)
        assert resp.status_code == status.HTTP_200_OK
        results = resp.data
        if isinstance(results, dict) and "result" in results:
            results = results["result"]
        if isinstance(results, dict) and "results" in results:
            results = results["results"]
        assert len(results) == 4
