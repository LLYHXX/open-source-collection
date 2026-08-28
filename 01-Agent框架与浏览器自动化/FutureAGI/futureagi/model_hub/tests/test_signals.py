"""Tests for model_hub signals."""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.django_db


class TestPromptVersionSignals:
    """Test Django signals for PromptVersion model."""

    @patch("agent_playground.services.prompt_sync.sync_nodes_for_prompt_version")
    def test_signal_triggered_on_variable_change(self, mock_sync, prompt_version):
        """Test that signal fires when variables change."""
        # Initial save
        prompt_version.prompt_config_snapshot = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Hi {{name}}"}],
                }
            ],
            "configuration": {},
        }
        prompt_version.variable_names = {"name": []}
        prompt_version.save()

        # Clear mock calls from initial save
        mock_sync.reset_mock()

        # Update with new variable
        prompt_version.variable_names = {"name": [], "city": []}
        prompt_version.save()

        # Verify sync was called
        assert mock_sync.called
        assert mock_sync.call_args[0][0] == prompt_version

    @patch("agent_playground.services.prompt_sync.sync_nodes_for_prompt_version")
    def test_signal_not_triggered_on_metadata_change(self, mock_sync, prompt_version):
        """Test that signal doesn't fire for irrelevant changes."""
        # Set initial state
        prompt_version.prompt_config_snapshot = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Hi {{name}}"}],
                }
            ],
            "configuration": {},
        }
        prompt_version.variable_names = {"name": []}
        prompt_version.save()

        # Clear mock calls from initial save
        mock_sync.reset_mock()

        # Update irrelevant field (metadata)
        prompt_version.metadata = {"key": "value"}
        prompt_version.save()

        # Verify sync was NOT called
        assert not mock_sync.called

    @patch("agent_playground.services.prompt_sync.sync_nodes_for_prompt_version")
    def test_signal_triggered_on_response_format_change(
        self, mock_sync, prompt_version
    ):
        """Test that signal fires when response_format changes."""
        # Initial save
        prompt_version.prompt_config_snapshot = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Hi"}],
                }
            ],
            "configuration": {"response_format": {"type": "text"}},
        }
        prompt_version.variable_names = {}
        prompt_version.save()

        # Clear mock calls from initial save
        mock_sync.reset_mock()

        # Update response_format
        prompt_version.prompt_config_snapshot = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Hi"}],
                }
            ],
            "configuration": {"response_format": {"type": "json_object"}},
        }
        prompt_version.save()

        # Verify sync was called
        assert mock_sync.called
        assert mock_sync.call_args[0][0] == prompt_version

    @patch("agent_playground.services.prompt_sync.sync_nodes_for_prompt_version")
    def test_signal_not_triggered_on_creation(self, mock_sync, organization, workspace):
        """Test that signal doesn't fire when PromptVersion is first created."""
        from model_hub.models.run_prompt import PromptTemplate, PromptVersion

        # Create new PromptTemplate
        template = PromptTemplate.objects.create(
            name="Test Template",
            organization=organization,
            workspace=workspace,
        )

        # Create new PromptVersion (created=True)
        new_version = PromptVersion.objects.create(
            original_template=template,
            prompt_config_snapshot={
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": "Hi {{name}}"}],
                    }
                ],
                "configuration": {"response_format": {"type": "text"}},
            },
            variable_names={"name": []},
        )

        # Verify sync was NOT called (because created=True)
        assert not mock_sync.called
