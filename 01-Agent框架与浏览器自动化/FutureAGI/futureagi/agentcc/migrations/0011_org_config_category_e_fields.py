from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prism", "0010_prismorgconfig_rate_limiting"),
    ]

    operations = [
        migrations.AddField(
            model_name="prismorgconfig",
            name="budgets",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="prismorgconfig",
            name="cost_tracking",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="prismorgconfig",
            name="ip_acl",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="prismorgconfig",
            name="alerting",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="prismorgconfig",
            name="privacy",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="prismorgconfig",
            name="tool_policy",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
