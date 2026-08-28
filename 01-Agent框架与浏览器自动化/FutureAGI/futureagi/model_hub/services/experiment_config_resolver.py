"""
Bridge between new ExperimentPromptConfig/ExperimentAgentConfig models
and the existing execution engine.

resolve_prompt_config() produces a dict that the execution engine can
consume directly — one model per config, no inner loop needed.
"""


def resolve_prompt_config(exp_prompt_config):
    """
    Convert an ExperimentPromptConfig record into the dict shape expected
    by the existing experiment execution engine.

    Works for ALL experiment types (llm, tts, stt, image).
    - LLM: messages come LOCKED from prompt_version.prompt_config_snapshot
    - TTS/STT/Image: messages stored inline on exp_prompt_config.messages

    Args:
        exp_prompt_config: ExperimentPromptConfig instance.

    Returns:
        dict with snake_case keys matching the backend execution engine.
    """
    config = {
        "name": exp_prompt_config.name,
        "messages": exp_prompt_config.get_messages(),
        "model": exp_prompt_config.model,
        "model_display_name": exp_prompt_config.model_display_name,
        "model_config": exp_prompt_config.model_config,
        "model_params": exp_prompt_config.model_params,
        "configuration": exp_prompt_config.configuration,
        "output_format": exp_prompt_config.output_format,
    }

    # STT-specific
    if exp_prompt_config.voice_input_column_id:
        config["voice_input_column"] = str(exp_prompt_config.voice_input_column_id)

    return config


def resolve_agent_config(exp_agent_config):
    """
    Convert an ExperimentAgentConfig record into a dict for agent execution.

    No configuration_snapshot needed — GraphVersion is immutable by design.
    The workflow passes graph_version_id directly to ExecuteGraphInput.

    Args:
        exp_agent_config: ExperimentAgentConfig instance.

    Returns:
        dict with keys: name, graph_id, graph_version_id, config_type.
    """
    return {
        "name": exp_agent_config.name,
        "graph_id": str(exp_agent_config.graph_id),
        "graph_version_id": str(exp_agent_config.graph_version_id),
        "config_type": "agent",
    }
