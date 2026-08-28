import os

import structlog
from mixpanel import Mixpanel

from accounts.models import User
from tfc.middleware.workspace_context import get_current_organization

logger = structlog.get_logger(__name__)
try:
    from ee.usage.models.usage import OrganizationSubscription
except ImportError:
    OrganizationSubscription = None

# Track if we've already warned about missing token
_token_warning_logged = False


class MixpanelTracker:
    def __init__(self):
        self.token = os.getenv("MIX_PANEL_TOKEN")
        self.mp = Mixpanel(self.token) if self.token else None
        self._check_token()

    def _check_token(self) -> bool:
        """Check if Mixpanel token is configured. Warns once if missing."""
        global _token_warning_logged
        if not self.token:
            if not _token_warning_logged:
                logger.warning(
                    "MIX_PANEL_TOKEN environment variable is not set. "
                    "Mixpanel tracking will be disabled."
                )
                _token_warning_logged = True
            return False
        return True

    def _is_enabled(self) -> bool:
        """Check if Mixpanel is enabled (token is configured)."""
        return self.mp is not None

    def update_org_details(self, org_id, org_name, subscription):
        """Update organization details in Mixpanel"""
        if not self._is_enabled():
            return
        try:
            self.mp.group_set(
                "org_id",
                str(org_id),
                {
                    "Organization Name": org_name,
                    "Subscription Tier": subscription,
                },
            )
        except Exception as e:
            logger.exception(f"Error updating organization details in Mixpanel: {e}")

    def set_details(self, user: User):
        if not self._is_enabled():
            return
        from accounts.utils import get_user_organization

        _org = get_current_organization() or get_user_organization(user)
        if not _org:
            logger.warning(
                "set_details: no organization found for user", user_id=str(user.id)
            )
            return
        if OrganizationSubscription is None:
            # No subscription model when ee is absent.
            subscription = "self-hosted"
        else:
            try:
                subscription = OrganizationSubscription.objects.get(
                    organization=_org
                ).get_subscription_name()
            except OrganizationSubscription.DoesNotExist:
                subscription = "Unknown"
        self.mp.group_set_once(
            "org_id",
            str(_org.id),
            {
                "Organization Name": _org.display_name or _org.name,
                "Subscription Tier": subscription,
            },
        )
        self.mp.people_set_once(
            str(user.id),
            {
                "id": str(user.id),
                "$email": user.email,
                "$name": user.name,
                "org_id": [str(_org.id)],
                "org_name": _org.display_name or _org.name,
            },
        )

    def track_event(self, event_name, properties=None):
        """Send event data to Mixpanel"""
        if not self._is_enabled():
            return
        try:
            properties = properties or {}
            if "org_id" in properties and "org_name" in properties:
                subscription = properties.pop("subscription", None)
                self.mp.group_set_once(
                    "org_id",
                    str(properties.get("org_id")[0]),
                    {
                        "Organization Name": properties.get("org_name"),
                        "Subscription Tier": subscription,
                    },
                )
                self.mp.people_set_once(
                    str(properties.get("$user_id")),
                    {"org_id": properties.get("org_id")},
                )
            user_id = str(properties.get("$user_id", "unknown"))
            self.mp.track(user_id, event_name, properties)
        except Exception as e:
            logger.exception(f"Error tracking Mixpanel event: {e}")


mixpanel_tracker = MixpanelTracker()
