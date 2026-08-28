from rest_framework import serializers

from agent_playground.models.edge import Edge
from agent_playground.serializers.port import PortReadSerializer


class SourceNodeOutputPortsSerializer(serializers.Serializer):
    """Serializer for source node with its output ports."""

    source_node_id = serializers.UUIDField(help_text="UUID of the source node")
    source_node_name = serializers.CharField(help_text="Name of the source node")
    node_connection_id = serializers.UUIDField(help_text="UUID of the NodeConnection")
    output_ports = PortReadSerializer(
        many=True, help_text="All output ports from the source node"
    )


class EdgeReadSerializer(serializers.ModelSerializer):
    """Serializer for reading edge data in responses."""

    source_port_id = serializers.UUIDField(source="source_port.id", read_only=True)
    target_port_id = serializers.UUIDField(source="target_port.id", read_only=True)

    class Meta:
        model = Edge
        fields = [
            "id",
            "source_port_id",
            "target_port_id",
        ]
        read_only_fields = fields


class EdgeWriteSerializer(serializers.Serializer):
    """Serializer for writing edge data in requests."""

    source_port_temp_id = serializers.CharField(
        required=True, help_text="Temporary ID of the source port"
    )
    target_port_temp_id = serializers.CharField(
        required=True, help_text="Temporary ID of the target port"
    )
