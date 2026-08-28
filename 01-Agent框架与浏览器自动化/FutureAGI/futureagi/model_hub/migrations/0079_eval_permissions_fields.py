# Add allow_edit / allow_copy permission fields to EvalTemplate

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("model_hub", "0078_ground_truth_embeddings"),
    ]

    operations = [
        migrations.AddField(
            model_name="evaltemplate",
            name="allow_edit",
            field=models.BooleanField(default=True, help_text="Whether users can edit this eval template."),
        ),
        migrations.AddField(
            model_name="evaltemplate",
            name="allow_copy",
            field=models.BooleanField(default=True, help_text="Whether users can duplicate/copy this eval template."),
        ),
    ]
