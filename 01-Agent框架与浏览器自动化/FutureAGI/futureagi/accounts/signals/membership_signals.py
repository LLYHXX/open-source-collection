"""
Django signals for membership lifecycle events.

- OrganizationMembership deletion: clears Redis cache, logs audit.
- WorkspaceMembership deletion: logs audit.

Registered in accounts/apps.py ready().
"""

import structlog
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from tfc.utils.audit import get_current_actor, is_audit_muted, log_audit

logger = structlog.get_logger(__name__)


@receiver(pre_delete, sender="accounts.OrganizationMembership")
def org_membership_pre_delete(sender, instance, **kwargs):
    """
    Before deleting an org membership, reset the user's current workspace
    if it belongs to this organization — prevents 404s after removal.
    """
    try:
        user = instance.user
        if (
            hasattr(user, "current_workspace")
            and user.current_workspace
            and user.current_workspace.organization_id == instance.organization_id
        ):
            user.current_workspace = None
            user.save(update_fields=["current_workspace"])
    except Exception:
        logger.exception("Error in org_membership_pre_delete signal")


@receiver(post_delete, sender="accounts.OrganizationMembership")
def org_membership_post_delete(sender, instance, **kwargs):
    """
    After deleting an org membership:
    1. Clear Redis cache (immediate session invalidation).
    2. Create audit log entry.
    """
    # 1. Clear Redis cache
    try:
        from accounts.views.workspace_management import clear_user_redis_cache

        clear_user_redis_cache(instance.user_id)
    except Exception:
        logger.exception("Error clearing Redis cache in org_membership_post_delete")

    # 2. Audit log
    if not is_audit_muted():
        try:
            log_audit(
                organization=instance.organization,
                action="member.removed",
                scope="organization",
                target_id=instance.user_id,
                changes={
                    "role": instance.role,
                    "level": instance.level,
                },
                actor=get_current_actor(),
            )
        except Exception:
            logger.exception("Error creating audit log in org_membership_post_delete")


@receiver(post_delete, sender="accounts.WorkspaceMembership")
def ws_membership_post_delete(sender, instance, **kwargs):
    """
    After deleting a workspace membership, create audit log entry.
    Redis cache clearing is handled by the org membership signal
    (since ws memberships CASCADE from org memberships).
    """
    if not is_audit_muted():
        try:
            log_audit(
                organization=instance.workspace.organization,
                action="member.removed",
                scope="workspace",
                target_id=instance.user_id,
                changes={
                    "workspace_id": str(instance.workspace_id),
                    "role": instance.role,
                    "level": instance.level,
                },
                actor=get_current_actor(),
            )
        except Exception:
            logger.exception("Error creating audit log in ws_membership_post_delete")
