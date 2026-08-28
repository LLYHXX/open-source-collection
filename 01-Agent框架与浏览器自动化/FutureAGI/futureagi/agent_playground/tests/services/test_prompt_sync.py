"""Tests for prompt playground → agent playground synchronization."""

import pytest

from model_hub.models.run_prompt import PromptVersion

pytestmark = pytest.mark.django_db


class TestSyncNodesForPromptVersion:
    """Test suite for sync_nodes_for_prompt_version function."""

    def test_sync_creates_new_input_port_when_variable_added(
        self, graph_version, llm_node_template, prompt_template, prompt_version
    ):
        """Test that adding a {{variable}} creates a new input port."""
        from agent_playground.models.node import Node
        from agent_playground.models.port import Port, PortDirection
        from agent_playground.models.prompt_template_node import PromptTemplateNode
        from agent_playground.services.prompt_sync import sync_nodes_for_prompt_version

        # Create LLM node (dynamic input mode)
        node = Node.no_workspace_objects.create(
            name="LLM Node",
            graph_version=graph_version,
            node_template=llm_node_template,
        )

        # Link to prompt
        PromptTemplateNode.no_workspace_objects.create(
            node=node,
            prompt_template=prompt_template,
            prompt_version=prompt_version,
        )

        # Initial state: 0 input ports
        assert (
            Port.no_workspace_objects.filter(
                node=node, direction=PortDirection.INPUT
            ).count()
            == 0
        )

        # Update PromptVersion with new variable
        prompt_version.prompt_config_snapshot = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Hello {{name}}"}],
                }
            ],
            "configuration": {"response_format": "text"},
        }
        prompt_version.variable_names = {"name": []}
        prompt_version.save()

        # Manually trigger sync (signal would do this automatically)
        sync_nodes_for_prompt_version(prompt_version)

        # Verify new input port created
        input_ports = Port.no_workspace_objects.filter(
            node=node, direction=PortDirection.INPUT
        )
        assert input_ports.count() == 1
        assert input_ports.first().display_name == "name"

    def test_sync_removes_input_port_when_variable_removed(
        self, graph_version, llm_node_template, prompt_template, prompt_version
    ):
        """Test that removing a {{variable}} soft-deletes the input port."""
        from agent_playground.models.node import Node
        from agent_playground.models.port import Port, PortDirection
        from agent_playground.models.prompt_template_node import PromptTemplateNode
        from agent_playground.services.prompt_sync import sync_nodes_for_prompt_version

        # Create LLM node (dynamic input mode)
        node = Node.no_workspace_objects.create(
            name="LLM Node",
            graph_version=graph_version,
            node_template=llm_node_template,
        )

        # Link to prompt
        PromptTemplateNode.no_workspace_objects.create(
            node=node,
            prompt_template=prompt_template,
            prompt_version=prompt_version,
        )

        # Create initial port
        port = Port.no_workspace_objects.create(
            node=node,
            key="custom",
            display_name="old_var",
            direction=PortDirection.INPUT,
            data_schema={"type": "string"},
        )

        # Update PromptVersion without the variable
        prompt_version.prompt_config_snapshot = {
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": "Hello"}]}
            ],
            "configuration": {"response_format": "text"},
        }
        prompt_version.variable_names = {}
        prompt_version.save()

        # Trigger sync
        sync_nodes_for_prompt_version(prompt_version)

        # Verify port was soft-deleted
        port.refresh_from_db()
        assert port.deleted is True

    def test_sync_updates_output_port_schema_on_response_format_change(
        self, graph_version, llm_node_template, prompt_template, prompt_version
    ):
        """Test that changing response_format updates output port schema."""
        from agent_playground.models.node import Node
        from agent_playground.models.port import Port, PortDirection
        from agent_playground.models.prompt_template_node import PromptTemplateNode
        from agent_playground.services.prompt_sync import sync_nodes_for_prompt_version

        # Create LLM node (dynamic input mode)
        node = Node.no_workspace_objects.create(
            name="LLM Node",
            graph_version=graph_version,
            node_template=llm_node_template,
        )

        # Link to prompt
        PromptTemplateNode.no_workspace_objects.create(
            node=node,
            prompt_template=prompt_template,
            prompt_version=prompt_version,
        )

        # Create output port with string schema
        output_port = Port.no_workspace_objects.create(
            node=node,
            key="response",
            display_name="response",
            direction=PortDirection.OUTPUT,
            data_schema={"type": "string"},
        )

        # Update PromptVersion to json response_format
        prompt_version.prompt_config_snapshot = {
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": "Hello"}]}
            ],
            "configuration": {"response_format": "json"},
        }
        prompt_version.save()

        # Trigger sync
        sync_nodes_for_prompt_version(prompt_version)

        # Verify output port schema updated
        output_port.refresh_from_db()
        assert output_port.data_schema["type"] == "object"

    def test_sync_handles_multiple_nodes_with_same_prompt_version(
        self, graph_version, prompt_version, prompt_template, llm_node_template
    ):
        """Test syncing when multiple nodes use the same PromptVersion."""
        from agent_playground.models.node import Node
        from agent_playground.models.port import Port, PortDirection
        from agent_playground.models.prompt_template_node import PromptTemplateNode
        from agent_playground.services.prompt_sync import sync_nodes_for_prompt_version

        # Create two nodes using same prompt version
        node1 = Node.no_workspace_objects.create(
            name="Node 1",
            graph_version=graph_version,
            node_template=llm_node_template,
        )
        node2 = Node.no_workspace_objects.create(
            name="Node 2",
            graph_version=graph_version,
            node_template=llm_node_template,
        )

        # Link both nodes to the same prompt version
        PromptTemplateNode.no_workspace_objects.create(
            node=node1,
            prompt_template=prompt_template,
            prompt_version=prompt_version,
        )
        PromptTemplateNode.no_workspace_objects.create(
            node=node2,
            prompt_template=prompt_template,
            prompt_version=prompt_version,
        )

        # Update PromptVersion with variable
        prompt_version.prompt_config_snapshot = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Hello {{user}}"}],
                }
            ],
            "configuration": {"response_format": "text"},
        }
        prompt_version.variable_names = {"user": []}
        prompt_version.save()

        # Trigger sync
        sync_nodes_for_prompt_version(prompt_version)

        # Verify both nodes got the new port
        for node in [node1, node2]:
            input_ports = Port.no_workspace_objects.filter(
                node=node, direction=PortDirection.INPUT
            )
            assert input_ports.count() == 1
            assert input_ports.first().display_name == "user"
