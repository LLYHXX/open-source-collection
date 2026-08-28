from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import key_value_block, section
from ai_tools.registry import register_tool


class GetUserPermissionsInput(PydanticBaseModel):
    user_id: Optional[UUID] = Field(
        default=None,
        description="UUID of the user to check. Defaults to the current user.",
    )
    workspace_id: Optional[UUID] = Field(
        default=None,
        description="Workspace UUID to check permissions for. Defaults to the current workspace.",
    )


@register_tool
class GetUserPermissionsTool(BaseTool):
    name = "get_user_permissions"
    description = (
        "Checks a user's permissions for a specific workspace. Shows whether they "
        "can read, write, and their workspace role. Defaults to the current user "
        "and current workspace if not specified."
    )
    category = "users"
    input_model = GetUserPermissionsInput

    def execute(
        self, params: GetUserPermissionsInput, context: ToolContext
    ) -> ToolResult:

        from accounts.models.user import User
        from accounts.models.workspace import Workspace

        org = context.organization

        # Determine target user
        if params.user_id:
            try:
                target_user = User.objects.get(id=params.user_id, organization=org)
            except User.DoesNotExist:
                return ToolResult.not_found("User", str(params.user_id))
        else:
            target_user = context.user

        # Determine target workspace
        if params.workspace_id:
            try:
                workspace = Workspace.objects.get(
                    id=params.workspace_id,
                    organization=org,
                    is_active=True,
                )
            except Workspace.DoesNotExist:
                return ToolResult.not_found("Workspace", str(params.workspace_id))
        else:
            workspace = context.workspace

        # Check permissions
        can_access = target_user.can_access_workspace(workspace)
        can_read = target_user.can_read_from_workspace(workspace)
        can_write = target_user.can_write_to_workspace(workspace)
        workspace_role = target_user.get_workspace_role(workspace)
        org_role = target_user.get_organization_role(org)
        has_global_access = target_user.has_global_workspace_access(org)

        info = key_value_block(
            [
                ("User", f"{target_user.name} ({target_user.email})"),
                ("Organization Role", org_role or "—"),
                ("Workspace", f"{workspace.name} (`{workspace.id}`)"),
                ("Workspace Role", workspace_role or "—"),
                ("Global Workspace Access", "Yes" if has_global_access else "No"),
                ("Can Access Workspace", "Yes" if can_access else "No"),
                ("Can Read", "Yes" if can_read else "No"),
                ("Can Write", "Yes" if can_write else "No"),
            ]
        )

        content = section("User Permissions", info)

        return ToolResult(
            content=content,
            data={
                "user_id": str(target_user.id),
                "user_email": target_user.email,
                "workspace_id": str(workspace.id),
                "workspace_name": workspace.name,
                "organization_role": org_role,
                "workspace_role": workspace_role,
                "has_global_access": has_global_access,
                "can_access": can_access,
                "can_read": can_read,
                "can_write": can_write,
            },
        )
