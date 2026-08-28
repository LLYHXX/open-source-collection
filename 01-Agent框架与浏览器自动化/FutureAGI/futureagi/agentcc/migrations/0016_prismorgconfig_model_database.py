from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prism", "0015_prismorgconfig_audit"),
    ]

    operations = [
        migrations.AddField(
            model_name="prismorgconfig",
            name="model_database",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
