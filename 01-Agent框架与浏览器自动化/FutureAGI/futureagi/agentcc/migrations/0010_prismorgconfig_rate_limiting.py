from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prism", "0009_prismorgconfig_cache"),
    ]

    operations = [
        migrations.AddField(
            model_name="prismorgconfig",
            name="rate_limiting",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
