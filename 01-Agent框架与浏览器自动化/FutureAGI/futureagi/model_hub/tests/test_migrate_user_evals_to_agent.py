"""Tests for the migrate_user_evals_to_agent management command."""

from io import StringIO

import pytest
from django.core.management import call_command

from model_hub.models.choices import OwnerChoices
from model_hub.models.evals_metric import EvalTemplate, EvalTemplateVersion


def _make_llm_eval(organization, workspace, name, **overrides):
    config = {
        "output": "Pass/Fail",
        "eval_type_id": "CustomPromptEvaluator",
        "rule_prompt": "Check {{response}}.",
        "required_keys": ["response"],
        "check_internet": False,
    }
    config.update(overrides.pop("config", {}))
    kwargs = dict(
        name=name,
        organization=organization,
        workspace=workspace,
        owner=OwnerChoices.USER.value,
        eval_type="llm",
        config=config,
        criteria="Check {{response}}.",
        model="turing_large",
        visible_ui=True,
        output_type_normalized="pass_fail",
        pass_threshold=0.5,
    )
    kwargs.update(overrides)
    return EvalTemplate.no_workspace_objects.create(**kwargs)


@pytest.mark.unit
@pytest.mark.django_db
class TestMigrateUserEvalsToAgent:
    def test_flips_eval_type_and_config(self, organization, workspace):
        template = _make_llm_eval(organization, workspace, "flip-me")

        out = StringIO()
        call_command("migrate_user_evals_to_agent", stdout=out)

        template.refresh_from_db()
        assert template.eval_type == "agent"
        assert template.config["eval_type_id"] == "AgentEvaluator"
        assert template.config["agent_mode"] == "quick"
        assert template.config["tools"] == {"internet": False, "connectors": []}
        assert template.config["knowledge_bases"] == []
        assert template.config["data_injection"] == {"variables_only": True}
        assert template.config["summary"] == {"type": "concise"}
        # Preserved
        assert template.config["rule_prompt"] == "Check {{response}}."
        assert template.model == "turing_large"
        assert template.pass_threshold == 0.5

    def test_dry_run_does_not_write(self, organization, workspace):
        template = _make_llm_eval(organization, workspace, "dry-run-me")
        original_config = dict(template.config)

        call_command("migrate_user_evals_to_agent", "--dry-run", stdout=StringIO())

        template.refresh_from_db()
        assert template.eval_type == "llm"
        assert template.config == original_config

    def test_idempotent(self, organization, workspace):
        template = _make_llm_eval(organization, workspace, "idempotent-me")

        call_command("migrate_user_evals_to_agent", stdout=StringIO())
        template.refresh_from_db()
        first_config = dict(template.config)

        out = StringIO()
        call_command("migrate_user_evals_to_agent", stdout=out)
        template.refresh_from_db()
        # Second run selects zero candidates (already agent type).
        assert template.config == first_config
        assert "Candidates: 0" in out.getvalue()

    def test_skips_system_templates_by_default(self, organization):
        system_eval = EvalTemplate.no_workspace_objects.create(
            name="system-llm-eval",
            organization=None,
            workspace=None,
            owner=OwnerChoices.SYSTEM.value,
            eval_type="llm",
            config={"eval_type_id": "CustomPromptEvaluator"},
            visible_ui=True,
        )

        call_command("migrate_user_evals_to_agent", stdout=StringIO())

        system_eval.refresh_from_db()
        assert system_eval.eval_type == "llm"
        assert system_eval.config["eval_type_id"] == "CustomPromptEvaluator"

    def test_include_system_flag_flips_system_templates(self, organization, workspace):
        system_eval = EvalTemplate.no_workspace_objects.create(
            name="system-llm-eval-opted-in",
            organization=None,
            workspace=None,
            owner=OwnerChoices.SYSTEM.value,
            eval_type="llm",
            config={
                "eval_type_id": "CustomPromptEvaluator",
                "rule_prompt": "Check {{response}}.",
                "check_internet": True,
            },
            visible_ui=True,
        )
        user_eval = _make_llm_eval(organization, workspace, "user-too")

        call_command(
            "migrate_user_evals_to_agent", "--include-system", stdout=StringIO()
        )

        system_eval.refresh_from_db()
        user_eval.refresh_from_db()
        assert system_eval.eval_type == "agent"
        assert system_eval.config["eval_type_id"] == "AgentEvaluator"
        assert system_eval.config["agent_mode"] == "quick"
        assert system_eval.config["tools"] == {"internet": True, "connectors": []}
        assert user_eval.eval_type == "agent"

    def test_skips_code_and_agent_templates(self, organization, workspace):
        code = _make_llm_eval(
            organization,
            workspace,
            "already-code",
            eval_type="code",
            config={"eval_type_id": "CustomCodeEval"},
        )
        agent = _make_llm_eval(
            organization,
            workspace,
            "already-agent",
            eval_type="agent",
            config={"eval_type_id": "AgentEvaluator"},
        )

        call_command("migrate_user_evals_to_agent", stdout=StringIO())

        code.refresh_from_db()
        agent.refresh_from_db()
        assert code.eval_type == "code"
        assert code.config["eval_type_id"] == "CustomCodeEval"
        assert agent.eval_type == "agent"
        assert agent.config["eval_type_id"] == "AgentEvaluator"

    def test_org_id_filter(self, organization, workspace):
        target = _make_llm_eval(organization, workspace, "target-org-eval")

        call_command(
            "migrate_user_evals_to_agent",
            f"--org-id={organization.id}",
            stdout=StringIO(),
        )

        target.refresh_from_db()
        assert target.eval_type == "agent"

    def test_preserves_existing_kb_and_tools(self, organization, workspace):
        """Existing knowledge_bases / tools / data_injection must survive the flip."""
        template = _make_llm_eval(
            organization,
            workspace,
            "has-kb",
            config={
                "knowledge_bases": ["kb-uuid-1", "kb-uuid-2"],
                "tools": {"internet": True, "connectors": ["conn-1"]},
                "data_injection": {"trace_context": True},
                "summary": {"type": "long"},
            },
        )

        call_command("migrate_user_evals_to_agent", stdout=StringIO())

        template.refresh_from_db()
        assert template.config["knowledge_bases"] == ["kb-uuid-1", "kb-uuid-2"]
        assert template.config["tools"] == {
            "internet": True,
            "connectors": ["conn-1"],
        }
        assert template.config["data_injection"] == {"trace_context": True}
        assert template.config["summary"] == {"type": "long"}

    def test_promotes_legacy_knowledge_base_id(self, organization, workspace):
        """Legacy scalar knowledge_base_id is promoted into the list form."""
        template = _make_llm_eval(
            organization,
            workspace,
            "legacy-kb",
            config={"knowledge_base_id": "legacy-kb-uuid"},
        )

        call_command("migrate_user_evals_to_agent", stdout=StringIO())

        template.refresh_from_db()
        assert template.config["knowledge_bases"] == ["legacy-kb-uuid"]

    def test_syncs_default_version_snapshot(self, organization, workspace, user):
        """The active EvalTemplateVersion snapshot is refreshed after the flip."""
        template = _make_llm_eval(organization, workspace, "versioned-llm")
        version = EvalTemplateVersion.objects.create_version(
            eval_template=template,
            prompt_messages=[],
            config_snapshot=dict(template.config),
            criteria=template.criteria,
            model=template.model,
            user=user,
            organization=organization,
            workspace=workspace,
        )
        assert version.is_default is True
        assert version.config_snapshot["eval_type_id"] == "CustomPromptEvaluator"

        call_command("migrate_user_evals_to_agent", stdout=StringIO())

        version.refresh_from_db()
        assert version.config_snapshot["eval_type_id"] == "AgentEvaluator"
        assert version.config_snapshot["agent_mode"] == "quick"
