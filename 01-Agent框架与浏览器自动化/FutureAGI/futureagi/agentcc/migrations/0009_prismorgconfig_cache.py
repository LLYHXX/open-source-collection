from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prism", "0008_remaining_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="prismorgconfig",
            name="cache",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
