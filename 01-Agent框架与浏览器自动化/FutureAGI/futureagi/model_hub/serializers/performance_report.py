from rest_framework import serializers

from model_hub.models.performance_report import PerformanceReport


class PerformanceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceReport
        fields = "__all__"


class PerformanceReportCreateSerializer(serializers.ModelSerializer):
    start_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    end_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = PerformanceReport
        fields = [
            "name",
            "datasets",
            "filters",
            "breakdown",
            "aggregation",
            "start_date",
            "end_date",
        ]

    def create(self, validated_data):
        model = validated_data.pop("model")
        organization = validated_data.pop("organization")
        return PerformanceReport.objects.create(
            model=model, organization=organization, **validated_data
        )
