"""Tests for NodeConnectionCrudViewSet — granular node connection endpoints."""

import uuid
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from agent_playground.models.choices import NodeType
from agent_playground.models.node import Node
from agent_playground.models.node_connection import NodeConnection

# ── helpers ────────────────────────────────────────────────────────────


def _nc_create_url(graph, version):
    return reverse(
        "graph-version-nc-create",
        kwargs={"pk": graph.id, "version_id": version.id},
    )


def _nc_delete_url(graph, version, nc_id):
    return reverse(
        "graph-version-nc-delete",
        kwargs={"pk": graph.id, "version_id": version.id, "nc_id": nc_id},
    )


# =====================================================================
# CREATE NODE CONNECTION
# =====================================================================


@pytest.mark.unit
class TestCreateNodeConnectionAPI:
    def test_create_nc(
        self, authenticated_client, graph, graph_version, node, second_node
    ):
        fe_id = str(uuid.uuid4())
        url = _nc_create_url(graph, graph_version)
        payload = {
            "id": fe_id,
            "source_node_id": str(node.id),
            "target_node_id": str(second_node.id),
        }
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] is True
        assert response.data["result"]["id"] == fe_id

    def test_create_nc_self_connection(
        self, authenticated_client, graph, graph_version, node
    ):
        url = _nc_create_url(graph, graph_version)
        payload = {
            "id": str(uuid.uuid4()),
            "source_node_id": str(node.id),
            "target_node_id": str(node.id),
        }
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_nc_rejects_non_draft(
        self,
        authenticated_client,
        graph,
        active_graph_version,
        node_template,
    ):
        # Create two nodes in the active version for the payload
        n1 = Node.no_workspace_objects.create(
            graph_version=active_graph_version,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="N1",
            config={},
        )
        n2 = Node.no_workspace_objects.create(
            graph_version=active_graph_version,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="N2",
            config={},
        )
        url = _nc_create_url(graph, active_graph_version)
        payload = {
            "id": str(uuid.uuid4()),
            "source_node_id": str(n1.id),
            "target_node_id": str(n2.id),
        }
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_nc_node_not_found(
        self, authenticated_client, graph, graph_version, node
    ):
        url = _nc_create_url(graph, graph_version)
        payload = {
            "id": str(uuid.uuid4()),
            "source_node_id": str(node.id),
            "target_node_id": str(uuid.uuid4()),  # does not exist
        }
        response = authenticated_client.post(url, payload, format="json")

        # The NodeConnection model validates that nodes exist and belong
        # to the same version; this will raise an error
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        )


# =====================================================================
# DELETE NODE CONNECTION
# =====================================================================


@pytest.mark.unit
class TestDeleteNodeConnectionAPI:
    def test_delete_nc(
        self,
        authenticated_client,
        graph,
        graph_version,
        node_connection,
    ):
        url = _nc_delete_url(graph, graph_version, node_connection.id)
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["result"]["message"] == "Node connection deleted successfully"
        )

    def test_delete_nc_cascades_edges(
        self,
        authenticated_client,
        graph,
        graph_version,
        node,
        second_node,
        output_port,
        second_node_input_port,
        edge,
        node_connection,
    ):
        url = _nc_delete_url(graph, graph_version, node_connection.id)
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        edge.refresh_from_db()
        assert edge.deleted is True

    def test_delete_nc_rejects_non_draft(
        self,
        authenticated_client,
        graph,
        active_graph_version,
        node_template,
    ):
        n1 = Node.no_workspace_objects.create(
            graph_version=active_graph_version,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="N1",
            config={},
        )
        n2 = Node.no_workspace_objects.create(
            graph_version=active_graph_version,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="N2",
            config={},
        )
        nc = NodeConnection.no_workspace_objects.create(
            graph_version=active_graph_version,
            source_node=n1,
            target_node=n2,
        )
        url = _nc_delete_url(graph, active_graph_version, nc.id)
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_nc_not_found(self, authenticated_client, graph, graph_version):
        fake_id = uuid.uuid4()
        url = _nc_delete_url(graph, graph_version, fake_id)
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


# =====================================================================
# SYNC DATASET COLUMNS SIDE-EFFECT TESTS
# =====================================================================


SYNC_MOCK_PATH = "agent_playground.views.node_connection.sync_dataset_columns"


@pytest.mark.unit
class TestNodeConnectionSyncSideEffects:
    """Verify sync_dataset_columns is called as a side effect of NC CRUD."""

    def test_create_nc_triggers_column_sync(
        self, authenticated_client, graph, graph_version, node, second_node
    ):
        url = _nc_create_url(graph, graph_version)
        payload = {
            "id": str(uuid.uuid4()),
            "source_node_id": str(node.id),
            "target_node_id": str(second_node.id),
        }
        with patch(SYNC_MOCK_PATH) as mock_sync:
            response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        mock_sync.assert_called_once_with(graph, graph_version)

    def test_delete_nc_triggers_column_sync(
        self,
        authenticated_client,
        graph,
        graph_version,
        node_connection,
    ):
        url = _nc_delete_url(graph, graph_version, node_connection.id)
        with patch(SYNC_MOCK_PATH) as mock_sync:
            response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        mock_sync.assert_called_once_with(graph, graph_version)

    def test_create_nc_succeeds_if_sync_fails(
        self, authenticated_client, graph, graph_version, node, second_node
    ):
        url = _nc_create_url(graph, graph_version)
        payload = {
            "id": str(uuid.uuid4()),
            "source_node_id": str(node.id),
            "target_node_id": str(second_node.id),
        }
        with patch(SYNC_MOCK_PATH, side_effect=RuntimeError("sync boom")):
            response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
