from agent_playground.templates._registry import TemplateDefinition, register_template

LLM_PROMPT_TEMPLATE: TemplateDefinition = {
    "name": "llm_prompt",
    "display_name": "LLM Prompt",
    "description": (
        "Run a prompt against an LLM. All config (model, messages, parameters) comes "
        "from the linked PromptVersion via PromptTemplateNode. Input ports are dynamic "
        "— auto-generated from variables in the prompt version."
    ),
    "icon": None,
    "categories": ["llm", "ai", "prompt"],
    "input_definition": [],
    "output_definition": [
        {
            "key": "response",
            "data_schema": {},
            "schema_source": "prompt_version",
        }
    ],
    "input_mode": "dynamic",
    "output_mode": "strict",
    "config_schema": {},
}

register_template(LLM_PROMPT_TEMPLATE)
