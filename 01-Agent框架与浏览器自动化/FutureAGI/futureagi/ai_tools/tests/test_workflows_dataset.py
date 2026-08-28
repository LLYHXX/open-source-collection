import pytest

from ai_tools.tests.conftest import run_tool


@pytest.fixture(autouse=True)
def _resource_limit(mock_resource_limit):
    """All dataset workflows need the resource limit mock."""
    pass


class TestDatasetCRUDWorkflow:
    """Create -> populate -> inspect -> update -> delete workflow."""

    def test_full_lifecycle(self, tool_context):
        # 1. Create dataset (columns is list of strings)
        create = run_tool(
            "create_dataset",
            {"name": "Workflow DS", "columns": ["question", "answer"]},
            tool_context,
        )
        assert not create.is_error
        ds_id = create.data["dataset_id"]

        # 2. Verify it appears in list
        listing = run_tool("list_datasets", {}, tool_context)
        assert not listing.is_error
        assert listing.data["total"] >= 1
        assert any(d["id"] == ds_id for d in listing.data["datasets"])

        # 3. Add rows
        add = run_tool(
            "add_dataset_rows",
            {
                "dataset_id": ds_id,
                "rows": [
                    {"question": "What is AI?", "answer": "Artificial intelligence"},
                    {"question": "What is ML?", "answer": "Machine learning"},
                ],
            },
            tool_context,
        )
        assert not add.is_error
        assert add.data["rows_added"] == 2

        # 4. Get dataset to verify schema
        get = run_tool("get_dataset", {"dataset_id": ds_id}, tool_context)
        assert not get.is_error
        assert get.data["name"] == "Workflow DS"
        assert len(get.data["columns"]) == 2

        # 5. Update name
        update = run_tool(
            "update_dataset",
            {"dataset_id": ds_id, "name": "Renamed DS"},
            tool_context,
        )
        assert not update.is_error
        assert update.data["name"] == "Renamed DS"

        # 6. Delete (takes dataset_ids as list)
        delete = run_tool("delete_dataset", {"dataset_ids": [ds_id]}, tool_context)
        assert not delete.is_error

        # 7. Verify gone from list
        listing2 = run_tool("list_datasets", {}, tool_context)
        assert not any(d["id"] == ds_id for d in listing2.data["datasets"])


class TestDatasetCloneWorkflow:
    """Create -> add rows -> clone -> verify independence."""

    def test_clone_with_data(self, tool_context):
        # 1. Create source
        src = run_tool(
            "create_dataset",
            {"name": "Source DS", "columns": ["input", "output"]},
            tool_context,
        )
        assert not src.is_error
        src_id = src.data["dataset_id"]

        # 2. Add rows to source
        run_tool(
            "add_dataset_rows",
            {"dataset_id": src_id, "rows": [{"input": "hello", "output": "world"}]},
            tool_context,
        )

        # 3. Clone (returns dataset_id)
        clone = run_tool(
            "clone_dataset",
            {"dataset_id": src_id, "new_name": "Cloned DS"},
            tool_context,
        )
        assert not clone.is_error
        clone_id = clone.data["dataset_id"]
        assert clone_id != src_id

        # 4. Verify both exist
        listing = run_tool("list_datasets", {}, tool_context)
        ids = [d["id"] for d in listing.data["datasets"]]
        assert src_id in ids
        assert clone_id in ids

        # 5. Delete source doesn't affect clone
        run_tool("delete_dataset", {"dataset_ids": [src_id]}, tool_context)
        get_clone = run_tool("get_dataset", {"dataset_id": clone_id}, tool_context)
        assert not get_clone.is_error


class TestDatasetColumnWorkflow:
    """Create -> add columns -> delete column."""

    def test_add_and_remove_columns(self, tool_context):
        # 1. Create with initial column
        ds = run_tool(
            "create_dataset",
            {"name": "Col Test DS", "columns": ["base"]},
            tool_context,
        )
        assert not ds.is_error
        ds_id = ds.data["dataset_id"]

        # 2. Add new columns (add_columns takes ColumnDef dicts with name/data_type)
        add = run_tool(
            "add_columns",
            {
                "dataset_id": ds_id,
                "columns": [
                    {"name": "score", "data_type": "float"},
                    {"name": "notes", "data_type": "text"},
                ],
            },
            tool_context,
        )
        assert not add.is_error
        # add_columns returns {"columns": [...]}
        assert len(add.data["columns"]) >= 2

        # 3. Get dataset to see all columns
        get = run_tool("get_dataset", {"dataset_id": ds_id}, tool_context)
        col_names = [c["name"] for c in get.data["columns"]]
        assert "base" in col_names
        assert "score" in col_names
        assert "notes" in col_names

        # 4. Delete one column
        score_col = next(c for c in get.data["columns"] if c["name"] == "score")
        delete = run_tool(
            "delete_column",
            {"dataset_id": ds_id, "column_id": score_col["id"]},
            tool_context,
        )
        assert not delete.is_error

        # 5. Verify column removed
        get2 = run_tool("get_dataset", {"dataset_id": ds_id}, tool_context)
        col_names2 = [c["name"] for c in get2.data["columns"]]
        assert "score" not in col_names2
        assert "base" in col_names2
