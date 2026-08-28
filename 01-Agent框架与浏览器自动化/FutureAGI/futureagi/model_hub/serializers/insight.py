from rest_framework import serializers

from model_hub.models import Insight
from model_hub.serializers.ai_model import AIModelSerializer


class InsightSerializer(serializers.ModelSerializer):
    model = AIModelSerializer()

    class Meta:
        model = Insight
        fields = "__all__"
