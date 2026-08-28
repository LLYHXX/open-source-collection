import gzip
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from integrations.services.base import BaseIntegrationService, register_service

logger = logging.getLogger(__name__)

# Sub-platform constants
S3 = "s3"
AZURE_BLOB = "azure_blob"
GCS = "gcs"


class CloudStorageService(BaseIntegrationService):
    """Cloud object storage client for log archival (S3, Azure Blob, GCS).

    Credentials dict shape varies by sub_platform:
        S3:
            sub_platform: "s3"
            bucket (str): S3 bucket name
            region (str): AWS region
            access_key_id (str): AWS access key
            secret_access_key (str): AWS secret key
            prefix (str): optional key prefix
            role_arn (str): optional IAM role ARN for assume-role
        Azure Blob:
            sub_platform: "azure_blob"
            storage_account (str): Azure storage account name
            container (str): Container name
            connection_string (str): Azure storage connection string
            prefix (str): optional blob prefix
        GCS:
            sub_platform: "gcs"
            bucket (str): GCS bucket name
            service_account_json (str): JSON string of service account key
            prefix (str): optional object prefix
    """

    TIMEOUT = 30

    def validate_credentials(
        self,
        host_url: str,
        credentials: dict,
        ca_certificate: Optional[str] = None,
    ) -> dict:
        sub_platform = credentials.get("sub_platform", "")
        if not sub_platform:
            return {
                "valid": False,
                "error": "Storage type is required (s3, azure_blob, or gcs).",
            }

        try:
            if sub_platform == S3:
                return self._validate_s3(credentials)
            elif sub_platform == AZURE_BLOB:
                return self._validate_azure(credentials)
            elif sub_platform == GCS:
                return self._validate_gcs(credentials)
            else:
                return {
                    "valid": False,
                    "error": f"Unknown storage type: {sub_platform}",
                }
        except Exception as e:
            logger.exception("Error validating cloud storage credentials")
            return {"valid": False, "error": f"Validation failed: {str(e)}"}

    def _validate_s3(self, credentials: dict) -> dict:
        bucket = credentials.get("bucket", "")
        region = credentials.get("region", "us-east-1")
        access_key = credentials.get("access_key_id", "")
        secret_key = credentials.get("secret_access_key", "")

        if not bucket:
            return {"valid": False, "error": "S3 bucket name is required."}
        if not access_key or not secret_key:
            return {
                "valid": False,
                "error": "AWS access key and secret key are required.",
            }

        try:
            import boto3
            from botocore.exceptions import ClientError

            client = boto3.client(
                "s3",
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )

            # Test write → read → delete
            test_key = (
                f"{credentials.get('prefix', '').strip('/')}/_agentcc_test.txt".lstrip(
                    "/"
                )
            )
            client.put_object(Bucket=bucket, Key=test_key, Body=b"ok")
            client.delete_object(Bucket=bucket, Key=test_key)

            return {"valid": True, "projects": [], "total_traces": 0}

        except ClientError as e:
            code = e.response["Error"]["Code"]
            msg = e.response["Error"]["Message"]
            return {"valid": False, "error": f"S3 error ({code}): {msg}"}
        except ImportError:
            return {"valid": False, "error": "boto3 is not installed on the server."}

    def _validate_azure(self, credentials: dict) -> dict:
        container = credentials.get("container", "")
        conn_str = credentials.get("connection_string", "")

        if not container:
            return {"valid": False, "error": "Azure container name is required."}
        if not conn_str:
            return {"valid": False, "error": "Azure connection string is required."}

        try:
            from azure.storage.blob import BlobServiceClient

            client = BlobServiceClient.from_connection_string(conn_str)
            container_client = client.get_container_client(container)

            test_blob = (
                f"{credentials.get('prefix', '').strip('/')}/_agentcc_test.txt".lstrip(
                    "/"
                )
            )
            container_client.upload_blob(test_blob, b"ok", overwrite=True)
            container_client.delete_blob(test_blob)

            return {"valid": True, "projects": [], "total_traces": 0}

        except ImportError:
            return {
                "valid": False,
                "error": "azure-storage-blob is not installed on the server.",
            }
        except Exception as e:
            return {"valid": False, "error": f"Azure error: {str(e)}"}

    def _validate_gcs(self, credentials: dict) -> dict:
        bucket_name = credentials.get("bucket", "")
        sa_json = credentials.get("service_account_json", "")

        if not bucket_name:
            return {"valid": False, "error": "GCS bucket name is required."}
        if not sa_json:
            return {"valid": False, "error": "Service account JSON is required."}

        try:
            from google.cloud import storage
            from google.oauth2 import service_account

            info = json.loads(sa_json)
            creds = service_account.Credentials.from_service_account_info(info)
            client = storage.Client(credentials=creds)
            bucket = client.bucket(bucket_name)

            test_blob = bucket.blob(
                f"{credentials.get('prefix', '').strip('/')}/_agentcc_test.txt".lstrip(
                    "/"
                )
            )
            test_blob.upload_from_string("ok")
            test_blob.delete()

            return {"valid": True, "projects": [], "total_traces": 0}

        except ImportError:
            return {
                "valid": False,
                "error": "google-cloud-storage is not installed on the server.",
            }
        except json.JSONDecodeError:
            return {"valid": False, "error": "Invalid service account JSON."}
        except Exception as e:
            return {"valid": False, "error": f"GCS error: {str(e)}"}

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
        """Not used — Cloud storage is an export target."""
        return {"traces": [], "has_more": False, "next_page": 1, "total_items": 0}

    def fetch_trace_detail(
        self,
        host_url: str,
        credentials: dict,
        trace_id: str,
        ca_certificate: Optional[str] = None,
    ) -> dict[str, Any]:
        """Not used — Cloud storage is an export target."""
        return {}

    # --- Export method (called by sync tasks) ---

    def export_logs(
        self, credentials: dict, logs: list[dict], config: dict | None = None
    ) -> dict:
        """Export logs to cloud object storage.

        Args:
            credentials: Storage credentials with sub_platform key.
            logs: List of log dicts to export.
            config: Export configuration (format, compression, etc.)

        Returns:
            dict with count of logs exported and object path.
        """
        if not logs:
            return {"sent": 0}

        config = config or {}
        sub_platform = credentials.get("sub_platform", "")
        prefix = credentials.get("prefix", "").strip("/")
        now = datetime.now(timezone.utc)
        partition = f"{prefix}/logs/{now.strftime('%Y/%m/%d')}/hour={now.strftime('%H')}".lstrip(
            "/"
        )
        filename = f"batch_{uuid.uuid4().hex[:12]}.jsonl.gz"
        object_key = f"{partition}/{filename}"

        # Serialize to compressed JSONL
        lines = "\n".join(json.dumps(log) for log in logs)
        data = gzip.compress(lines.encode())

        if sub_platform == S3:
            self._upload_s3(credentials, object_key, data)
        elif sub_platform == AZURE_BLOB:
            self._upload_azure(credentials, object_key, data)
        elif sub_platform == GCS:
            self._upload_gcs(credentials, object_key, data)

        return {"sent": len(logs), "object_key": object_key}

    def _upload_s3(self, credentials: dict, key: str, data: bytes):
        import boto3

        client = boto3.client(
            "s3",
            region_name=credentials.get("region", "us-east-1"),
            aws_access_key_id=credentials["access_key_id"],
            aws_secret_access_key=credentials["secret_access_key"],
        )
        client.put_object(
            Bucket=credentials["bucket"],
            Key=key,
            Body=data,
            ContentEncoding="gzip",
            ContentType="application/x-ndjson",
        )

    def _upload_azure(self, credentials: dict, key: str, data: bytes):
        from azure.storage.blob import BlobServiceClient

        client = BlobServiceClient.from_connection_string(
            credentials["connection_string"]
        )
        container_client = client.get_container_client(credentials["container"])
        container_client.upload_blob(key, data, overwrite=True)

    def _upload_gcs(self, credentials: dict, key: str, data: bytes):
        from google.cloud import storage
        from google.oauth2 import service_account

        info = json.loads(credentials["service_account_json"])
        creds = service_account.Credentials.from_service_account_info(info)
        client = storage.Client(credentials=creds)
        bucket = client.bucket(credentials["bucket"])
        blob = bucket.blob(key)
        blob.upload_from_string(data, content_type="application/x-ndjson")


# Self-register on module import
_cloud_storage_service = CloudStorageService()
register_service("cloud_storage", _cloud_storage_service)
