"""
Apply the system eval catalog to the database.

Updates all system eval templates with:
  - Agent evals: rule_prompt from YAML, synced to criteria
  - Code evals: Python code from system_eval_code.py, stored in config.code

Usage:
    python manage.py shell -c "from evaluations.scripts.apply_catalog import run; run('--dry-run')"
    python manage.py shell -c "from evaluations.scripts.apply_catalog import run; run()"
"""

import os

import structlog
import yaml

logger = structlog.get_logger(__name__)

CATALOG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*args):
    dry_run = "--dry-run" in args

    from django.db import transaction

    from evaluations.catalog.system_eval_code import CODE_REGISTRY
    from model_hub.models.evals_metric import EvalTemplate

    # Load YAML catalog
    yaml_path = os.path.join(CATALOG_DIR, "catalog", "system_evals.yaml")
    with open(yaml_path) as f:
        catalog = yaml.safe_load(f)

    print(f"Loaded catalog: {len(catalog)} entries")
    print(f"Code registry: {len(CODE_REGISTRY)} entries")

    stats = {
        "agent_updated": 0,
        "code_updated": 0,
        "not_found": 0,
        "already_ok": 0,
        "skipped": 0,
    }
    updates = []

    # --- Apply agent eval prompts from YAML ---
    for eval_name, spec in catalog.items():
        if spec.get("eval_type") != "agent":
            continue

        rule_prompt = spec.get("rule_prompt", "").strip()
        if not rule_prompt:
            continue

        tmpl = EvalTemplate.no_workspace_objects.filter(
            name=eval_name, owner="system", deleted=False
        ).first()

        if not tmpl:
            stats["not_found"] += 1
            if dry_run:
                print(f"  NOT FOUND: {eval_name}")
            continue

        config = tmpl.config or {}
        current_rp = config.get("rule_prompt", "")

        if current_rp == rule_prompt and tmpl.criteria == rule_prompt:
            stats["already_ok"] += 1
            continue

        if dry_run:
            changed = "rule_prompt" if current_rp != rule_prompt else "criteria_sync"
            print(f"  AGENT UPDATE: {eval_name} ({changed})")
        else:
            config["rule_prompt"] = rule_prompt
            tmpl.config = config
            tmpl.criteria = rule_prompt
            updates.append(tmpl)

        stats["agent_updated"] += 1

    # --- Apply code eval Python code ---
    for eval_name, code_str in CODE_REGISTRY.items():
        tmpl = EvalTemplate.no_workspace_objects.filter(
            name=eval_name, owner="system", deleted=False
        ).first()

        if not tmpl:
            stats["not_found"] += 1
            if dry_run:
                print(f"  NOT FOUND (code): {eval_name}")
            continue

        config = tmpl.config or {}
        current_code = config.get("code", "")

        if current_code == code_str:
            stats["already_ok"] += 1
            continue

        if dry_run:
            print(f"  CODE UPDATE: {eval_name} ({len(code_str)} chars)")
        else:
            config["code"] = code_str
            config["function_eval"] = True
            tmpl.config = config
            if tmpl not in updates:
                updates.append(tmpl)

        stats["code_updated"] += 1

    if not dry_run and updates:
        batch_size = 50
        with transaction.atomic():
            for i in range(0, len(updates), batch_size):
                batch = updates[i : i + batch_size]
                EvalTemplate.no_workspace_objects.bulk_update(
                    batch, ["config", "criteria"], batch_size=batch_size
                )
        print(f"\nUpdated {len(updates)} templates")

    print(f"\n--- Stats ---")
    print(f"  Agent prompts updated: {stats['agent_updated']}")
    print(f"  Code evals updated:    {stats['code_updated']}")
    print(f"  Already OK:            {stats['already_ok']}")
    print(f"  Not found in DB:       {stats['not_found']}")

    if dry_run:
        print(f"\n  *** DRY RUN ***")
