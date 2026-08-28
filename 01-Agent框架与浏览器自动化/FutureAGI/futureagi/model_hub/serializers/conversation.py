from rest_framework import serializers

from model_hub.models import Conversation, Message, Node


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "created_at",
            "updated_at",
            "author",
            "content",
            "metadata",
        ]


class NodeSerializer(serializers.ModelSerializer):
    message = MessageSerializer()  # Nested serializer

    class Meta:
        model = Node
        fields = [
            "id",
            "user_provided_id",
            "parent_node",
            "message",
            "conversation",
        ]


class ConversationSerializer(serializers.ModelSerializer):
    nodes = NodeSerializer(many=True, read_only=True)  # Nested serializer
    root_node = NodeSerializer(read_only=True)  # Serializer for the root node

    class Meta:
        model = Conversation
        fields = [
            "id",
            "user_provided_id",
            "title",
            "created_at",
            "updated_at",
            "root_node",
            "nodes",
            "organization",
            "metadata",
        ]
