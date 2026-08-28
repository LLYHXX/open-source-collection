from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_alter_user_organization_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="region",
            field=models.CharField(default="us", max_length=16),
        ),
    ]
