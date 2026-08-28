"""
Audit infrastructure for RBAC changes.

- AuditMiddleware: stores request.user in thread-local so model-level
  code can resolve the actor without passing request around.
- get_current_actor(): reads from thread-local.
- log_audit(): convenience function to create AuditLog entries.
- mute_audit_signals(): context manager to suppress audit logging in bulk ops.
"""

import logging
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_thread_locals = threading.local()


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class AuditMiddleware:
    """
    Stores request.user in thread-local storage so signals and model
    save() methods can access the current actor without needing the request.
    Must be placed after AuthenticationMiddleware in MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.current_user = getattr(request, "user", None)
        _thread_locals.audit_muted = False
        try:
            return self.get_response(request)
        finally:
            _thread_locals.current_user = None
            _thread_locals.audit_muted = False


# ---------------------------------------------------------------------------
# Thread-local accessors
# ---------------------------------------------------------------------------


def get_current_actor():
    """Return the current request user, or None if outside request context."""
    user = getattr(_thread_locals, "current_user", None)
    if user and hasattr(user, "is_authenticated") and user.is_authenticated:
        return user
    return None


def is_audit_muted():
    return getattr(_thread_locals, "audit_muted", False)


@contextmanager
def mute_audit_signals():
    """
    Context manager to suppress audit logging — useful for data migrations
    and bulk operations where per-row audit entries are not needed.

    Usage:
        with mute_audit_signals():
            OrganizationMembership.objects.bulk_create(...)
    """
    prev = getattr(_thread_locals, "audit_muted", False)
    _thread_locals.audit_muted = True
    try:
        yield
    finally:
        _thread_locals.audit_muted = prev


# ---------------------------------------------------------------------------
# Convenience logger
# ---------------------------------------------------------------------------


def log_audit(
    *, organization, action, scope, target_id, changes=None, metadata=None, actor=None
):
    """
    Create an AuditLog entry.

    If `actor` is not supplied, falls back to the thread-local current user.
    Import AuditLog lazily to avoid circular imports.
    """
    if is_audit_muted():
        return None

    from accounts.models.audit_log import AuditLog

    if actor is None:
        actor = get_current_actor()

    try:
        return AuditLog.objects.create(
            organization=organization,
            actor=actor,
            action=action,
            scope=scope,
            target_id=target_id,
            changes=changes or {},
            metadata=metadata or {},
        )
    except Exception:
        logger.exception("Failed to write audit log entry (action=%s)", action)
        return None
