import pytest

from ai_tools.tests.conftest import run_tool


class TestUserExplorationWorkflow:
    """Get org → list users → get specific user → check permissions."""

    def test_explore_org_and_users(self, tool_context):
        # 1. Get org details
        org = run_tool("get_organization", {}, tool_context)
        assert not org.is_error
        org_id = org.data["organization_id"]
        assert org.data["active_members"] >= 1

        # 2. List users in org
        users = run_tool("list_users", {}, tool_context)
        assert not users.is_error
        assert users.data["total"] >= 1

        # 3. Get the first user's details
        first_user_id = users.data["users"][0]["id"]
        user = run_tool("get_user", {"user_id": first_user_id}, tool_context)
        assert not user.is_error
        assert user.data["user"]["id"] == first_user_id

        # 4. Check current user's permissions
        perms = run_tool("get_user_permissions", {}, tool_context)
        assert not perms.is_error

        # 5. List workspace members
        ws_members = run_tool("list_workspace_members", {}, tool_context)
        assert not ws_members.is_error
        assert ws_members.data["workspace_id"] == str(tool_context.workspace.id)

        # 6. Search for the test user by email
        search = run_tool(
            "list_users",
            {"search": tool_context.user.email},
            tool_context,
        )
        assert not search.is_error
        assert search.data["total"] >= 1


class TestUserFilterWorkflow:
    """Test various filter combinations on user listing."""

    def test_filter_active_users(self, tool_context):
        # 1. List all active users
        active = run_tool("list_users", {"status": "active"}, tool_context)
        assert not active.is_error
        all_active = active.data["total"]

        # 2. List all inactive users
        inactive = run_tool("list_users", {"status": "inactive"}, tool_context)
        assert not inactive.is_error

        # 3. List all users (no filter)
        all_users = run_tool("list_users", {}, tool_context)
        assert not all_users.is_error

        # Active + inactive should equal total
        assert active.data["total"] + inactive.data["total"] == all_users.data["total"]
