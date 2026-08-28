from ai_tools.base import BaseTool, EmptyInput, ToolContext, ToolResult
from ai_tools.formatting import format_datetime, key_value_block, section
from ai_tools.registry import register_tool


@register_tool
class GetOrganizationTool(BaseTool):
    name = "get_organization"
    description = (
        "Gets details about the current organization, including name, "
        "member count, workspace count, and creation date."
    )
    category = "users"
    input_model = EmptyInput

    def execute(self, params: EmptyInput, context: ToolContext) -> ToolResult:

        from accounts.models.user import User
        from accounts.models.workspace import Workspace

        org = context.organization

        # Count members
        member_count = User.objects.filter(organization=org, is_active=True).count()
        total_member_count = User.objects.filter(organization=org).count()

        # Count workspaces
        workspace_count = Workspace.objects.filter(
            organization=org, is_active=True, deleted=False
        ).count()

        info = key_value_block(
            [
                ("Organization ID", f"`{org.id}`"),
                ("Name", org.name),
                ("Display Name", org.display_name or "—"),
                ("Active Members", str(member_count)),
                ("Total Members", str(total_member_count)),
                ("Workspaces", str(workspace_count)),
                ("Workspaces Enabled", "Yes" if org.ws_enabled else "No"),
                ("Created", format_datetime(org.created_at)),
            ]
        )

        content = section("Organization Details", info)

        return ToolResult(
            content=content,
            data={
                "organization_id": str(org.id),
                "name": org.name,
                "display_name": org.display_name,
                "active_members": member_count,
                "total_members": total_member_count,
                "workspace_count": workspace_count,
                "ws_enabled": org.ws_enabled,
            },
        )
