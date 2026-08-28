# Run Prompt Tests

Comprehensive test suite for the RunPrompt class and LiteLLM integration.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                   # Test fixtures and configuration
├── test_run_prompt.py            # Unit tests and basic integration tests
├── test_live_all_providers.py    # Comprehensive live tests for all providers
└── README.md                     # This file
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
Tests that don't require API keys or external services. These use mocks for all external calls.

- **TestRunPromptInitialization** - Tests for class initialization
- **TestPayloadCreation** - Tests for payload generation
- **TestReasoningModelDetection** - Tests for reasoning model handling
- **TestLiteLLMModelManager** - Tests for model manager class
- **TestRetryLogic** - Tests for retry mechanism
- **TestMessageHandling** - Tests for message processing
- **TestConfigurationVariations** - Tests for parameter combinations
- **TestAvailableModels** - Tests for model registry

### Integration Tests (`@pytest.mark.integration`, `@pytest.mark.live_llm`)
Tests that make actual API calls. Require corresponding API keys.

#### Basic Integration Tests (test_run_prompt.py)
- **TestOpenAILiveIntegration** - OpenAI models (GPT-4o, etc.)
- **TestAnthropicLiveIntegration** - Anthropic models (Claude)
- **TestGroqLiveIntegration** - Groq models (Llama)
- **TestXAILiveIntegration** - xAI models (Grok)
- **TestPerplexityLiveIntegration** - Perplexity models (Sonar)

#### Comprehensive Live Tests (test_live_all_providers.py)
- **TestOpenAILiveAllModels** - All 85 OpenAI models with all parameter variations
- **TestAnthropicLiveAllModels** - All 9 Anthropic models with all parameter variations
- **TestGroqLiveAllModels** - All 23 Groq models with all parameter variations
- **TestXAILiveAllModels** - All 6 xAI/Grok models with all parameter variations
- **TestPerplexityLiveAllModels** - All 20 Perplexity models with all parameter variations
- **TestOpenRouterLiveAllModels** - All 40 OpenRouter models with all parameter variations
- **TestCrossProviderParameterConsistency** - Cross-provider consistency tests
- **TestErrorHandling** - Error handling tests

### Stress Tests (`@pytest.mark.slow`)
Performance and stress tests for edge cases.

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install pytest pytest-cov pytest-xdist
```

2. Set up environment variables (copy from `.env` to `.env.test.local` if needed):
```bash
# Required for unit tests: None (all mocked)

# Required for live tests:
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GROQ_API_KEY=gsk_...
export XAI_API_KEY=xai-...
export PERPLEXITY_API_KEY=pplx-...
export OPENROUTER_API_KEY=sk-or-...

# Optional (tests will skip if not present):
export GEMINI_API_KEY=...
export AZURE_API_KEY=...
export COHERE_API_KEY=...
export MISTRAL_API_KEY=...
```

### Run All Tests
```bash
# From core-backend directory
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v
```

### Run Unit Tests Only (No API Keys Required)
```bash
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v -m unit
```

### Run Live LLM Tests (Requires API Keys)
```bash
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v -m live_llm
```

### Run Specific Provider Tests
```bash
# OpenAI tests only
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v -k "openai"

# Anthropic tests only
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v -k "anthropic"

# Groq tests only
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v -k "groq"

# xAI tests only
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v -k "xai"

# Perplexity tests only
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v -k "perplexity"

# OpenRouter tests only
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v -k "openrouter"

# Reasoning model tests
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v -k "reasoning"
```

### Run Comprehensive Provider Tests
```bash
# All comprehensive live tests
python -m pytest agentic_eval/core_evals/run_prompt/tests/test_live_all_providers.py -v

# Temperature variations only
python -m pytest agentic_eval/core_evals/run_prompt/tests/test_live_all_providers.py -v -k "temperature"

# Max tokens variations only
python -m pytest agentic_eval/core_evals/run_prompt/tests/test_live_all_providers.py -v -k "max_tokens"

