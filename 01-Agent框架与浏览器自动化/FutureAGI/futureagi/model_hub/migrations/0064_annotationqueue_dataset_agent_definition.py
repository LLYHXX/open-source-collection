import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("model_hub", "0063_annotationqueue_project_is_default"),
        ("simulate", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="annotationqueue",
            name="dataset",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="annotation_queues",
                to="model_hub.dataset",
            ),
        ),
        migrations.AddField(
            model_name="annotationqueue",
            name="agent_definition",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="annotation_queues",
                to="simulate.agentdefinition",
            ),
        ),
        # Update the org-level name uniqueness to exclude dataset/agent scoped queues
        migrations.RemoveConstraint(
            model_name="annotationqueue",
            name="unique_active_queue_name_org",
        ),
        migrations.AddConstraint(
            model_name="annotationqueue",
            constraint=models.UniqueConstraint(
                fields=["organization", "name"],
                condition=Q(
                    deleted=False,
                    project__isnull=True,
                    dataset__isnull=True,
                    agent_definition__isnull=True,
                ),
                name="unique_active_queue_name_org",
            ),
        ),
        # Name uniqueness per dataset
        migrations.AddConstraint(
            model_name="annotationqueue",
            constraint=models.UniqueConstraint(
                fields=["organization", "name", "dataset"],
                condition=Q(deleted=False, dataset__isnull=False),
                name="unique_active_queue_name_org_dataset",
            ),
        ),
        # Name uniqueness per agent_definition
        migrations.AddConstraint(
            model_name="annotationqueue",
            constraint=models.UniqueConstraint(
                fields=["organization", "name", "agent_definition"],
                condition=Q(deleted=False, agent_definition__isnull=False),
                name="unique_active_queue_name_org_agent",
            ),
        ),
        # One default queue per dataset
        migrations.AddConstraint(
            model_name="annotationqueue",
            constraint=models.UniqueConstraint(
                fields=["dataset"],
                condition=Q(deleted=False, is_default=True, dataset__isnull=False),
                name="unique_default_queue_per_dataset",
            ),
        ),
        # One default queue per agent_definition
        migrations.AddConstraint(
            model_name="annotationqueue",
            constraint=models.UniqueConstraint(
                fields=["agent_definition"],
                condition=Q(deleted=False, is_default=True, agent_definition__isnull=False),
                name="unique_default_queue_per_agent",
            ),
        ),
        # Update the project default constraint to be explicit
        migrations.RemoveConstraint(
            model_name="annotationqueue",
            name="unique_default_queue_per_project",
        ),
        migrations.AddConstraint(
            model_name="annotationqueue",
            constraint=models.UniqueConstraint(
                fields=["project"],
                condition=Q(deleted=False, is_default=True, project__isnull=False),
                name="unique_default_queue_per_project",
            ),
        ),
    ]
