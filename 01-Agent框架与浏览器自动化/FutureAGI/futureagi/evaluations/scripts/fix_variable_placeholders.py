"""
Fix {{variable_N}} placeholders in rule_prompt.

DeterministicEvaluator used {{variable_1}}, {{variable_2}} etc. mapped to required_keys by index.
AgentEvaluator expects {{actual_key_name}} like {{output}}, {{input}}.

This script converts:
  {{variable_1}} → {{first_required_key}}
  {{variable_2}} → {{second_required_key}}
  etc.

Also syncs rule_prompt back to the criteria field for frontend display.

Usage:
    python manage.py shell -c "from evaluations.scripts.fix_variable_placeholders import run; run('--dry-run')"
    python manage.py shell -c "from evaluations.scripts.fix_variable_placeholders import run; run()"
"""

import re

import structlog

logger = structlog.get_logger(__name__)


def run(*args):
    dry_run = "--dry-run" in args

    from django.db import transaction

    from model_hub.models.evals_metric import EvalTemplate

    templates = EvalTemplate.no_workspace_objects.filter(deleted=False)
    total = templates.count()

    stats = {"fixed_vars": 0, "synced_criteria": 0, "already_ok": 0, "skipped": 0}
    updates = []

    for tmpl in templates.iterator():
        config = tmpl.config or {}
        rule_prompt = config.get("rule_prompt", "")
        criteria = tmpl.criteria or ""
        required_keys = config.get("required_keys", [])

        if isinstance(rule_prompt, dict):
            rule_prompt = ""
        if isinstance(criteria, dict):
            criteria = ""

        # Use rule_prompt if available, else criteria
        text = rule_prompt or criteria
        if not text:
            stats["skipped"] += 1
            continue

        changed = False
        new_text = text

        # Replace {{variable_N}} with actual key names
        if "{{variable" in new_text and required_keys:
            for i, key in enumerate(required_keys):
                old_var = f"{{{{variable_{i + 1}}}}}"
                new_var = f"{{{{{key}}}}}"
                if old_var in new_text:
                    new_text = new_text.replace(old_var, new_var)
                    changed = True

        if not changed:
            # Check if criteria needs syncing to rule_prompt
            if rule_prompt and not criteria:
                tmpl.criteria = rule_prompt
                stats["synced_criteria"] += 1
                updates.append(tmpl)
            else:
                stats["already_ok"] += 1
            continue

        stats["fixed_vars"] += 1

        if dry_run:
            print(f"\n  [{tmpl.id}] {tmpl.name}")
            print(f"    keys: {required_keys}")
            print(f"    before: {text[:100]}")
            print(f"    after:  {new_text[:100]}")
        else:
            config["rule_prompt"] = new_text
            tmpl.config = config
            tmpl.criteria = new_text  # sync to criteria for frontend
            updates.append(tmpl)

    if not dry_run and updates:
        batch_size = 100
        with transaction.atomic():
            for i in range(0, len(updates), batch_size):
                batch = updates[i : i + batch_size]
                EvalTemplate.no_workspace_objects.bulk_update(
                    batch, ["config", "criteria"], batch_size=batch_size
                )
        print(f"\nUpdated {len(updates)} templates")

    print(f"\n--- Stats ---")
    print(f"  Total:           {total}")
    print(f"  Fixed vars:      {stats['fixed_vars']}")
    print(f"  Synced criteria: {stats['synced_criteria']}")
    print(f"  Already OK:      {stats['already_ok']}")
    print(f"  Skipped (empty): {stats['skipped']}")

    if dry_run:
        print(f"\n  *** DRY RUN ***")
