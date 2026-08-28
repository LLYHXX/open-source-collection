from ai_tools.base import BaseTool, EmptyInput, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    format_uuid,
    markdown_table,
    section,
)
from ai_tools.registry import register_tool


@register_tool
class ListOrganizationsTool(BaseTool):
    name = "list_organizations"
    description = (
        "Lists all organizations the current user has access to, including their "
        "primary organization and any organizations they have been invited to."
    )
    category = "users"
    input_model = EmptyInput

    def execute(self, params: EmptyInput, context: ToolContext) -> ToolResult:

        from accounts.models.organization_membership import OrganizationMembership

        user = context.user
        primary_org = user.organization

        rows = []
        data_list = []

        # Primary organization
        if primary_org:
            is_current = str(primary_org.id) == str(context.organization.id)
            current_marker = " (current)" if is_current else ""
            rows.append(
                [
                    format_uuid(primary_org.id),
                    f"{primary_org.display_name or primary_org.name}{current_marker}",
                    user.organization_role or "—",
                    "Primary",
                    format_datetime(primary_org.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(primary_org.id),
                    "name": primary_org.name,
                    "display_name": primary_org.display_name,
                    "role": user.organization_role,
                    "type": "primary",
                    "is_current": is_current,
                }
            )

        # Invited organizations
        invited_memberships = OrganizationMembership.objects.filter(
            user=user, is_active=True
        ).select_related("organization")

        for membership in invited_memberships:
            org = membership.organization
            # Skip if it's the same as primary org
            if primary_org and str(org.id) == str(primary_org.id):
                continue
            is_current = str(org.id) == str(context.organization.id)
            current_marker = " (current)" if is_current else ""
            rows.append(
                [
                    format_uuid(org.id),
                    f"{org.display_name or org.name}{current_marker}",
                    membership.role or "—",
                    "Invited",
                    format_datetime(membership.joined_at),
                ]
            )
            data_list.append(
                {
                    "id": str(org.id),
                    "name": org.name,
                    "display_name": org.display_name,
                    "role": membership.role,
                    "type": "invited",
                    "is_current": is_current,
                }
            )

        table = markdown_table(["ID", "Name", "Role", "Type", "Joined"], rows)
        content = section(f"Organizations ({len(rows)})", table)

        return ToolResult(
            content=content, data={"organizations": data_list, "total": len(data_list)}
        )
