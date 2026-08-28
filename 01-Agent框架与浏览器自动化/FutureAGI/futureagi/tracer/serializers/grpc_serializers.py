from django_socio_grpc import proto_serializers
from rest_framework import serializers

from tracer.grpc.tracer_pb2 import (
    CreateOtelSpanRequest,
    CreateOtelSpanResponse,
)


class CreateOtelSpanRequestSerializer(proto_serializers.ProtoSerializer):
    """
    Serializer for the incoming otel span data.
    We use a JSONField because the otel data is a complex, nested dictionary.
    """

    otel_data_list = serializers.ListField(child=serializers.JSONField())

    class Meta:
        proto_class_name = "CreateOtelSpanRequest"
        proto_class = CreateOtelSpanRequest


class CreateOtelSpanResponseSerializer(proto_serializers.ProtoSerializer):
    """
    Serializer for the response, which are the IDs of the created spans.
    """

    ids = serializers.ListField(child=serializers.CharField())

    class Meta:
        proto_class_name = "CreateOtelSpanResponse"
        proto_class = CreateOtelSpanResponse
