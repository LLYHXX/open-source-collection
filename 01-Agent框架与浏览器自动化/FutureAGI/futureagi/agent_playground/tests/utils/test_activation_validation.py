"""
Tests for validate_version_for_activation() holistic validation.
"""

import pytest
from django.core.exceptions import ValidationError

from agent_playground.models.choices import (
    GraphVersionStatus,
    NodeType,
    PortDirection,
)
from agent_playground.models.node import Node
from agent_playground.models.port import Port
from agent_playground.utils.graph_validation import validate_version_for_activation


def _create_node_no_validation(**kwargs):
    """Create a Node bypassing clean() validation."""
    node = Node(**kwargs)
    node.save(skip_validation=True)
    return node


def _create_port_no_validation(**kwargs):
    """Create a Port bypassing clean() validation."""
    port = Port(**kwargs)
    port.save(skip_validation=True)
    return port


@pytest.mark.unit
class TestValidateVersionForActivation:
    """Tests for the holistic activation validation function."""

    def test_valid_version_passes(
        self, db, graph_version, node, input_port, output_port
    ):
        """A version with valid nodes and ports passes without errors."""
        validate_version_for_activation(graph_version)

    def test_empty_version_passes(self, db, graph_version):
        """A version with no nodes/ports passes (nothing to validate)."""
        validate_version_for_activation(graph_version)

    def test_node_reserved_chars_in_name(self, db, graph_version, node_template):
        """Node with reserved characters in name is caught."""
        _create_node_no_validation(
            graph_version=graph_version,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="Bad.Node",
            config={},
            position={"x": 0, "y": 0},
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_version_for_activation(graph_version)
        messages = exc_info.value.messages
        assert any("Bad.Node" in str(m) for m in messages)
        assert any("reserved characters" in str(m) for m in messages)

    def test_atomic_node_missing_template(self, db, graph_version):
        """Atomic node without node_template is caught."""
        _create_node_no_validation(
            graph_version=graph_version,
            node_template=None,
            type=NodeType.ATOMIC,
            name="No Template",
            config={},
            position={"x": 0, "y": 0},
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_version_for_activation(graph_version)
        messages = exc_info.value.messages
        assert any("node_template" in str(m) for m in messages)

    def test_subgraph_node_missing_ref(self, db, graph_version):
        """Subgraph node without ref_graph_version is caught."""
        _create_node_no_validation(
            graph_version=graph_version,
            ref_graph_version=None,
            type=NodeType.SUBGRAPH,
            name="No Ref",
            config={},
            position={"x": 0, "y": 0},
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_version_for_activation(graph_version)
        messages = exc_info.value.messages
        assert any("ref_graph_version" in str(m) for m in messages)

    def test_output_port_reserved_chars(self, db, graph_version, node):
        """Output port with reserved chars in display_name is caught."""
        _create_port_no_validation(
            node=node,
            key="custom",
            display_name="bad.port",
            direction=PortDirection.OUTPUT,
            data_schema={"type": "string"},
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_version_for_activation(graph_version)
        messages = exc_info.value.messages
        assert any("reserved characters" in str(m) for m in messages)

    def test_port_invalid_key_for_strict_template(self, db, graph_version, node):
        """Port with key not in STRICT template definition is caught."""
        _create_port_no_validation(
            node=node,
            key="nonexistent_key",
            display_name="bad key port",
            direction=PortDirection.INPUT,
            data_schema={"type": "string"},
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_version_for_activation(graph_version)
        messages = exc_info.value.messages
        assert any("not allowed" in str(m) for m in messages)

    def test_multiple_errors_collected(self, db, graph_version, node_template):
        """Multiple errors across nodes and ports are collected in a single ValidationError."""
        # Node with reserved chars
        bad_node = _create_node_no_validation(
            graph_version=graph_version,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="Bad[Node]",
            config={},
            position={"x": 0, "y": 0},
        )
        # Atomic node missing template
        _create_node_no_validation(
            graph_version=graph_version,
            node_template=None,
            type=NodeType.ATOMIC,
            name="Missing Template",
            config={},
            position={"x": 100, "y": 0},
        )
        # Port with reserved chars on bad_node
        _create_port_no_validation(
            node=bad_node,
            key="custom",
            display_name="out.put",
            direction=PortDirection.OUTPUT,
            data_schema={"type": "string"},
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_version_for_activation(graph_version)
        messages = exc_info.value.messages
        # Should have at least 3 errors: name chars, missing template, port display_name
        assert len(messages) >= 3

    def test_integration_activate_version_with_invalid_nodes(
        self,
        db,
        graph,
        graph_version,
        node_template,
    ):
        """Activating a draft with invalid nodes raises ValidationError via activate_version_and_sync()."""
        from agent_playground.services.dataset_bridge import activate_version_and_sync

        # Create a node with reserved chars in name
        _create_node_no_validation(
            graph_version=graph_version,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="Node.With.Dots",
            config={},
            position={"x": 0, "y": 0},
        )

        with pytest.raises(ValidationError) as exc_info:
            activate_version_and_sync(graph, graph_version)

        messages = exc_info.value.messages
        assert any("reserved characters" in str(m) for m in messages)

        # Verify version was NOT activated (still draft)
        graph_version.refresh_from_db()
        assert graph_version.status == GraphVersionStatus.DRAFT

    def test_input_port_reserved_chars_allowed(self, db, graph_version, dynamic_node):
        """Input ports ARE allowed to have reserved chars in display_name (for dot-notation variables)."""
        Port.no_workspace_objects.create(
            node=dynamic_node,
            key="custom",
            display_name="Node1.response.data",
            direction=PortDirection.INPUT,
            data_schema={"type": "string"},
        )
        # Should not raise
        validate_version_for_activation(graph_version)

    def test_subgraph_node_with_non_empty_config(
        self, db, graph_version, active_referenced_graph_version
    ):
        """Subgraph node with non-empty config is caught."""
        _create_node_no_validation(
            graph_version=graph_version,
            ref_graph_version=active_referenced_graph_version,
            type=NodeType.SUBGRAPH,
            name="Bad Config Subgraph",
            config={"key": "value"},
            position={"x": 0, "y": 0},
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_version_for_activation(graph_version)
        messages = exc_info.value.messages
        assert any("empty config" in str(m) for m in messages)
