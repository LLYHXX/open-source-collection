"""
Add remaining 6.6 models: PrismSession, PrismWebhook, PrismWebhookEvent,
PrismCustomPropertySchema, PrismRoutingPolicy, PrismPromptTemplate.
"""

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_alter_user_organization_role'),
        ('prism', '0007_prismguardrailfeedback'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # PrismSession
        migrations.CreateModel(
            name='PrismSession',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('session_id', models.CharField(max_length=255)),
                ('name', models.CharField(blank=True, default='', max_length=255)),
                ('status', models.CharField(choices=[('active', 'Active'), ('closed', 'Closed')], default='active', max_length=20)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prism_sessions', to='accounts.organization')),
            ],
            options={'db_table': 'prism_session', 'ordering': ['-created_at']},
        ),
        migrations.AddIndex(model_name='prismsession', index=models.Index(fields=['organization'], name='prism_sess_org_idx')),
        migrations.AddIndex(model_name='prismsession', index=models.Index(fields=['session_id'], name='prism_sess_sid_idx')),
        migrations.AddIndex(model_name='prismsession', index=models.Index(fields=['status'], name='prism_sess_status_idx')),
        migrations.AddConstraint(model_name='prismsession', constraint=models.UniqueConstraint(condition=models.Q(('deleted', False)), fields=('organization', 'session_id'), name='unique_prism_session_id')),

        # PrismWebhook
        migrations.CreateModel(
            name='PrismWebhook',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('url', models.URLField(max_length=2048)),
                ('secret', models.CharField(blank=True, default='', max_length=255)),
                ('events', models.JSONField(blank=True, default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('headers', models.JSONField(blank=True, default=dict)),
                ('description', models.TextField(blank=True, default='')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prism_webhooks', to='accounts.organization')),
            ],
            options={'db_table': 'prism_webhook', 'ordering': ['name']},
        ),
        migrations.AddIndex(model_name='prismwebhook', index=models.Index(fields=['organization'], name='prism_wh_org_idx')),
        migrations.AddConstraint(model_name='prismwebhook', constraint=models.UniqueConstraint(condition=models.Q(('deleted', False)), fields=('organization', 'name'), name='unique_prism_webhook_name')),

        # PrismWebhookEvent
        migrations.CreateModel(
            name='PrismWebhookEvent',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(max_length=50)),
                ('payload', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('delivered', 'Delivered'), ('failed', 'Failed'), ('dead_letter', 'Dead Letter')], default='pending', max_length=20)),
                ('attempts', models.IntegerField(default=0)),
                ('max_attempts', models.IntegerField(default=5)),
                ('last_attempt_at', models.DateTimeField(blank=True, null=True)),
                ('last_response_code', models.IntegerField(blank=True, null=True)),
                ('last_error', models.TextField(blank=True, default='')),
                ('next_retry_at', models.DateTimeField(blank=True, null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prism_webhook_events', to='accounts.organization')),
                ('webhook', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webhook_events', to='prism.prismwebhook')),
            ],
            options={'db_table': 'prism_webhook_event', 'ordering': ['-created_at']},
        ),
        migrations.AddIndex(model_name='prismwebhookevent', index=models.Index(fields=['organization'], name='prism_whe_org_idx')),
        migrations.AddIndex(model_name='prismwebhookevent', index=models.Index(fields=['webhook'], name='prism_whe_wh_idx')),
        migrations.AddIndex(model_name='prismwebhookevent', index=models.Index(fields=['status'], name='prism_whe_status_idx')),
        migrations.AddIndex(model_name='prismwebhookevent', index=models.Index(fields=['next_retry_at'], name='prism_whe_retry_idx')),

        # PrismCustomPropertySchema
        migrations.CreateModel(
            name='PrismCustomPropertySchema',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('property_type', models.CharField(choices=[('string', 'String'), ('number', 'Number'), ('boolean', 'Boolean'), ('enum', 'Enum')], default='string', max_length=20)),
                ('required', models.BooleanField(default=False)),
                ('allowed_values', models.JSONField(blank=True, default=list)),
                ('default_value', models.JSONField(blank=True, null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prism_custom_property_schemas', to='accounts.organization')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='custom_property_schemas', to='prism.prismproject')),
            ],
            options={'db_table': 'prism_custom_property_schema', 'ordering': ['name']},
        ),
        migrations.AddIndex(model_name='prismcustompropertyschema', index=models.Index(fields=['organization'], name='prism_cp_org_idx')),
        migrations.AddConstraint(model_name='prismcustompropertyschema', constraint=models.UniqueConstraint(condition=models.Q(('deleted', False)), fields=('organization', 'name'), name='unique_prism_custom_property_name')),

        # PrismRoutingPolicy
        migrations.CreateModel(
            name='PrismRoutingPolicy',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('version', models.PositiveIntegerField(default=1)),
                ('config', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prism_routing_policies', to='accounts.organization')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prism_routing_policies', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'prism_routing_policy', 'ordering': ['name', '-version']},
        ),
        migrations.AddIndex(model_name='prismroutingpolicy', index=models.Index(fields=['organization'], name='prism_rp_org_idx')),
        migrations.AddIndex(model_name='prismroutingpolicy', index=models.Index(fields=['name'], name='prism_rp_name_idx')),
        migrations.AddConstraint(model_name='prismroutingpolicy', constraint=models.UniqueConstraint(condition=models.Q(('deleted', False)), fields=('organization', 'name', 'version'), name='unique_prism_routing_policy_version')),

        # PrismPromptTemplate
        migrations.CreateModel(
            name='PrismPromptTemplate',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('version', models.PositiveIntegerField(default=1)),
                ('template', models.TextField()),
                ('variables', models.JSONField(blank=True, default=list)),
                ('model', models.CharField(blank=True, default='', max_length=255)),
                ('environment', models.CharField(choices=[('dev', 'Development'), ('staging', 'Staging'), ('prod', 'Production')], default='dev', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prism_prompt_templates', to='accounts.organization')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prism_prompt_templates', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'prism_prompt_template', 'ordering': ['name', '-version']},
        ),
        migrations.AddIndex(model_name='prismprompttemplate', index=models.Index(fields=['organization'], name='prism_pt_org_idx')),
        migrations.AddIndex(model_name='prismprompttemplate', index=models.Index(fields=['name'], name='prism_pt_name_idx')),
        migrations.AddIndex(model_name='prismprompttemplate', index=models.Index(fields=['environment'], name='prism_pt_env_idx')),
        migrations.AddConstraint(model_name='prismprompttemplate', constraint=models.UniqueConstraint(condition=models.Q(('deleted', False)), fields=('organization', 'name', 'version', 'environment'), name='unique_prism_prompt_template_version')),
    ]
