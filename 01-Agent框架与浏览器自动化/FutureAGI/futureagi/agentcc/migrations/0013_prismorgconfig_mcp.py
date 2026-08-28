from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prism", "0012_shadow_experiments"),
    ]

    operations = [
        migrations.AddField(
            model_name="prismorgconfig",
            name="mcp",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
