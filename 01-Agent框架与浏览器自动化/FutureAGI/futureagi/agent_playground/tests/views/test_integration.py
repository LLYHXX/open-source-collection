"""Integration tests for Agent Playground API workflows."""

import uuid

import pytest
from django.urls import reverse
from rest_framework import status

from agent_playground.models.choices import GraphVersionStatus, NodeType, PortDirection
from agent_playground.models.edge import Edge
from agent_playground.models.graph import Graph
from agent_playground.models.graph_version import GraphVersion
from agent_playground.models.node import Node
from agent_playground.models.node_connection import NodeConnection
from agent_playground.models.port import Port

# Note: api_client and authenticated_client fixtures are inherited from
# agent_playground/tests/conftest.py with proper workspace injection


class TestCreateGraphWorkflow:
    """
    Test the complete workflow for creating a new graph:
    1. Create graph (with empty draft v1)
    2. Create new version with nodes + node_connections (auto ports/edges)
    3. Publish via PATCH (promote to active)
    """

    def test_complete_create_workflow(
        self, authenticated_client, node_template, extensible_node_template
    ):
        """Test the complete graph creation workflow."""
        # Step 1: Create graph
        create_url = reverse("graph-list")
        create_data = {
            "name": "My Pipeline",
            "description": "A complete pipeline",
        }
        response = authenticated_client.post(
            create_url, data=create_data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        graph_id = response.data["result"]["id"]
        version_id = response.data["result"]["active_version"]["id"]
        assert response.data["result"]["active_version"]["version_number"] == 1
        assert (
            response.data["result"]["active_version"]["status"]
            == GraphVersionStatus.DRAFT
        )

        # Step 2: Create a new version with nodes + node_connections
        # Use different templates to avoid duplicate exposed output port names
        create_version_url = reverse("graph-versions", kwargs={"pk": graph_id})
        node1_id = str(uuid.uuid4())
        node2_id = str(uuid.uuid4())
        create_version_data = {
            "status": GraphVersionStatus.DRAFT,
            "nodes": [
                {
                    "id": node1_id,
                    "type": NodeType.ATOMIC,
                    "name": "LLM Chat",
                    "node_template_id": str(node_template.id),
                    "config": {"model": "gpt-4"},
                    "position": {"x": 100, "y": 200},
                },
                {
                    "id": node2_id,
                    "type": NodeType.ATOMIC,
                    "name": "Output",
                    "node_template_id": str(extensible_node_template.id),
                    "config": {},
                    "position": {"x": 400, "y": 200},
                },
            ],
            "node_connections": [
                {
                    "source_node_id": node1_id,
                    "target_node_id": node2_id,
                },
            ],
        }
        response = authenticated_client.post(
            create_version_url, data=create_version_data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        new_version_id = response.data["result"]["id"]
        assert len(response.data["result"]["nodes"]) == 2
        assert response.data["result"]["status"] == GraphVersionStatus.DRAFT

        # Step 3: Publish via PATCH
        update_url = reverse(
            "graph-version-detail",
            kwargs={"pk": graph_id, "version_id": new_version_id},
        )
        publish_data = {
            "status": GraphVersionStatus.ACTIVE,
            "commit_message": "Initial release",
        }
        response = authenticated_client.patch(
            update_url, data=publish_data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["result"]["status"] == GraphVersionStatus.ACTIVE
        assert response.data["result"]["commit_message"] == "Initial release"

        # Verify graph detail shows active version
        detail_url = reverse("graph-detail", kwargs={"pk": graph_id})
        response = authenticated_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["result"]["active_version"]["status"]
            == GraphVersionStatus.ACTIVE
        )


class TestCreateVersionAutoPortsFromTemplate:
    """Test that create_version auto-creates ports from strict/extensible templates."""

    def test_strict_template_auto_creates_ports(
        self, authenticated_client, graph, graph_version, node_template
    ):
        """Test that a strict template node gets ports from template definitions."""
        # node_template has input_definition=[{key: input1}] + output_definition=[{key: output1}]
        create_url = reverse("graph-versions", kwargs={"pk": str(graph.id)})
        data = {
            "nodes": [
                {
                    "id": str(uuid.uuid4()),
                    "type": NodeType.ATOMIC,
                    "name": "Strict Node",
                    "node_template_id": str(node_template.id),
                    "position": {"x": 100, "y": 200},
                },
            ],
        }
        response = authenticated_client.post(create_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        nodes = response.data["result"]["nodes"]
        assert len(nodes) == 1

        ports = nodes[0]["ports"]
        assert len(ports) == 2
        port_keys = {p["key"] for p in ports}
        assert "input1" in port_keys
        assert "output1" in port_keys

    def test_dynamic_template_creates_default_output_port(
        self, authenticated_client, graph, graph_version, dynamic_node_template
    ):
        """Test that a dynamic input_mode template node gets a default 'response' output port."""
        create_url = reverse("graph-versions", kwargs={"pk": str(graph.id)})
        data = {
            "nodes": [
                {
                    "id": str(uuid.uuid4()),
                    "type": NodeType.ATOMIC,
                    "name": "Dynamic Node",
                    "node_template_id": str(dynamic_node_template.id),
                    "position": {"x": 100, "y": 200},
                },
            ],
        }
        response = authenticated_client.post(create_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        ports = response.data["result"]["nodes"][0]["ports"]
        # DYNAMIC input_mode always creates a default "response" output port
        assert len(ports) == 1
        assert ports[0]["display_name"] == "response"
        assert ports[0]["direction"] == PortDirection.OUTPUT


class TestCreateVersionAutoEdges:
    """Test that create_version auto-creates edges by display_name matching."""

    def test_auto_creates_edges_by_name_matching(
        self, authenticated_client, graph, graph_version, node_template
    ):
        """Test that edges are auto-created where output.display_name == input.display_name."""
        # node_template: strict, input_definition=[{key: input1}], output_definition=[{key: output1}]
        # After auto port creation: Node1 gets ports input1+output1, Node2 gets input1+output1
        # Connection: Node1→Node2 should create edge from Node1.output1→Node2.input1
        create_url = reverse("graph-versions", kwargs={"pk": str(graph.id)})
        node1_id = str(uuid.uuid4())
        node2_id = str(uuid.uuid4())
        data = {
            "nodes": [
                {
                    "id": node1_id,
                    "type": NodeType.ATOMIC,
                    "name": "Node 1",
                    "node_template_id": str(node_template.id),
                    "position": {"x": 100, "y": 200},
                },
                {
                    "id": node2_id,
                    "type": NodeType.ATOMIC,
                    "name": "Node 2",
                    "node_template_id": str(node_template.id),
                    "position": {"x": 400, "y": 200},
                },
            ],
            "node_connections": [
                {
                    "source_node_id": node1_id,
                    "target_node_id": node2_id,
                },
            ],
        }
        response = authenticated_client.post(create_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        # Verify edges were auto-created
        new_version_id = response.data["result"]["id"]
        version = GraphVersion.no_workspace_objects.get(id=new_version_id)
        edges = Edge.no_workspace_objects.filter(graph_version=version)
        # Both templates define output1 and input1, but display_name matching works on
        # output port display_name == input port display_name.
        # Template output1 display_name="output1", template input1 display_name="input1"
        # These don't match, so 0 edges
        assert edges.count() == 0

    def test_auto_creates_edges_when_names_match(
        self, authenticated_client, graph, graph_version, db
    ):
        """Test edge auto-creation with matching port display_names across nodes."""
        from agent_playground.models.choices import PortMode
        from agent_playground.models.node_template import NodeTemplate

        # Use STRICT templates so ports are created from template definitions
        producer = NodeTemplate.no_workspace_objects.create(
            name="producer_template",
            display_name="Producer",
            description="Produces data",
            categories=["test"],
            input_definition=[],
            output_definition=[
                {
                    "key": "data_out",
                    "display_name": "data",
                    "data_schema": {"type": "string"},
                },
            ],
            input_mode=PortMode.STRICT,
            output_mode=PortMode.STRICT,
            config_schema={},
        )
        consumer = NodeTemplate.no_workspace_objects.create(
            name="consumer_template",
            display_name="Consumer",
            description="Consumes data",
            categories=["test"],
            input_definition=[
                {
                    "key": "data_in",
                    "display_name": "data",
                    "data_schema": {"type": "string"},
                },
            ],
            output_definition=[],
            input_mode=PortMode.STRICT,
            output_mode=PortMode.STRICT,
            config_schema={},
        )

        create_url = reverse("graph-versions", kwargs={"pk": str(graph.id)})
        producer_id = str(uuid.uuid4())
        consumer_id = str(uuid.uuid4())
        data = {
            "nodes": [
                {
                    "id": producer_id,
                    "type": NodeType.ATOMIC,
                    "name": "Producer",
                    "node_template_id": str(producer.id),
                    "position": {"x": 100, "y": 200},
                },
                {
                    "id": consumer_id,
                    "type": NodeType.ATOMIC,
                    "name": "Consumer",
                    "node_template_id": str(consumer.id),
                    "position": {"x": 400, "y": 200},
                },
            ],
            "node_connections": [
                {
                    "source_node_id": producer_id,
                    "target_node_id": consumer_id,
                },
            ],
        }
        response = authenticated_client.post(create_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        new_version_id = response.data["result"]["id"]
        version = GraphVersion.no_workspace_objects.get(id=new_version_id)
        edges = Edge.no_workspace_objects.filter(graph_version=version)
        # "data" output display_name matches "data" input display_name → 1 edge
        assert edges.count() == 1


class TestCreateVersionLLMNode:
    """Test create_version with LLM prompt nodes (auto ports + PTN)."""

    def test_llm_node_creates_ports_and_ptn(
        self, authenticated_client, graph, graph_version, llm_node_template
    ):
        """Test that an LLM node with prompt_template creates ports from {{variables}} and PTN."""
        create_url = reverse("graph-versions", kwargs={"pk": str(graph.id)})
        data = {
            "nodes": [
                {
                    "id": str(uuid.uuid4()),
                    "type": NodeType.ATOMIC,
                    "name": "LLM Node",
                    "node_template_id": str(llm_node_template.id),
                    "position": {"x": 100, "y": 200},
                    "prompt_template": {
                        "messages": [
                            {
                                "id": "msg-0",
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Hello {{name}}, summarize {{text}}",
                                    }
                                ],
                            },
                        ],
                        "response_format": "text",
                        "model": "gpt-4o",
                    },
                },
            ],
        }
        response = authenticated_client.post(create_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        nodes = response.data["result"]["nodes"]
        assert len(nodes) == 1

        ports = nodes[0]["ports"]
        port_names = {p["display_name"] for p in ports}
        # Should have input ports for {{name}} and {{text}}, plus output port "response"
        assert "name" in port_names
        assert "text" in port_names
        assert "response" in port_names
        assert len(ports) == 3

        # Should have prompt_template data
        assert nodes[0]["prompt_template"] is not None
        assert nodes[0]["prompt_template"]["prompt_template_id"] is not None


class TestCreateVersionSubgraph:
    """Test create_version with subgraph nodes (input_mappings)."""

    def test_subgraph_creates_input_ports_from_mappings(
        self,
        authenticated_client,
        graph,
        graph_version,
        referenced_graph,
        active_referenced_graph_version,
        dynamic_node_template,
    ):
        """Test that subgraph input_mappings keys become input ports."""
        create_url = reverse("graph-versions", kwargs={"pk": str(graph.id)})
        source_id = str(uuid.uuid4())
        subgraph_id = str(uuid.uuid4())
        data = {
            "nodes": [
                {
                    "id": source_id,
                    "type": NodeType.ATOMIC,
                    "name": "Source",
                    "node_template_id": str(dynamic_node_template.id),
                    "position": {"x": 100, "y": 200},
                },
                {
                    "id": subgraph_id,
                    "type": NodeType.SUBGRAPH,
                    "name": "Summarizer",
                    "ref_graph_version_id": str(active_referenced_graph_version.id),
                    "position": {"x": 400, "y": 200},
                    "ports": [
                        {
                            "id": str(uuid.uuid4()),
                            "key": "custom",
                            "display_name": "summary",
                            "direction": PortDirection.OUTPUT,
                            "data_schema": {"type": "string"},
                        },
                    ],
                    "input_mappings": [
                        {"key": "context", "value": "Source.response"},
                        {"key": "question", "value": None},
                    ],
                },
            ],
            "node_connections": [
                {
                    "source_node_id": source_id,
                    "target_node_id": subgraph_id,
                },
            ],
        }
        response = authenticated_client.post(create_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        nodes = response.data["result"]["nodes"]
        subgraph_node = next(n for n in nodes if n["type"] == NodeType.SUBGRAPH)
        ports = subgraph_node["ports"]
        port_info = {(p["display_name"], p["direction"]) for p in ports}

        # Should have output port "summary" from FE + input ports "context" and "question" from mappings
        assert ("summary", "output") in port_info
        assert ("context", "input") in port_info
        assert ("question", "input") in port_info
        assert len(ports) == 3

    def test_subgraph_null_mapping_creates_no_edge(
        self,
        authenticated_client,
        graph,
        graph_version,
        referenced_graph,
        active_referenced_graph_version,
        dynamic_node_template,
    ):
        """Test that null values in input_mappings create no edge (globally exposed)."""
        create_url = reverse("graph-versions", kwargs={"pk": str(graph.id)})
        source_id = str(uuid.uuid4())
        sub_id = str(uuid.uuid4())
        data = {
            "nodes": [
                {
                    "id": source_id,
                    "type": NodeType.ATOMIC,
                    "name": "Source",
                    "node_template_id": str(dynamic_node_template.id),
                    "position": {"x": 100, "y": 200},
                },
                {
                    "id": sub_id,
                    "type": NodeType.SUBGRAPH,
                    "name": "Sub",
                    "ref_graph_version_id": str(active_referenced_graph_version.id),
                    "position": {"x": 400, "y": 200},
                    "ports": [],
                    "input_mappings": [
                        {"key": "question", "value": None},
                    ],
                },
            ],
            "node_connections": [
                {
                    "source_node_id": source_id,
                    "target_node_id": sub_id,
                },
            ],
        }
        response = authenticated_client.post(create_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        new_version_id = response.data["result"]["id"]
        version = GraphVersion.no_workspace_objects.get(id=new_version_id)
        edges = Edge.no_workspace_objects.filter(graph_version=version)
        # null mapping → no edge
        assert edges.count() == 0


class TestEditExistingGraphWorkflow:
    """
    Test the workflow for editing an existing graph:
    1. Fetch existing graph (with active version)
    2. Create new draft version (via POST with nodes)
    3. Publish via PATCH
    """

    def test_complete_edit_workflow(
        self, authenticated_client, graph, active_graph_version, node_template
    ):
        """Test the complete graph editing workflow."""
        # Step 1: Fetch existing graph
        detail_url = reverse("graph-detail", kwargs={"pk": str(graph.id)})
        response = authenticated_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["result"]["active_version"]["id"] == str(
            active_graph_version.id
        )

        # Step 2: Create new draft version with content
        create_version_url = reverse("graph-versions", kwargs={"pk": str(graph.id)})
        create_data = {
            "status": GraphVersionStatus.DRAFT,
            "nodes": [
                {
                    "id": str(uuid.uuid4()),
                    "type": NodeType.ATOMIC,
                    "name": "Updated Node",
                    "node_template_id": str(node_template.id),
                    "config": {"new_param": "value"},
                    "position": {"x": 100, "y": 100},
                },
            ],
        }
        response = authenticated_client.post(
            create_version_url, data=create_data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        new_version_id = response.data["result"]["id"]
        assert (
            response.data["result"]["version_number"]
            == active_graph_version.version_number + 1
        )
        assert response.data["result"]["status"] == GraphVersionStatus.DRAFT

        # Step 3: Publish via PATCH
        update_url = reverse(
            "graph-version-detail",
            kwargs={"pk": str(graph.id), "version_id": new_version_id},
        )
        publish_data = {
            "status": GraphVersionStatus.ACTIVE,
            "commit_message": "Updated configuration",
        }
        response = authenticated_client.patch(
            update_url, data=publish_data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["result"]["status"] == GraphVersionStatus.ACTIVE

        # Verify old active is now inactive
        active_graph_version.refresh_from_db()
        assert active_graph_version.status == GraphVersionStatus.INACTIVE

        # Verify graph shows new active version
        response = authenticated_client.get(detail_url)
        assert response.data["result"]["active_version"]["id"] == new_version_id


class TestSubgraphWorkflow:
    """Test workflow involving subgraph references."""

    def test_create_graph_with_subgraph_node(
        self,
        authenticated_client,
        graph,
        graph_version,
        referenced_graph,
        active_referenced_graph_version,
        node_template,
    ):
        """Test creating a graph that references another graph as a subgraph."""
        # First, check that referenced_graph is available as referenceable
        referenceable_url = reverse(
            "graph-referenceable-graphs", kwargs={"pk": str(graph.id)}
        )
        response = authenticated_client.get(referenceable_url)

        assert response.status_code == status.HTTP_200_OK
        ref_graphs = response.data["result"]["graphs"]
        ref_graph_ids = [g["id"] for g in ref_graphs]
        assert str(referenced_graph.id) in ref_graph_ids

        # Get the version_id from referenceable response
        ref_graph_data = next(
            g for g in ref_graphs if g["id"] == str(referenced_graph.id)
        )
        # Get the first version (typically active)
        ref_version_id = ref_graph_data["versions"][0]["id"]

        # Create a version with an atomic node and a subgraph node
        create_url = reverse("graph-versions", kwargs={"pk": str(graph.id)})
        input_node_id = str(uuid.uuid4())
        summarizer_id = str(uuid.uuid4())
        create_data = {
            "nodes": [
                {
                    "id": input_node_id,
                    "type": NodeType.ATOMIC,
                    "name": "Input Node",
                    "node_template_id": str(node_template.id),
                    "position": {"x": 100, "y": 200},
                },
                {
                    "id": summarizer_id,
                    "type": NodeType.SUBGRAPH,
                    "name": "Summarizer",
                    "ref_graph_version_id": ref_version_id,
                    "position": {"x": 400, "y": 200},
                    "ports": [
                        {
                            "id": str(uuid.uuid4()),
                            "key": "custom",
                            "display_name": "Text",
                            "direction": PortDirection.OUTPUT,
                        },
                    ],
                    "input_mappings": [],
                },
            ],
            "node_connections": [
                {
                    "source_node_id": input_node_id,
                    "target_node_id": summarizer_id,
                },
            ],
        }
        response = authenticated_client.post(
            create_url, data=create_data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        nodes = response.data["result"]["nodes"]
        assert len(nodes) == 2

        # Find the subgraph node
        subgraph_node = next(n for n in nodes if n["type"] == NodeType.SUBGRAPH)
        assert subgraph_node["ref_graph_version_id"] == ref_version_id


class TestVersionHistory:
    """Test version history and rollback scenarios."""

    def test_version_history_preserved(
        self, authenticated_client, graph, node_template
    ):
        """Test that version history is preserved through multiple saves."""
        # Create v1 with content and publish
        create_url = reverse("graph-versions", kwargs={"pk": str(graph.id)})
        v1_data = {
            "status": GraphVersionStatus.ACTIVE,
            "commit_message": "Version 1",
            "nodes": [
                {
                    "id": str(uuid.uuid4()),
                    "type": NodeType.ATOMIC,
                    "name": "V1 Node",
                    "node_template_id": str(node_template.id),
                },
            ],
        }
        response = authenticated_client.post(create_url, data=v1_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        v1_id = response.data["result"]["id"]

        # Create v2 with content and publish
        v2_data = {
            "status": GraphVersionStatus.ACTIVE,
            "commit_message": "Version 2",
            "nodes": [
                {
                    "id": str(uuid.uuid4()),
                    "type": NodeType.ATOMIC,
                    "name": "V2 Node",
                    "node_template_id": str(node_template.id),
                },
            ],
        }
        response = authenticated_client.post(create_url, data=v2_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        v2_id = response.data["result"]["id"]

        # Verify version history
        versions_url = reverse("graph-versions", kwargs={"pk": str(graph.id)})
        response = authenticated_client.get(versions_url)

        assert response.status_code == status.HTTP_200_OK
        versions = response.data["result"]["versions"]
        assert len(versions) == 2

        # V1 should be inactive
        v1 = GraphVersion.no_workspace_objects.get(id=v1_id)
        assert v1.status == GraphVersionStatus.INACTIVE

        # V2 should be active
        statuses = {v["id"]: v["status"] for v in versions}
        assert statuses[v2_id] == GraphVersionStatus.ACTIVE


class TestCascadeSoftDelete:
    """Test cascade soft-delete functionality."""

    def test_delete_graph_cascades_to_versions(
        self, authenticated_client, graph, graph_version, active_graph_version
    ):
        """Test that deleting a graph soft-deletes all its versions."""
        url = reverse("graph-bulk-delete")
        response = authenticated_client.post(
            url, data={"ids": [str(graph.id)]}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

        # Graph should be soft-deleted
        graph.refresh_from_db()
        assert graph.deleted is True

        # Versions should be soft-deleted
        graph_version.refresh_from_db()
        active_graph_version.refresh_from_db()
        assert graph_version.deleted is True
        assert active_graph_version.deleted is True

    def test_delete_graph_cascades_to_nodes_and_ports(
        self, authenticated_client, graph, graph_version, node, input_port, output_port
    ):
        """Test that deleting a graph soft-deletes nodes and ports."""
        url = reverse("graph-bulk-delete")
        response = authenticated_client.post(
            url, data={"ids": [str(graph.id)]}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

        # Nodes and ports should be soft-deleted
        node.refresh_from_db()
        input_port.refresh_from_db()
        output_port.refresh_from_db()
        assert node.deleted is True
        assert input_port.deleted is True
        assert output_port.deleted is True

    def test_delete_graph_cascades_to_edges(
        self, authenticated_client, graph, graph_version, edge
    ):
        """Test that deleting a graph soft-deletes edges."""
        url = reverse("graph-bulk-delete")
        response = authenticated_client.post(
            url, data={"ids": [str(graph.id)]}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

        edge.refresh_from_db()
        assert edge.deleted is True

    def test_deleted_graph_not_in_list(
        self, authenticated_client, graph, graph_version
    ):
        """Test that deleted graphs don't appear in list."""
        # Delete the graph
        delete_url = reverse("graph-bulk-delete")
        authenticated_client.post(
            delete_url, data={"ids": [str(graph.id)]}, format="json"
        )

        # List should not include deleted graph
        list_url = reverse("graph-list")
        response = authenticated_client.get(list_url)

        assert response.status_code == status.HTTP_200_OK
        graph_ids = [g["id"] for g in response.data["result"]["graphs"]]
        assert str(graph.id) not in graph_ids


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_update_nonexistent_version(self, authenticated_client, graph):
        """Test updating a nonexistent version returns 404."""
        import uuid

        fake_version_id = str(uuid.uuid4())
        update_url = reverse(
            "graph-version-detail",
            kwargs={"pk": str(graph.id), "version_id": fake_version_id},
        )
        response = authenticated_client.patch(
            update_url, data={"commit_message": "x"}, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_version_wrong_graph(
        self, authenticated_client, graph, referenced_graph, referenced_graph_version
    ):
        """Test updating a version that belongs to a different graph."""
        update_url = reverse(
            "graph-version-detail",
            kwargs={
                "pk": str(graph.id),
                "version_id": str(referenced_graph_version.id),
            },
        )
        response = authenticated_client.patch(
            update_url, data={"commit_message": "x"}, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_update_active_version_to_draft(
        self, authenticated_client, graph, active_graph_version
    ):
        """Test that an active version cannot be reverted to draft."""
        update_url = reverse(
            "graph-version-detail",
            kwargs={"pk": str(graph.id), "version_id": str(active_graph_version.id)},
        )
        response = authenticated_client.patch(
            update_url,
            data={"status": GraphVersionStatus.DRAFT},
            format="json",
        )

        # This should fail because active versions can't be modified
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_graph_without_name_fails(self, authenticated_client):
        """Test that creating a graph without a name fails."""
        url = reverse("graph-list")
        response = authenticated_client.post(
            url, data={"description": "No name provided"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestMultiUserScenarios:
    """Test scenarios involving multiple users."""

    def test_user_cannot_access_other_org_graph(
        self, api_client, graph, graph_version, workspace, db
    ):
        """Test that users cannot access graphs from other organizations."""
        from accounts.models.organization import Organization
        from accounts.models.user import User

        # Create a different org and user
        other_org = Organization.objects.create(name="Other Org")
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpassword",
            name="Other User",
            organization=other_org,
        )

        api_client.force_authenticate(user=other_user)
        api_client.set_organization(other_org)

        # Try to access the graph
        url = reverse("graph-detail", kwargs={"pk": str(graph.id)})
        response = api_client.get(url)

        api_client.stop_workspace_injection()

        # Should return 404 (not 403) to avoid leaking existence
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_cannot_modify_other_org_graph(
        self, api_client, graph, graph_version, workspace, db
    ):
        """Test that users cannot modify graphs from other organizations."""
        from accounts.models.organization import Organization
        from accounts.models.user import User

        other_org = Organization.objects.create(name="Another Org")
        other_user = User.objects.create_user(
            email="another@example.com",
            password="testpassword",
            name="Another User",
            organization=other_org,
        )

        api_client.force_authenticate(user=other_user)
        api_client.set_organization(other_org)

        # Try to update the graph
        url = reverse("graph-detail", kwargs={"pk": str(graph.id)})
        response = api_client.patch(url, data={"name": "Hacked Name"}, format="json")

        api_client.stop_workspace_injection()

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestReferenceableGraphsWorkflow:
    """Test the referenceable graphs workflow for subgraph selection."""

    def test_graph_without_active_version_not_referenceable(
        self, authenticated_client, graph, graph_version, referenced_graph
    ):
        """Test that graphs without active versions are not referenceable."""
        url = reverse("graph-referenceable-graphs", kwargs={"pk": str(graph.id)})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        ref_graph_ids = [g["id"] for g in response.data["result"]["graphs"]]
        assert str(referenced_graph.id) not in ref_graph_ids

    def test_graph_with_active_version_is_referenceable(
        self,
        authenticated_client,
        graph,
        graph_version,
        referenced_graph,
        active_referenced_graph_version,
    ):
        """Test that graphs with active versions are referenceable."""
        url = reverse("graph-referenceable-graphs", kwargs={"pk": str(graph.id)})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        ref_graph_ids = [g["id"] for g in response.data["result"]["graphs"]]
        assert str(referenced_graph.id) in ref_graph_ids

    def test_self_not_referenceable(
        self, authenticated_client, graph, active_graph_version
    ):
        """Test that a graph cannot reference itself."""
        url = reverse("graph-referenceable-graphs", kwargs={"pk": str(graph.id)})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        ref_graph_ids = [g["id"] for g in response.data["result"]["graphs"]]
        assert str(graph.id) not in ref_graph_ids

    def test_referenceable_includes_active_version_id(
        self,
        authenticated_client,
        graph,
        graph_version,
        referenced_graph,
        active_referenced_graph_version,
    ):
        """Test that referenceable response includes version information."""
        url = reverse("graph-referenceable-graphs", kwargs={"pk": str(graph.id)})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        ref_graph = next(
            g
            for g in response.data["result"]["graphs"]
            if g["id"] == str(referenced_graph.id)
        )
        # Check versions array contains the active version
        assert "versions" in ref_graph
        assert len(ref_graph["versions"]) >= 1
        version_ids = [v["id"] for v in ref_graph["versions"]]
        assert str(active_referenced_graph_version.id) in version_ids
