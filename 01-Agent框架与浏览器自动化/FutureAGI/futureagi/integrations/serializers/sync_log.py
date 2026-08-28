from rest_framework import serializers

from integrations.models import SyncLog


class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncLog
        fields = [
            "id",
            "connection",
            "status",
            "started_at",
            "completed_at",
            "traces_fetched",
            "traces_created",
            "traces_updated",
            "spans_synced",
            "scores_synced",
            "error_message",
            "error_details",
            "sync_from",
            "sync_to",
        ]
        read_only_fields = fields
