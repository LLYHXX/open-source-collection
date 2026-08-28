import pytest

from ai_tools.tests.conftest import run_tool


class TestAnnotationLabelWorkflow:
    """Create labels → list → update → delete."""

    def test_full_lifecycle(self, tool_context):
        # 1. Create a text label
        text = run_tool(
            "create_annotation_label",
            {
                "name": "Feedback",
                "label_type": "text",
                "description": "Free text feedback",
            },
            tool_context,
        )
        assert not text.is_error
        text_id = text.data["label_id"]

        # 2. Create a star label
        star = run_tool(
            "create_annotation_label",
            {
                "name": "Rating",
                "label_type": "star",
                "settings": {"no_of_stars": 5},
            },
            tool_context,
        )
        assert not star.is_error
        star_id = star.data["label_id"]

        # 3. List all labels
        listing = run_tool("list_annotation_labels", {}, tool_context)
        assert not listing.is_error
        assert listing.data["total"] == 2

        # 4. Filter by type
        text_only = run_tool(
            "list_annotation_labels",
            {"label_type": "text"},
            tool_context,
        )
        assert text_only.data["total"] == 1

        star_only = run_tool(
            "list_annotation_labels",
            {"label_type": "star"},
            tool_context,
        )
        assert star_only.data["total"] == 1

        # 5. Update the text label
        update = run_tool(
            "update_annotation_label",
            {
                "label_id": text_id,
                "name": "User Feedback",
                "description": "Updated feedback",
            },
            tool_context,
        )
        assert not update.is_error
        assert len(update.data["changes"]) == 2  # name + description

        # 6. Delete star label
        delete = run_tool(
            "delete_annotation_label",
            {"label_id": star_id},
            tool_context,
        )
        assert not delete.is_error

        # 7. Verify only text label remains
        final = run_tool("list_annotation_labels", {}, tool_context)
        assert final.data["total"] == 1
        assert final.data["labels"][0]["name"] == "User Feedback"

        # 8. Clean up
        run_tool("delete_annotation_label", {"label_id": text_id}, tool_context)


class TestMultiTypeAnnotationLabels:
    """Create one of each label type and verify all appear in listing."""

    def test_create_all_types(self, tool_context):
        type_configs = [
            ("text-label", "text", {}),
            (
                "numeric-label",
                "numeric",
                {"min": 0, "max": 10, "step_size": 1, "display_type": "slider"},
            ),
            (
                "categorical-label",
                "categorical",
                {
                    "options": [{"label": "Good"}, {"label": "Bad"}],
                    "multi_choice": False,
                    "rule_prompt": "",
                    "auto_annotate": False,
                    "strategy": None,
                },
            ),
            ("star-label", "star", {"no_of_stars": 5}),
            ("thumbs-label", "thumbs_up_down", {}),
        ]

        created_ids = []
        for name, label_type, settings in type_configs:
            params = {"name": name, "label_type": label_type}
            if settings:
                params["settings"] = settings
            result = run_tool("create_annotation_label", params, tool_context)
            assert (
                not result.is_error
            ), f"Failed to create {label_type}: {result.content}"
            created_ids.append(result.data["label_id"])

        # Verify all 5 appear
        listing = run_tool("list_annotation_labels", {}, tool_context)
        assert listing.data["total"] == 5

        # Cleanup
        for label_id in created_ids:
            run_tool("delete_annotation_label", {"label_id": label_id}, tool_context)
