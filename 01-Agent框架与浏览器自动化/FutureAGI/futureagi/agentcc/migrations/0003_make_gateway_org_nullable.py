"""
Make PrismGateway.organization nullable — the gateway is a system-wide singleton
shared across all organizations. Also simplify the unique constraint.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prism", "0002_prismrequestlog_guardrail_results_and_more"),
    ]

    operations = [
        # 1. Make organization nullable
        migrations.AlterField(
            model_name="prismgateway",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prism_gateways",
                to="accounts.organization",
            ),
        ),
        # 2. Remove old constraint and indexes
        migrations.RemoveConstraint(
            model_name="prismgateway",
            name="unique_prism_gateway_per_org_workspace",
        ),
        migrations.RemoveIndex(
            model_name="prismgateway",
            name="prism_gatew_organiz_0d96d6_idx",
        ),
        migrations.RemoveIndex(
            model_name="prismgateway",
            name="prism_gatew_organiz_241445_idx",
        ),
        # 3. Add new simpler constraint (unique name when not deleted)
        migrations.AddConstraint(
            model_name="prismgateway",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted", False)),
                fields=("name",),
                name="unique_prism_gateway_name",
            ),
        ),
    ]
