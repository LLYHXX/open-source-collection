"""Add workspace/org fields to models that were updated in recent pull."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_alter_user_organization_role"),
        ("prism", "0018_provider_credential_key_hash_admin_encrypt"),
    ]

    operations = [
        # OrgConfig: add nullable workspace FK
        migrations.AddField(
            model_name="prismorgconfig",
            name="workspace",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prism_org_configs",
                to="accounts.workspace",
            ),
        ),
        # Session: add nullable workspace FK
        migrations.AddField(
            model_name="prismsession",
            name="workspace",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prism_sessions",
                to="accounts.workspace",
            ),
        ),
        # ShadowExperiment: add organization FK (non-nullable, but table is empty)
        migrations.AddField(
            model_name="prismshadowexperiment",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prism_shadow_experiments",
                to="accounts.organization",
            ),
            preserve_default=False,
        ),
        # ShadowExperiment: add nullable workspace FK
        migrations.AddField(
            model_name="prismshadowexperiment",
            name="workspace",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prism_shadow_experiments",
                to="accounts.workspace",
            ),
        ),
        # ShadowResult: add organization FK (non-nullable, but table is empty)
        migrations.AddField(
            model_name="prismshadowresult",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prism_shadow_results",
                to="accounts.organization",
            ),
            preserve_default=False,
        ),
        # ShadowResult: add nullable workspace FK
        migrations.AddField(
            model_name="prismshadowresult",
            name="workspace",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prism_shadow_results",
                to="accounts.workspace",
            ),
        ),
    ]
