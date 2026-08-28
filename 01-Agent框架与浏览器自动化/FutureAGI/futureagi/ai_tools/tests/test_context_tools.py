import pytest

from ai_tools.registry import registry


class TestWhoamiTool:
    def test_whoami_returns_user_info(self, tool_context):
        tool = registry.get("whoami")
        result = tool.run({}, tool_context)

        assert not result.is_error
        assert tool_context.user.email in result.content
        assert tool_context.user.name in result.content
        assert tool_context.organization.name in result.content
        assert tool_context.workspace.name in result.content

    def test_whoami_has_structured_data(self, tool_context):
        tool = registry.get("whoami")
        result = tool.run({}, tool_context)

        assert result.data is not None
        assert result.data["user_email"] == tool_context.user.email
        assert result.data["organization_name"] == tool_context.organization.name
        assert result.data["workspace_name"] == tool_context.workspace.name


class TestListWorkspacesTool:
    def test_list_workspaces_returns_table(self, tool_context):
        tool = registry.get("list_workspaces")
        result = tool.run({}, tool_context)

        assert not result.is_error
        assert "Workspaces" in result.content
        assert tool_context.workspace.name in result.content

    def test_list_workspaces_has_structured_data(self, tool_context):
        tool = registry.get("list_workspaces")
        result = tool.run({}, tool_context)

        assert result.data is not None
        assert "workspaces" in result.data
        assert len(result.data["workspaces"]) >= 1
        ws = result.data["workspaces"][0]
        assert "id" in ws
        assert "name" in ws


class TestReadSchemaTool:
    def test_read_schema_evaluations(self, tool_context):
        tool = registry.get("read_schema")
        result = tool.run({"entity_type": "evaluations"}, tool_context)

        assert not result.is_error
        assert "Evaluation Schema" in result.content
        assert "status" in result.content
        assert "eval_template" in result.content

    def test_read_schema_datasets(self, tool_context):
        tool = registry.get("read_schema")
        result = tool.run({"entity_type": "datasets"}, tool_context)

        assert not result.is_error
        assert "Dataset Schema" in result.content
        assert "Column Schema" in result.content

    def test_read_schema_traces(self, tool_context):
        tool = registry.get("read_schema")
        result = tool.run({"entity_type": "traces"}, tool_context)

        assert not result.is_error
        assert "Trace Schema" in result.content
        assert "Span Schema" in result.content

    def test_read_schema_invalid_type(self, tool_context):
        tool = registry.get("read_schema")
        result = tool.run({"entity_type": "invalid"}, tool_context)

        assert result.is_error


class TestReadTaxonomyTool:
    def test_taxonomy_dataset_sources(self, tool_context):
        tool = registry.get("read_taxonomy")
        result = tool.run({"category": "dataset_sources"}, tool_context)

        assert not result.is_error
        assert "BUILD" in result.content
        assert "UPLOAD" in result.content
        assert "API" in result.content
        assert "SYNTHETIC" in result.content

    def test_taxonomy_trace_span_types(self, tool_context):
        tool = registry.get("read_taxonomy")
        result = tool.run({"category": "trace_span_types"}, tool_context)

        assert not result.is_error
        assert "llm" in result.content
        assert "tool" in result.content
        assert "agent" in result.content

    def test_taxonomy_model_types(self, tool_context):
        tool = registry.get("read_taxonomy")
        result = tool.run({"category": "model_types"}, tool_context)

        assert not result.is_error
        assert "GENERATIVE_LLM" in result.content

    def test_taxonomy_eval_types(self, tool_context):
        tool = registry.get("read_taxonomy")
        result = tool.run({"category": "eval_types"}, tool_context)

        # May have no templates in test db, but should not error
        assert not result.is_error

    def test_taxonomy_invalid_category(self, tool_context):
        tool = registry.get("read_taxonomy")
        result = tool.run({"category": "invalid"}, tool_context)

        assert result.is_error
