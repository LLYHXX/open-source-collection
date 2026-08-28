"""Tests for the LLM Prompt template definition."""

import jsonschema
import pytest
from django.core.exceptions import ValidationError

from agent_playground.models import Node, NodeTemplate
from agent_playground.models.choices import NodeType, PortMode
from agent_playground.templates import get_all_templates
from agent_playground.templates.llm_prompt import LLM_PROMPT_TEMPLATE

REQUIRED_FIELDS = {
    "name",
    "display_name",
    "description",
    "icon",
    "categories",
    "input_definition",
    "output_definition",
    "input_mode",
    "output_mode",
    "config_schema",
}


@pytest.mark.unit
class TestLLMPromptDefinitionStructure:
    """Tests for the template definition structure."""

    def test_has_all_required_fields(self):
        assert set(LLM_PROMPT_TEMPLATE.keys()) == REQUIRED_FIELDS

    def test_registered_in_registry(self):
        templates = get_all_templates()
        assert "llm_prompt" in templates
        assert templates["llm_prompt"] is LLM_PROMPT_TEMPLATE

    def test_input_mode_is_dynamic(self):
        assert LLM_PROMPT_TEMPLATE["input_mode"] == "dynamic"

    def test_output_mode_is_strict(self):
        assert LLM_PROMPT_TEMPLATE["output_mode"] == "strict"

    def test_input_definition_is_empty(self):
        """Dynamic input mode requires empty input_definition."""
        assert LLM_PROMPT_TEMPLATE["input_definition"] == []

    def test_output_port_has_key_and_data_schema(self):
        outputs = LLM_PROMPT_TEMPLATE["output_definition"]
        assert len(outputs) == 1
        assert outputs[0]["key"] == "response"
        assert outputs[0]["data_schema"] == {}
        assert outputs[0]["schema_source"] == "prompt_version"

    def test_categories(self):
        assert LLM_PROMPT_TEMPLATE["categories"] == ["llm", "ai", "prompt"]


@pytest.mark.unit
class TestLLMPromptConfigSchema:
    """Tests for config_schema — now an empty schema that accepts anything."""

    def test_config_schema_is_empty(self):
        assert LLM_PROMPT_TEMPLATE["config_schema"] == {}

    def test_empty_config_validates(self):
        """Empty config is valid since all config comes from PromptVersion."""
        jsonschema.validate(
            instance={},
            schema=LLM_PROMPT_TEMPLATE["config_schema"],
        )

    def test_any_config_validates(self):
        """Empty schema accepts any JSON value."""
        jsonschema.validate(
            instance={"arbitrary": "data", "count": 42},
            schema=LLM_PROMPT_TEMPLATE["config_schema"],
        )


@pytest.mark.unit
class TestLLMPromptDBIntegration:
    """Tests for creating NodeTemplate and Node records from the definition."""

    def test_db_creation_and_clean(self, db):
        """Creating a NodeTemplate from the definition and calling clean() passes."""
        template = NodeTemplate.no_workspace_objects.create(**LLM_PROMPT_TEMPLATE)
        template.clean()
        assert template.name == "llm_prompt"
        assert template.input_mode == PortMode.DYNAMIC
        assert template.input_definition == []

    def test_node_with_empty_config_validates(self, db, graph_version):
        """A Node with empty config validates since config comes from PromptVersion."""
        template = NodeTemplate.no_workspace_objects.create(**LLM_PROMPT_TEMPLATE)
        node = Node.no_workspace_objects.create(
            graph_version=graph_version,
            node_template=template,
            type=NodeType.ATOMIC,
            name="My LLM Node",
            config={},
            position={"x": 0, "y": 0},
        )
        node.clean()
