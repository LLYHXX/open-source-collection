from rest_framework import serializers

from simulate.models.chat_message import ChatMessageModel


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessageModel - stores chat messages for call executions"""

    class Meta:
        model = ChatMessageModel
        fields = [
            "id",
            "role",
            "messages",
            "content",
            "session_id",
            "tool_calls",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