# Combined parameter tests
python -m pytest agentic_eval/core_evals/run_prompt/tests/test_live_all_providers.py -v -k "combined"
```

### Run With Coverage
```bash
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v --cov=agentic_eval.core_evals.run_prompt --cov-report=html
```

### Run Parallel Tests
```bash
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v -n auto
```

## Test Markers

| Marker | Description |
|--------|-------------|
| `@pytest.mark.unit` | Unit tests (no external dependencies) |
| `@pytest.mark.integration` | Integration tests (may need services) |
| `@pytest.mark.live_llm` | Tests that call live LLM APIs |
| `@pytest.mark.external` | Tests that require external network |
| `@pytest.mark.slow` | Slow-running tests |

## API Keys Status

The test suite checks for the following API keys:

| Provider | Environment Variable | Status |
|----------|---------------------|--------|
| OpenAI | `OPENAI_API_KEY` | Required for OpenAI live tests |
| Anthropic | `ANTHROPIC_API_KEY` | Required for Anthropic live tests |
| Groq | `GROQ_API_KEY` | Required for Groq live tests |
| xAI | `XAI_API_KEY` | Required for xAI live tests |
| Perplexity | `PERPLEXITY_API_KEY` | Required for Perplexity live tests |
| OpenRouter | `OPENROUTER_API_KEY` | Required for OpenRouter live tests |
| Gemini | `GEMINI_API_KEY` | Optional (tests skip if missing) |
| Azure | `AZURE_API_KEY` | Optional (tests skip if missing) |
| Cohere | `COHERE_API_KEY` | Optional (tests skip if missing) |
| Mistral | `MISTRAL_API_KEY` | Optional (tests skip if missing) |

## Models Tested

### OpenAI Models (85 models)

#### Chat Models
- gpt-4o, gpt-4o-mini, gpt-4o-2024-05-13, gpt-4o-2024-08-06
- chatgpt-4o-latest
- gpt-4, gpt-4.1, gpt-4-turbo, gpt-4-turbo-preview
- gpt-4-0613, gpt-4-1106-preview, gpt-4-0125-preview
- gpt-3.5-turbo, gpt-3.5-turbo-1106, gpt-3.5-turbo-0125, gpt-3.5-turbo-16k

#### Reasoning Models (Special Parameter Handling)
- o1, o1-mini, o1-preview (and dated versions)
- o3, o3-mini, o3-pro (and dated versions)
- o4-mini
- gpt-5 series (gpt-5, gpt-5-mini, gpt-5-nano, gpt-5-pro, gpt-5-chat-latest)
- gpt-5.1 series
- gpt-5.2 series

#### Azure OpenAI Models
- azure/gpt-4o, azure/gpt-4o-mini
- azure/gpt-4-turbo, azure/gpt-4
- azure/gpt-35-turbo series
- Azure reasoning: azure/o1, azure/o1-mini, azure/o3-mini

### Anthropic Models (9 models)
- claude-3-5-haiku-20241022, claude-3-haiku-20240307
- claude-3-7-sonnet-20250219
- claude-opus-4-20250514, claude-sonnet-4-20250514
- claude-haiku-4-5-20251001
- claude-opus-4-1-20250805, claude-opus-4-5-20251101
- claude-sonnet-4-5-20250929

### Groq Models (23 models)
- groq/llama3-8b-8192, groq/llama3-70b-8192
- groq/llama-3.3-70b-versatile, groq/llama-3.1-8b-instant
- groq/gemma2-9b-it
- groq/meta-llama/llama-4-scout-17b-16e-instruct
- groq/qwen/qwen3-32b
- groq/compound-beta, groq/compound-beta-mini
- groq/deepseek-r1-distill-llama-70b
- And more...

### xAI/Grok Models (6 models)
- xai/grok-beta, xai/grok-vision-beta
- xai/grok-2-latest, xai/grok-2-vision-latest
- xai/grok-2-1212, xai/grok-2-vision-1212

### Perplexity Models (20 models)
- perplexity/llama-3.1-70b-instruct, perplexity/llama-3.1-8b-instruct
- perplexity/llama-3.1-sonar-* series (online and chat variants)
- perplexity/sonar-small-chat, perplexity/sonar-medium-chat
- perplexity/sonar-small-online, perplexity/sonar-medium-online
- perplexity/codellama-34b-instruct, perplexity/codellama-70b-instruct
- perplexity/pplx-* series
- perplexity/mixtral-8x7b-instruct

### OpenRouter Models (40 models)
- openrouter/openai/gpt-4o, gpt-4, gpt-3.5-turbo
- openrouter/anthropic/claude-3.5-sonnet, claude-3-opus, claude-3-haiku
- openrouter/google/gemini-pro-1.5, gemini-pro-vision
- openrouter/mistralai/mistral-large, mixtral-8x22b-instruct
- openrouter/meta-llama/llama-3-70b-instruct, llama-3-8b-instruct
- openrouter/cohere/command-r-plus
- openrouter/deepseek/deepseek-coder
- And many more...

## Parameters Tested

Each provider is tested with various combinations of:

| Parameter | Values Tested |
|-----------|---------------|
| Temperature | 0.0, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0 |
| Max Tokens | 50, 100, 250, 500, 1000, 2000, 4000 |
| Top P | 0.1, 0.5, 0.7, 0.9, 0.95, 1.0 |
| Frequency Penalty | 0.0, 0.5, 1.0, 1.5, 2.0 |
| Presence Penalty | 0.0, 0.5, 1.0, 1.5, 2.0 |
| Response Format | text, json_object |
| Tools/Function Calling | enabled/disabled |

## Test Count Summary

| Provider | Models | Parameter Tests | Total Tests |
|----------|--------|-----------------|-------------|
| OpenAI | 30+ | 7 parameters x variations | ~200+ |
| Anthropic | 9 | 4 parameters x variations | ~50+ |
| Groq | 16 | 4 parameters x variations | ~60+ |
| xAI | 6 | 5 parameters x variations | ~50+ |
| Perplexity | 20 | 4 parameters x variations | ~60+ |
| OpenRouter | 40 | 5 parameters x variations | ~100+ |
| **Total** | **121+** | - | **~520+** |

## Troubleshooting

### Tests Skip Due to Missing API Keys
Tests automatically skip if the required API key is not set. Check the test output for skip messages.

### Import Errors
Make sure you're running from the `core-backend` directory and have activated your virtual environment:
```bash
cd /path/to/core-backend
source .venv/bin/activate
```

### Database Connection Errors
Unit tests don't require database - they mock all DB calls. For integration tests, ensure test database is running:
```bash
docker compose -f docker-compose.test.yml up -d
```

### Rate Limiting
Live LLM tests may hit rate limits. Wait a few minutes and retry, or use smaller test batches:
```bash
python -m pytest agentic_eval/core_evals/run_prompt/tests/ -v -m live_llm --maxfail=3
```

### NumPy Version Conflict
If you see NumPy compatibility errors, ensure you're using the correct virtual environment:
```bash
# Deactivate any conda environment
conda deactivate

# Use the project's venv
source .venv/bin/activate
```

## Adding New Tests

1. Add fixtures to `conftest.py` if needed
2. Add test class to `test_run_prompt.py` (basic tests) or `test_live_all_providers.py` (comprehensive tests)
3. Use appropriate markers (`@pytest.mark.unit`, `@pytest.mark.live_llm`, etc.)
4. For new providers, add API key check in `conftest.py`

Example:
```python
@pytest.mark.integration
@pytest.mark.live_llm
class TestNewProviderIntegration:
    @pytest.fixture(autouse=True)
    def setup(self, api_keys):
        if not api_keys.get("new_provider"):
            pytest.skip("NEW_PROVIDER_API_KEY not configured")

    def test_basic_chat(self, ...):
        # Test implementation
        pass
```
