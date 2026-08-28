"""
Rename all Prism* models to Agentcc* and their tables from prism_* to agentcc_*.

Data-preserving: every operation is RenameModel / AlterModelTable /
RemoveConstraint+AddConstraint — no DeleteModel, no data loss.

Hand-written because Django's makemigrations autodetector won't offer
"Did you rename?" prompts when any field differs between old and new
(we changed `related_name="prism_*"` → `"agentcc_*"` on FKs earlier,
which counts as a field change). In that state the autodetector silently
falls to DeleteModel+CreateModel, which would wipe all data. All ops
below are standard Django migration operations — equivalent to what
makemigrations would emit if the autodetector could see these as renames.
"""
from django.db import migrations, models


# (old_class_name, new_class_name, new_db_table)
MODEL_RENAMES = [
    ("PrismBlocklist", "AgentccBlocklist", "agentcc_blocklist"),
    ("PrismProviderCredential", "AgentccProviderCredential", "agentcc_provider_credential"),
    ("PrismWebhook", "AgentccWebhook", "agentcc_webhook"),
    ("PrismWebhookEvent", "AgentccWebhookEvent", "agentcc_webhook_event"),
    ("PrismEmailAlert", "AgentccEmailAlert", "agentcc_email_alert"),
    ("PrismSession", "AgentccSession", "agentcc_session"),
    ("PrismRoutingPolicy", "AgentccRoutingPolicy", "agentcc_routing_policy"),
    ("PrismAPIKey", "AgentccAPIKey", "agentcc_api_key"),
    ("PrismShadowExperiment", "AgentccShadowExperiment", "agentcc_shadow_experiment"),
    ("PrismCustomPropertySchema", "AgentccCustomPropertySchema", "agentcc_custom_property_schema"),
    ("PrismShadowResult", "AgentccShadowResult", "agentcc_shadow_result"),
    ("PrismRequestLog", "AgentccRequestLog", "agentcc_request_log"),
    ("PrismOrgConfig", "AgentccOrgConfig", "agentcc_org_config"),
    ("PrismGuardrailFeedback", "AgentccGuardrailFeedback", "agentcc_guardrail_feedback"),
    ("PrismProject", "AgentccProject", "agentcc_project"),
    ("PrismGuardrailPolicy", "AgentccGuardrailPolicy", "agentcc_guardrail_policy"),
    # PrismPromptTemplate omitted: deleted in migration 0012, zombie in code only.
]


# (lowercase_model_name, old_name, new_name, fields list, Q condition)
# Fields + condition MUST match Meta.constraints in the current model exactly,
# otherwise the autodetector sees drift and wants to regenerate.
CONSTRAINT_RENAMES = [
    (
        "agentccblocklist",
        "unique_prism_blocklist_name",
        "unique_agentcc_blocklist_name",
        ["organization", "name"],
        models.Q(deleted=False),
    ),
    (
        "agentccprovidercredential",
        "unique_prism_provider_per_org",
        "unique_agentcc_provider_per_org",
        ["organization", "provider_name"],
        models.Q(deleted=False),
    ),
    (
        "agentccwebhook",
        "unique_prism_webhook_name",
        "unique_agentcc_webhook_name",
        ["organization", "name"],
        models.Q(deleted=False),
    ),
    (
        "agentccemailalert",
        "unique_prism_email_alert_name_per_org",
        "unique_agentcc_email_alert_name_per_org",
        ["organization", "name"],
        models.Q(deleted=False),
    ),
    (
        "agentccsession",
        "unique_prism_session_id",
        "unique_agentcc_session_id",
        ["organization", "session_id"],
        models.Q(deleted=False),
    ),
    (
        "agentccroutingpolicy",
        "unique_prism_routing_policy_version",
        "unique_agentcc_routing_policy_version",
        ["organization", "name", "version"],
        models.Q(deleted=False),
    ),
    (
        "agentccapikey",
        "unique_prism_api_key_id",
        "unique_agentcc_api_key_id",
        ["gateway_key_id"],
        models.Q(deleted=False),
    ),
    (
        "agentccshadowexperiment",
        "unique_prism_shadow_experiment_name",
        "unique_agentcc_shadow_experiment_name",
        ["organization", "name"],
        models.Q(deleted=False),
    ),
    (
        "agentcccustompropertyschema",
        "unique_prism_custom_property_name",
        "unique_agentcc_custom_property_name",
        ["organization", "name"],
        models.Q(deleted=False),
    ),
    (
        "agentccorgconfig",
        "unique_prism_org_config_version",
        "unique_agentcc_org_config_version",
        ["organization", "version"],
        models.Q(deleted=False),
    ),
    (
        "agentccorgconfig",
        "unique_prism_org_config_active",
        "unique_agentcc_org_config_active",
        ["organization"],
        models.Q(deleted=False, is_active=True),
    ),
    (
        "agentccproject",
        "unique_prism_project_per_org",
        "unique_agentcc_project_per_org",
        ["organization", "name"],
        models.Q(deleted=False),
    ),
    (
        "agentccguardrailpolicy",
        "unique_prism_guardrail_policy_name",
        "unique_agentcc_guardrail_policy_name",
        ["organization", "name"],
        models.Q(deleted=False),
    ),
    # PrismPromptTemplate omitted — model is a zombie (deleted in 0012).
]


def _build_ops():
    ops = []

    # 1. Rename classes. Since Meta.db_table now says agentcc_*, Django's
    #    RenameModel will issue ALTER TABLE prism_X RENAME TO agentcc_X.
    for old, new, _ in MODEL_RENAMES:
        ops.append(migrations.RenameModel(old_name=old, new_name=new))

    # 2. Explicitly set db_table post-rename. No-op when already matches, but
    #    necessary for shadow_experiment / shadow_result where the old table
    #    was prism_prismshadow* (Django's default for pre-rename class names)
    #    rather than prism_shadow_*.
    for _, new, table in MODEL_RENAMES:
        ops.append(migrations.AlterModelTable(name=new.lower(), table=table))

    # 3. Rename unique constraints (RemoveConstraint then AddConstraint —
    #    Django has no RenameConstraint operation). Fields + condition
    #    mirror the current Meta.constraints in each model.
    for model_name, old_name, new_name, fields, condition in CONSTRAINT_RENAMES:
        ops.append(
            migrations.RemoveConstraint(model_name=model_name, name=old_name)
        )
        ops.append(
            migrations.AddConstraint(
                model_name=model_name,
                constraint=models.UniqueConstraint(
                    fields=fields,
                    condition=condition,
                    name=new_name,
                ),
            )
        )

    return ops


class Migration(migrations.Migration):

    dependencies = [
        ("prism", "0023_alter_prismshadowexperiment_unique_together_and_more"),
    ]

    operations = _build_ops()
