import requests
import structlog
from django.conf import settings

from accounts.models import OrgApiKey

logger = structlog.get_logger(__name__)


# Function to send message to websocket to avoid RunTimeError
def call_websocket(organization_id, message, send_to_uuid=False, uuid=None):
    url = settings.WEBSOCKET_ENDPOINT
    payload = {
        "organization_id": str(organization_id),
        "message": message,
        "send_to_uuid": send_to_uuid,
        "uuid": uuid,
    }
    try:
        org_key = OrgApiKey.no_workspace_objects.get(
            organization__id=organization_id, type="system", enabled=True
        )
    except OrgApiKey.DoesNotExist:
        logger.exception(
            f"No API key found for organization {organization_id}, creating one"
        )
        org_key = OrgApiKey.no_workspace_objects.create(
            organization_id=organization_id, type="system"
        )
        if not org_key.api_key or not org_key.secret_key:
            logger.exception(
                f"Failed to generate API keys for organization {organization_id}"
            )
            return {"status": "error", "message": "Failed to generate API keys"}
        # return {"status": "error", "message": "Organization API key not found"}
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=60,
            headers={
                "X-Api-Key": org_key.api_key,
                "X-Secret-Key": org_key.secret_key,
            },
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.JSONDecodeError as e:
        logger.exception(f"Invalid JSON response from websocket: {str(e)}")
        return {"status": "error", "message": "Invalid response format"}
    except requests.exceptions.RequestException as e:
        logger.exception(f"Request error calling websocket: {str(e)}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.exception(f"Error sending message to Websocket: {str(e)}")
        return {"status": "error", "message": str(e)}
