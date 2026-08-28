"""
Migration script: Convert DeterministicEvaluator templates to AgentEvaluator.

Changes:
  - config.eval_type_id: "DeterministicEvaluator" → "AgentEvaluator"
  - eval_type: → "agent"
  - Copies criteria → config.rule_prompt
  - Adds agent-specific config fields (agent_mode, tools, etc.)

Usage:
    # Dry run:
    python manage.py shell -c "from evaluations.scripts.migrate_deterministic_to_agent import run; run('--dry-run')"

    # Execute:
    python manage.py shell -c "from evaluations.scripts.migrate_deterministic_to_agent import run; run()"
"""

import copy
import json

import structlog

logger = structlog.get_logger(__name__)


def migrate_config(template):
    """
    Transform a DeterministicEvaluator config into AgentEvaluator config.

    DeterministicEvaluator reads:
      - eval_template.criteria → rule_prompt
      - config.choices / eval_template.choices
      - config.multi_choice / eval_template.multi_choice
      - config.output → output_type

    AgentEvaluator needs:
      - config.eval_type_id = "AgentEvaluator"
      - config.rule_prompt = the criteria/instructions
      - config.agent_mode = "agent"
      - config.tools = {}
      - config.knowledge_bases = []
      - config.check_internet = False
      - config.data_injection = {}
      - config.summary = {"type": "concise"}
      - config.output = (preserved from original)
      - config.required_keys = (preserved from original)

    Returns the new config dict.
    """
    old_config = copy.deepcopy(template.config or {})
    new_config = {}

    # Core identity
    new_config["eval_type_id"] = "AgentEvaluator"

    # Preserve existing fields
    new_config["required_keys"] = old_config.get("required_keys", [])
    new_config["optional_keys"] = old_config.get("optional_keys", [])
    new_config["output"] = old_config.get("output", "Pass/Fail")

    # Map criteria → rule_prompt
    # DeterministicEvaluator stores instructions in eval_template.criteria
    # and sometimes in config.rule_prompt or config.config.rule_prompt
    rule_prompt = (
        old_config.get("rule_prompt")
        or (old_config.get("config", {}) or {}).get("rule_prompt")
        or template.criteria
        or ""
    )
    new_config["rule_prompt"] = rule_prompt

    # Agent-specific fields
    new_config["agent_mode"] = "agent"
    new_config["tools"] = old_config.get("tools", {})
    new_config["knowledge_bases"] = old_config.get("knowledge_bases", [])
    new_config["check_internet"] = old_config.get("check_internet", False)
    new_config["data_injection"] = old_config.get("data_injection", {})
    new_config["summary"] = old_config.get("summary", {"type": "concise"})

    # Preserve param modalities if set
    if "param_modalities" in old_config:
        new_config["param_modalities"] = old_config["param_modalities"]

    # Preserve config_params_desc if set
    if "config_params_desc" in old_config:
        new_config["config_params_desc"] = old_config["config_params_desc"]

    # Preserve any model setting
    if "model" in old_config:
        new_config["model"] = old_config["model"]

    return new_config


def run(*args):
    dry_run = "--dry-run" in args

    from django.db import transaction

    from model_hub.models.evals_metric import EvalTemplate

    templates = EvalTemplate.no_workspace_objects.filter(
        deleted=False,
        config__eval_type_id="DeterministicEvaluator",
    )
    total = templates.count()
    print(f"\nFound {total} DeterministicEvaluator templates to migrate")

    updates = []

    for tmpl in templates.iterator():
        new_config = migrate_config(tmpl)

        if dry_run:
            print(f"\n  [{tmpl.id}] {tmpl.name}")
            print(f"    eval_type: {tmpl.eval_type!r} -> 'agent'")
            print(f"    eval_type_id: DeterministicEvaluator -> AgentEvaluator")
            print(
                f"    rule_prompt: {new_config['rule_prompt'][:80]}..."
                if len(new_config.get("rule_prompt", "")) > 80
                else f"    rule_prompt: {new_config.get('rule_prompt', '')!r}"
            )
            print(f"    output: {new_config['output']}")
            print(f"    required_keys: {new_config['required_keys']}")
        else:
            tmpl.config = new_config
            tmpl.eval_type = "agent"
            updates.append(tmpl)

    if not dry_run and updates:
        batch_size = 100
        with transaction.atomic():
            for i in range(0, len(updates), batch_size):
                batch = updates[i : i + batch_size]
                EvalTemplate.no_workspace_objects.bulk_update(
                    batch, ["config", "eval_type"], batch_size=batch_size
                )
        print(f"\nMigrated {len(updates)} templates")

    print(f"\n--- Stats ---")
    print(f"  Total:    {total}")
    print(f"  Migrated: {len(updates) if not dry_run else total}")

    if dry_run:
        print(f"\n  *** DRY RUN — no changes written ***")
