from ai_tools.base import BaseTool, EmptyInput, ToolContext, ToolResult
from ai_tools.formatting import key_value_block, section
from ai_tools.registry import register_tool


@register_tool
class WhoamiTool(BaseTool):
    name = "whoami"
    description = (
        "Returns the current authenticated user, organization, workspace, "
        "and subscription information. Use this to understand who you are "
        "acting as and what resources are available."
    )
    category = "context"
    input_model = EmptyInput

    def execute(self, params: EmptyInput, context: ToolContext) -> ToolResult:
        user = context.user
        org = context.organization
        workspace = context.workspace

        # Get subscription info
        subscription_info = self._get_subscription(org)

        # Get workspace count
        from accounts.models.workspace import Workspace

        workspace_count = Workspace.objects.filter(
            organization=org, is_active=True, deleted=False
        ).count()

        info = key_value_block(
            [
                ("User", f"{user.name} ({user.email})"),
                ("Role", getattr(user, "organization_role", "—")),
                ("Organization", f"{org.name} (`{org.id}`)"),
                ("Workspace", f"{workspace.name} (`{workspace.id}`)"),
                ("Subscription", subscription_info.get("tier", "—")),
                ("Status", subscription_info.get("status", "—")),
                (
                    "Wallet Balance",
                    (
                        f"${subscription_info['balance']}"
                        if subscription_info.get("balance") is not None
                        else None
                    ),
                ),
                ("Available Workspaces", str(workspace_count)),
            ]
        )

        content = section("Current Context", info)

        return ToolResult(
            content=content,
            data={
                "user_id": str(user.id),
                "user_email": user.email,
                "user_name": user.name,
                "organization_id": str(org.id),
                "organization_name": org.name,
                "workspace_id": str(workspace.id),
                "workspace_name": workspace.name,
                "subscription_tier": subscription_info.get("tier"),
                "wallet_balance": subscription_info.get("balance"),
            },
        )

    def _get_subscription(self, org) -> dict:
        # No subscription model when ee is absent.
        try:
            from ee.usage.models.usage import OrganizationSubscription
        except ImportError:
            return {"tier": "self-hosted", "status": "self-hosted", "balance": None}

        try:
            sub = OrganizationSubscription.objects.select_related(
                "subscription_tier"
            ).get(organization=org)
            return {
                "tier": sub.subscription_tier.name if sub.subscription_tier else "—",
                "status": sub.status,
                "balance": float(sub.wallet_balance) if sub.wallet_balance else 0,
            }
        except Exception:
            return {"tier": "Unknown", "status": "Unknown", "balance": None}
