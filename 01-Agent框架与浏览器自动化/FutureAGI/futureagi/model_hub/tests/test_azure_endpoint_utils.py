from model_hub.utils.azure_endpoints import normalize_azure_custom_model_config


def test_normalize_azure_legacy_full_url_extracts_base_and_version():
    config = normalize_azure_custom_model_config(
        {
            "api_base": "https://res.openai.azure.com/openai/deployments/my-deploy/chat/completions?api-version=2024-10-21",
            "api_key": "k",
        }
    )

    assert config["api_base"] == "https://res.openai.azure.com"
    assert config["api_version"] == "2024-10-21"
    assert config["azure_endpoint_type"] == "legacy"


def test_normalize_azure_foundry_full_url_extracts_base():
    config = normalize_azure_custom_model_config(
        {
            "api_base": "https://res.services.ai.azure.com/models/chat/completions?api-version=2024-05-01-preview",
            "api_key": "k",
        }
    )

    assert config["api_base"] == "https://res.services.ai.azure.com"
    assert config["api_version"] == "2024-05-01-preview"
    assert config["azure_endpoint_type"] == "foundry"


def test_normalize_keeps_explicit_endpoint_type():
    config = normalize_azure_custom_model_config(
        {
            "api_base": "https://res.openai.azure.com",
            "api_version": "2024-10-21",
            "api_key": "k",
            "azure_endpoint_type": "legacy",
        }
    )

    assert config["azure_endpoint_type"] == "legacy"


def test_normalize_legacy_url_without_scheme():
    config = normalize_azure_custom_model_config(
        {
            "api_base": "res.openai.azure.com/openai/deployments/my-deploy",
            "api_key": "k",
        }
    )

    assert config["api_base"] == "https://res.openai.azure.com"
    assert config["azure_endpoint_type"] == "legacy"


def test_normalize_foundry_url_without_scheme():
    config = normalize_azure_custom_model_config(
        {
            "api_base": "res.services.ai.azure.com/models/chat/completions",
            "api_key": "k",
        }
    )

    assert config["api_base"] == "https://res.services.ai.azure.com"
    assert config["azure_endpoint_type"] == "foundry"


def test_normalize_v1_endpoint_sets_api_version():
    config = normalize_azure_custom_model_config(
        {
            "api_base": "https://res.openai.azure.com/openai/v1/",
            "api_key": "k",
        }
    )

    assert config["api_base"] == "https://res.openai.azure.com"
    assert config["api_version"] == "v1"
    assert config["azure_endpoint_type"] == "legacy"


def test_normalize_foundry_project_scoped_keeps_path():
    config = normalize_azure_custom_model_config(
        {
            "api_base": "https://res.services.ai.azure.com/api/projects/proj-default",
            "api_key": "k",
        }
    )

    assert (
        config["api_base"]
        == "https://res.services.ai.azure.com/api/projects/proj-default"
    )
    assert config["azure_endpoint_type"] == "foundry"


def test_normalize_cognitiveservices_detected_as_foundry():
    config = normalize_azure_custom_model_config(
        {
            "api_base": "https://res.cognitiveservices.azure.com/",
            "api_key": "k",
        }
    )

    assert config["api_base"] == "https://res.cognitiveservices.azure.com"
    assert config["azure_endpoint_type"] == "foundry"


def test_normalize_unknown_url_defaults_to_foundry():
    config = normalize_azure_custom_model_config(
        {
            "api_base": "https://my-proxy.example.com/v1",
            "api_key": "k",
        }
    )

    assert config["api_base"] == "https://my-proxy.example.com"
    assert config["azure_endpoint_type"] == "foundry"


def test_normalize_foundry_anthropic_base_keeps_path():
    config = normalize_azure_custom_model_config(
        {
            "api_base": "https://res.services.ai.azure.com/anthropic",
            "api_key": "k",
        }
    )

    assert config["api_base"] == "https://res.services.ai.azure.com/anthropic"
    assert config["azure_endpoint_type"] == "foundry"
