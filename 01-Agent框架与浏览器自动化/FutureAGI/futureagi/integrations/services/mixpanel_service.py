import base64
import logging
import time
from typing import Any, Optional

import requests

from integrations.services.base import BaseIntegrationService, register_service

logger = logging.getLogger(__name__)


class MixpanelService(BaseIntegrationService):
    """Mixpanel API client for exporting Agentcc LLM usage events.

    Credentials dict shape:
        project_token (str): Mixpanel project token (required)
        api_secret (str): Mixpanel API secret (optional, enables /import endpoint)
    """

    TIMEOUT = 15
    TRACK_URL = "https://api.mixpanel.com/track"
    IMPORT_URL = "https://api.mixpanel.com/import"

    def validate_credentials(
        self,
        host_url: str,
        credentials: dict,
        ca_certificate: Optional[str] = None,
    ) -> dict:
        try:
            project_token = credentials.get("project_token", "")
            if not project_token:
                return {"valid": False, "error": "Project token is required."}

            # Send a test event via /track
            payload = [
                {
                    "event": "$agentcc_connection_test",
                    "properties": {
                        "token": project_token,
                        "distinct_id": "agentcc_test",
                        "time": int(time.time()),
                    },
                }
            ]

            resp = requests.post(
                self.TRACK_URL,
                json=payload,
                timeout=self.TIMEOUT,
            )

            # Mixpanel /track returns "1" on success, "0" on failure
            if resp.status_code == 200 and resp.text.strip() == "1":
                return {
                    "valid": True,
                    "projects": [],
                    "total_traces": 0,
                }

            if resp.status_code == 200 and resp.text.strip() == "0":
                return {
                    "valid": False,
                    "error": "Invalid project token. Please check your Mixpanel project token.",
                }

            return {
                "valid": False,
                "error": f"Unexpected response from Mixpanel (HTTP {resp.status_code}).",
            }

        except requests.exceptions.ConnectionError:
            return {
                "valid": False,
                "error": "Could not reach Mixpanel API. Check your network.",
            }
        except requests.exceptions.Timeout:
            return {
                "valid": False,
                "error": "Connection to Mixpanel timed out. Please try again.",
            }
        except Exception as e:
            logger.exception("Unexpected error validating Mixpanel credentials")
            return {"valid": False, "error": f"Validation failed: {str(e)}"}

    def fetch_traces(
        self,
        host_url: str,
        credentials: dict,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        ca_certificate: Optional[str] = None,
    ) -> dict:
        """Not used — Mixpanel is an export target, not a trace source."""
        return {"traces": [], "has_more": False, "next_page": 1, "total_items": 0}

    def fetch_trace_detail(
        self,
        host_url: str,
        credentials: dict,
        trace_id: str,
        ca_certificate: Optional[str] = None,
    ) -> dict[str, Any]:
        """Not used — Mixpanel is an export target, not a trace source."""
        return {}

    # --- Export methods (called by sync tasks) ---

    def export_events(self, credentials: dict, events: list[dict]) -> dict:
        """Send events to Mixpanel.

        Uses /import (with Basic auth) if api_secret is provided,
        otherwise falls back to /track (with project_token in each event).

        Args:
            credentials: Mixpanel credentials with project_token and optional api_secret.
            events: List of event dicts with: event, properties, timestamp, distinct_id.

        Returns:
            dict with count of events sent.
        """
        if not events:
            return {"sent": 0}

        project_token = credentials.get("project_token", "")
        api_secret = credentials.get("api_secret", "")

        batch = []
        for event in events:
            batch.append(
                {
                    "event": event.get("event", "agentcc_request"),
                    "properties": {
                        "token": project_token,
                        "distinct_id": event.get("distinct_id", "agentcc-gateway"),
                        "time": event.get("time", int(time.time())),
                        **event.get("properties", {}),
                    },
                }
            )

        if api_secret:
            # Use /import with Basic auth for historical data
            auth_str = base64.b64encode(f"{api_secret}:".encode()).decode()
            resp = requests.post(
                self.IMPORT_URL,
                json=batch,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {auth_str}",
                },
                timeout=self.TIMEOUT,
            )
        else:
            # Use /track with token embedded in each event
            resp = requests.post(
                self.TRACK_URL,
                json=batch,
                timeout=self.TIMEOUT,
            )

        resp.raise_for_status()
        return {"sent": len(batch)}


# Self-register on module import
_mixpanel_service = MixpanelService()
register_service("mixpanel", _mixpanel_service)
