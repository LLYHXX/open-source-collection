from rest_framework import serializers

from accounts.serializers.user import UserSerializer
from model_hub.models import AnnotationTask
from model_hub.serializers.ai_model import AIModelSerializer


class AnnotationTaskSerializer(serializers.ModelSerializer):
    assigned_users = UserSerializer(many=True, read_only=True)
    ai_model = AIModelSerializer(read_only=True)

    class Meta:
        model = AnnotationTask
        fields = [
            "id",
            "assigned_users",
            "created_at",
            "updated_at",
            "ai_model",
            "task_name",
        ]
