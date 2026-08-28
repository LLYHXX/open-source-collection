import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("model_hub", "0060_alter_dataset_eval_reason_status_annotationqueue_and_more"),
        ("tracer", "0046_replaysession"),
    ]

    operations = [
        migrations.AddField(
            model_name="queueitem",
            name="trace_session",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="queue_items",
                to="tracer.tracesession",
            ),
        ),
        migrations.AlterField(
            model_name="queueitem",
            name="source_type",
            field=models.CharField(
                choices=[
                    ("dataset_row", "Dataset Row"),
                    ("trace", "Trace"),
                    ("observation_span", "Observation Span"),
                    ("prototype_run", "Prototype Run"),
                    ("call_execution", "Call Execution"),
                    ("trace_session", "Trace Session"),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="automationrule",
            name="source_type",
            field=models.CharField(
                choices=[
                    ("dataset_row", "Dataset Row"),
                    ("trace", "Trace"),
                    ("observation_span", "Observation Span"),
                    ("prototype_run", "Prototype Run"),
                    ("call_execution", "Call Execution"),
                    ("trace_session", "Trace Session"),
                ],
                max_length=50,
            ),
        ),
        migrations.AddConstraint(
            model_name="queueitem",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted", False), ("trace_session__isnull", False)),
                fields=("queue", "trace_session"),
                name="unique_queue_trace_session",
            ),
        ),
    ]
