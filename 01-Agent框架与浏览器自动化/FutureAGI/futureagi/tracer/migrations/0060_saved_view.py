# Generated manually

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracer", "0059_dashboardwidget_dashboard_pos_idx"),
        ("accounts", "0013_alter_user_organization_role"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SavedView",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "deleted",
                    models.BooleanField(db_index=True, default=False),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, null=True),
                ),
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
                    "name",
                    models.CharField(max_length=255),
                ),
                (
                    "tab_type",
                    models.CharField(
                        choices=[
                            ("traces", "Traces"),
                            ("spans", "Spans"),
                            ("voice", "Voice"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "visibility",
                    models.CharField(
                        choices=[
                            ("personal", "Personal"),
                            ("project", "Project"),
                        ],
                        default="personal",
                        max_length=20,
                    ),
                ),
                (
                    "position",
                    models.IntegerField(default=0),
                ),
                (
                    "icon",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                (
                    "config",
                    models.JSONField(blank=True, default=dict),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="saved_views",
                        to="tracer.project",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="saved_views",
                        to="accounts.workspace",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_saved_views",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_saved_views",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "tracer_saved_view",
                "ordering": ["position", "created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="savedview",
            index=models.Index(
                fields=["project", "created_by", "visibility"],
                name="tracer_save_project_user_vis_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="savedview",
            index=models.Index(
                fields=["project", "visibility"],
                name="tracer_save_project_vis_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="savedview",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted", False)),
                fields=("project", "created_by", "name"),
                name="unique_saved_view_name_per_user_project",
            ),
        ),
    ]
