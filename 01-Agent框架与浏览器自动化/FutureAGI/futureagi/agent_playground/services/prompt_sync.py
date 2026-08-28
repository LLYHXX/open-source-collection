"""
Service for syncing agent playground nodes when prompt templates change.

Called by Django signals from model_hub when PromptVersion updates occur.
"""

import structlog
from django.db import transaction

logger = structlog.get_logger(__name__)


def sync_nodes_for_prompt_version(prompt_version) -> None:
    """
    Sync all agent playground nodes linked to a PromptVersion.

    When a PromptVersion's variables or response_format changes:
    1. Find all PromptTemplateNode records referencing this version
    2. For each linked node:
       - Extract variables from prompt_config_snapshot messages
       - Reconcile input ports (add/remove based on variables)
       - Update output port schema (based on response_format)
       - Sync dataset columns for the node's graph

    Args:
        prompt_version: The PromptVersion that changed
    """
    from agent_playground.models.prompt_template_node import PromptTemplateNode

    # Find all nodes using this prompt version
    ptn_records = (
        PromptTemplateNode.no_workspace_objects.select_related(
            "node",
            "node__graph_version",
            "node__graph_version__graph",
        )
        .filter(
            prompt_version=prompt_version,
            deleted=False,
        )
        .all()
    )

    if not ptn_records:
        logger.info(
            "no_nodes_to_sync",
            prompt_version_id=str(prompt_version.id),
        )
        return

    synced_count = 0
    failed_count = 0

    for ptn in ptn_records:
        try:
            _sync_single_node(ptn, prompt_version)
            synced_count += 1
        except Exception as e:
            failed_count += 1
            logger.error(
                "node_sync_failed",
                node_id=str(ptn.node.id),
                prompt_version_id=str(prompt_version.id),
                error=str(e),
                exc_info=True,
            )

    logger.info(
        "sync_completed",
        prompt_version_id=str(prompt_version.id),
        synced=synced_count,
        failed=failed_count,
    )


def _sync_single_node(ptn, prompt_version) -> None:
    """
    Sync a single node's ports and dataset based on prompt changes.

    Args:
        ptn: PromptTemplateNode record
        prompt_version: The updated PromptVersion
    """
    from agent_playground.services.dataset_bridge import sync_dataset_columns
    from agent_playground.services.node_crud import _reconcile_prompt_ports

    node = ptn.node
    version = node.graph_version
    graph = version.graph

    # Build prompt_data dict from prompt_config_snapshot
    config_snapshot = prompt_version.prompt_config_snapshot or {}
    messages = config_snapshot.get("messages", [])
    configuration = config_snapshot.get("configuration", {})

    prompt_data = {
        "messages": messages,
        "response_format": configuration.get("response_format"),
        "response_schema": configuration.get("response_schema"),
    }

    with transaction.atomic():
        # Reconcile ports (add/remove based on variables, update output schema)
        _reconcile_prompt_ports(node, prompt_data)

        # Sync dataset columns to match new exposed ports
        sync_dataset_columns(graph, version)

    logger.info(
        "node_synced",
        node_id=str(node.id),
        node_name=node.name,
        graph_version_id=str(version.id),
        prompt_version_id=str(prompt_version.id),
    )
