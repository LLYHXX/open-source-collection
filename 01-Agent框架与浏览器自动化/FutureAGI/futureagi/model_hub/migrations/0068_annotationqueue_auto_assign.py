from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("model_hub", "0067_merge_20260316_0730"),
    ]

    operations = [
        migrations.AddField(
            model_name="annotationqueue",
            name="auto_assign",
            field=models.BooleanField(
                default=False,
                help_text="When enabled, all queue members can annotate any item without explicit assignment.",
            ),
        ),
    ]
