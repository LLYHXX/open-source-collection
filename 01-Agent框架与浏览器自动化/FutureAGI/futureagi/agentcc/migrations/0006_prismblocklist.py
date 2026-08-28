import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_alter_user_organization_role'),
        ('prism', '0005_prismguardrailpolicy_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrismBlocklist',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('words', models.JSONField(blank=True, default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prism_blocklists', to='accounts.organization')),
            ],
            options={
                'db_table': 'prism_blocklist',
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='prismblocklist',
            index=models.Index(fields=['organization'], name='prism_block_organiz_idx'),
        ),
        migrations.AddConstraint(
            model_name='prismblocklist',
            constraint=models.UniqueConstraint(condition=models.Q(('deleted', False)), fields=('organization', 'name'), name='unique_prism_blocklist_name'),
        ),
    ]
