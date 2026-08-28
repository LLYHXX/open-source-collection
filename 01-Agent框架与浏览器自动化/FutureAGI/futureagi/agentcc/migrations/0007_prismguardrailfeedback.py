import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_alter_user_organization_role'),
        ('prism', '0006_prismblocklist'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PrismGuardrailFeedback',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('check_name', models.CharField(max_length=255)),
                ('feedback', models.CharField(choices=[('correct', 'Correct'), ('false_positive', 'False Positive'), ('false_negative', 'False Negative'), ('unsure', 'Unsure')], max_length=20)),
                ('comment', models.TextField(blank=True, default='')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prism_guardrail_feedback', to='accounts.organization')),
                ('request_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guardrail_feedback', to='prism.prismrequestlog')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prism_guardrail_feedback', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'prism_guardrail_feedback',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='prismguardrailfeedback',
            index=models.Index(fields=['organization'], name='prism_gfeed_org_idx'),
        ),
        migrations.AddIndex(
            model_name='prismguardrailfeedback',
            index=models.Index(fields=['request_log'], name='prism_gfeed_reqlog_idx'),
        ),
        migrations.AddIndex(
            model_name='prismguardrailfeedback',
            index=models.Index(fields=['check_name'], name='prism_gfeed_check_idx'),
        ),
    ]
