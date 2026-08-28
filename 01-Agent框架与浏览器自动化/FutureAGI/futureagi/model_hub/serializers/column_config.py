from rest_framework import serializers

from model_hub.models import ColumnConfig


class ColumnConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColumnConfig
        fields = [
            "id",
            "table_name",
            "identifier",
            "columns",
        ]
