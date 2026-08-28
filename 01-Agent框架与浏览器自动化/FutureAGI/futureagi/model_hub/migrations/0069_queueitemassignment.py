import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("model_hub", "0068_annotationqueue_auto_assign"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="QueueItemAssignment",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "queue_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to="model_hub.queueitem",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="queue_item_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddConstraint(
            model_name="queueitemassignment",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted", False)),
                fields=("queue_item", "user"),
                name="unique_active_queue_item_assignment",
            ),
        ),
        migrations.AddField(
            model_name="queueitem",
            name="assigned_users",
            field=models.ManyToManyField(
                blank=True,
                related_name="multi_assigned_queue_items",
                through="model_hub.QueueItemAssignment",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
