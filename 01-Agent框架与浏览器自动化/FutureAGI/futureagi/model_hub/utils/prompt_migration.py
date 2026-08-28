"""
Utility for converting between flat eval template config and structured prompt_messages format.

Used by:
- Data migration to backfill v0 versions from existing templates
- insert_evals_template to create v0 for system evals
- EvaluationRunner to convert version prompt_messages back to flat config for execution
"""


def config_to_prompt_messages(config, criteria=None, eval_type_id=None):
    """
    Convert existing flat eval template config to structured prompt_messages array.

    Args:
        config: dict - the eval template's config JSON
        criteria: str or None - the eval template's criteria field
        eval_type_id: str or None - from config.get('eval_type_id')

    Returns:
        list[dict]: Array of {role, name, content} message dicts.
    """
    if not config:
        config = {}

    if eval_type_id is None:
        eval_type_id = config.get("eval_type_id", "")

    # Function evals have no LLM prompt
    if config.get("function_eval"):
        return []

    messages = []

    if eval_type_id == "CustomPromptEvaluator":
        # User LLM-as-judge evals
        system_prompt = config.get("system_prompt", "")
        rule_prompt = config.get("rule_prompt", "") or criteria or ""

        if system_prompt and system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "name": "system_prompt",
                    "content": system_prompt.strip(),
                }
            )
        if rule_prompt and rule_prompt.strip():
            messages.append(
                {
                    "role": "user",
                    "name": "eval_prompt",
                    "content": rule_prompt.strip(),
                }
            )
    else:
        # System evals (DeterministicEvaluator, RankingEvaluator, etc.)
        effective_criteria = criteria or config.get("criteria", "")
        if effective_criteria and effective_criteria.strip():
            content = effective_criteria.strip()
            # Include required_keys as named variable placeholders so users
            # can see exactly which variables the eval expects.
            required_keys = config.get("required_keys", [])
            if required_keys:
                var_parts = " ".join(f"{{{{{key}}}}}" for key in required_keys)
                content = f"{content}\n\n{var_parts}"
            messages.append(
                {
                    "role": "system",
                    "name": "criteria",
                    "content": content,
                }
            )

    return messages


def prompt_messages_to_flat_config(prompt_messages):
    """
    Convert structured prompt_messages back to flat config fields.
    Used by the eval runner for backward-compatible execution.

    Args:
        prompt_messages: list[dict] - array of {role, name, content}

    Returns:
        dict with keys: system_prompt, rule_prompt, criteria (any can be None)
    """
    result = {
        "system_prompt": None,
        "rule_prompt": None,
        "criteria": None,
    }

    if not prompt_messages:
        return result

    for msg in prompt_messages:
        role = msg.get("role", "")
        name = msg.get("name", "")
        content = msg.get("content", "")

        # Prioritize name-based matching over role-based so that
        # {role: "system", name: "criteria"} maps to criteria, not system_prompt.
        if name == "criteria" and not result["criteria"]:
            result["criteria"] = content
        elif name == "eval_prompt" and not result["rule_prompt"]:
            result["rule_prompt"] = content
        elif role == "system" and not result["system_prompt"]:
            result["system_prompt"] = content

    # If we have a rule_prompt but no criteria, use rule_prompt as criteria too
    if result["rule_prompt"] and not result["criteria"]:
        result["criteria"] = result["rule_prompt"]

    return result
