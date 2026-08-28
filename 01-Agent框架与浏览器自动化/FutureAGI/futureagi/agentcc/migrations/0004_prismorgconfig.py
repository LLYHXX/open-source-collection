"""
Add PrismOrgConfig model for per-organization gateway configuration.
Each org gets its own provider API keys, guardrail pipeline, and routing strategy.
"""

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_alter_user_organization_role"),
        ("prism", "0003_make_gateway_org_nullable"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PrismOrgConfig",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted", models.BooleanField(db_index=True, default=False)),
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
                ("version", models.PositiveIntegerField(default=1)),
                ("providers", models.JSONField(blank=True, default=dict)),
                ("guardrails", models.JSONField(blank=True, default=dict)),
                ("routing", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("change_description", models.TextField(blank=True, default="")),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prism_org_configs",
                        to="accounts.organization",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="prism_org_configs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "prism_org_config",
                "ordering": ["-version"],
            },
        ),
        migrations.AddIndex(
            model_name="prismorgconfig",
            index=models.Index(
                fields=["organization", "-version"],
                name="prism_org_c_organiz_ver_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="prismorgconfig",
            index=models.Index(
                fields=["organization", "is_active"],
                name="prism_org_c_organiz_act_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="prismorgconfig",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted", False)),
                fields=("organization", "version"),
                name="unique_prism_org_config_version",
            ),
        ),
        migrations.AddConstraint(
            model_name="prismorgconfig",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted", False), ("is_active", True)),
                fields=("organization",),
                name="unique_prism_org_config_active",
            ),
        ),
    ]
