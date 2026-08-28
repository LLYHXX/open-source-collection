"""Django signals to bind user/org context to logs."""

import structlog
from django.dispatch import receiver
from django_structlog import signals


@receiver(signals.bind_extra_request_metadata)
def bind_user_and_org_context(request, logger, **kwargs):
    """
    Bind user_id, user_email, organization_id, and workspace_id to all logs.

    This signal fires after django-structlog's RequestMiddleware has already
    bound request_id and ip. We add user/org context here.

    All subsequent logs within this request will automatically include
    these context fields.
    """
    # User context
    if hasattr(request, "user") and request.user.is_authenticated:
        structlog.contextvars.bind_contextvars(
            user_id=str(request.user.id),
        )

        # Add email if available
        if hasattr(request.user, "email") and request.user.email:
            structlog.contextvars.bind_contextvars(
                user_email=request.user.email,
            )

        # Organization context (prefer request.organization from auth middleware)
        org = getattr(request, "organization", None) or getattr(
            request.user, "organization", None
        )
        if org:
            structlog.contextvars.bind_contextvars(
                organization_id=str(org.id),
            )

    # Workspace context (from header)
    workspace_id = request.headers.get("X-Workspace-Id")
    if workspace_id:
        structlog.contextvars.bind_contextvars(workspace_id=workspace_id)
