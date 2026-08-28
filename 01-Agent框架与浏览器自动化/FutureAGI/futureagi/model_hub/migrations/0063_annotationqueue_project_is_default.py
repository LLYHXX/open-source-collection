import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("model_hub", "0062_ttsvoice_score"),
        ("tracer", "0046_replaysession"),
    ]

    operations = [
        migrations.AddField(
            model_name="annotationqueue",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="annotation_queues",
                to="tracer.project",
            ),
        ),
        migrations.AddField(
            model_name="annotationqueue",
            name="is_default",
            field=models.BooleanField(default=False),
        ),
        # Keep the original constraint for queues without a project
        migrations.RemoveConstraint(
            model_name="annotationqueue",
            name="unique_active_queue_name_org",
        ),
        migrations.AddConstraint(
            model_name="annotationqueue",
            constraint=models.UniqueConstraint(
                fields=["organization", "name"],
                condition=Q(deleted=False, project__isnull=True),
                name="unique_active_queue_name_org",
            ),
        ),
        # New constraint for queues with a project
        migrations.AddConstraint(
            model_name="annotationqueue",
            constraint=models.UniqueConstraint(
                fields=["organization", "name", "project"],
                condition=Q(deleted=False, project__isnull=False),
                name="unique_active_queue_name_org_project",
            ),
        ),
        # Only one default queue per project
        migrations.AddConstraint(
            model_name="annotationqueue",
            constraint=models.UniqueConstraint(
                fields=["project"],
                condition=Q(deleted=False, is_default=True),
                name="unique_default_queue_per_project",
            ),
        ),
    ]
