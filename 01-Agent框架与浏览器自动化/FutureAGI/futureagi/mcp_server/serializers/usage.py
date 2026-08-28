from rest_framework import serializers


class MCPUsageSummarySerializer(serializers.Serializer):
    total_calls = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    avg_latency_ms = serializers.FloatField()
    error_rate = serializers.FloatField()
    active_sessions = serializers.IntegerField()


class MCPUsageToolBreakdownSerializer(serializers.Serializer):
    tool_name = serializers.CharField()
    call_count = serializers.IntegerField()
    avg_latency_ms = serializers.FloatField()
    error_rate = serializers.FloatField()


class MCPUsageTimelineSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    call_count = serializers.IntegerField()
