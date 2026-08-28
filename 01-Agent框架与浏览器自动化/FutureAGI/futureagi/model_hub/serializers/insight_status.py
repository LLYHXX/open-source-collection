from rest_framework import serializers

from model_hub.models import InsightStatus


class InsightStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsightStatus
        fields = "__all__"
