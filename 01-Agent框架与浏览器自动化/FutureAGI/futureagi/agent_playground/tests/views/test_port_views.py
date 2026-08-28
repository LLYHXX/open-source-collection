"""Tests for PortCrudViewSet — granular port endpoints."""

import uuid
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from agent_playground.models.choices import PortDirection
from agent_playground.models.port import Port

# ── helpers ────────────────────────────────────────────────────────────


def _port_update_url(graph, version, port_id):
    return reverse(
        "graph-version-port-update",
        kwargs={"pk": graph.id, "version_id": version.id, "port_id": port_id},
    )


# =====================================================================
# UPDATE PORT
# =====================================================================


@pytest.mark.unit
class TestUpdatePortAPI:
    def test_update_display_name(
        self, authenticated_client, graph, graph_version, node, input_port
    ):
        url = _port_update_url(graph, graph_version, input_port.id)
        response = authenticated_client.patch(
            url, {"display_name": "renamed_port"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["result"]["display_name"] == "renamed_port"

    def test_update_port_rejects_non_draft(
        self,
        authenticated_client,
        graph,
        active_graph_version,
        node_in_active_version,
    ):
        port = Port.no_workspace_objects.create(
            node=node_in_active_version,
            key="input1",
            display_name="input1",
            direction=PortDirection.INPUT,
            data_schema={"type": "string"},
        )
        url = _port_update_url(graph, active_graph_version, port.id)
        response = authenticated_client.patch(
            url, {"display_name": "fail"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_port_not_found(self, authenticated_client, graph, graph_version):
        fake_id = uuid.uuid4()
        url = _port_update_url(graph, graph_version, fake_id)
        response = authenticated_client.patch(url, {"display_name": "x"}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_port_duplicate_display_name(
        self,
        authenticated_client,
        graph,
        graph_version,
        node,
        input_port,
        output_port,
    ):
        # Try renaming output_port to input_port's display_name
        # This may or may not trigger IntegrityError depending on DB constraints.
        # The endpoint should handle it gracefully either way.
        url = _port_update_url(graph, graph_version, output_port.id)
        response = authenticated_client.patch(
            url, {"display_name": input_port.display_name}, format="json"
        )
        # If there's a unique constraint on (node, display_name, direction),
        # this should be 400. If not, it's 200.
        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
        )


# =====================================================================
# SYNC DATASET COLUMNS SIDE-EFFECT TESTS
# =====================================================================


SYNC_MOCK_PATH = "agent_playground.views.port.sync_dataset_columns"


@pytest.mark.unit
class TestPortSyncSideEffects:
    """Verify sync_dataset_columns is called as a side effect of port update."""

    def test_update_port_triggers_column_sync(
        self, authenticated_client, graph, graph_version, node, input_port
    ):
        url = _port_update_url(graph, graph_version, input_port.id)
        with patch(SYNC_MOCK_PATH) as mock_sync:
            response = authenticated_client.patch(
                url, {"display_name": "renamed_sync"}, format="json"
            )

        assert response.status_code == status.HTTP_200_OK
        mock_sync.assert_called_once_with(graph, graph_version)

    def test_update_port_succeeds_if_sync_fails(
        self, authenticated_client, graph, graph_version, node, input_port
    ):
        url = _port_update_url(graph, graph_version, input_port.id)
        with patch(SYNC_MOCK_PATH, side_effect=RuntimeError("sync boom")):
            response = authenticated_client.patch(
                url, {"display_name": "still_works"}, format="json"
            )

        assert response.status_code == status.HTTP_200_OK
