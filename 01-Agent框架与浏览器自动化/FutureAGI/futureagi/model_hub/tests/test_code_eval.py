"""
Tests for Phase 8: Code Evals.
"""

import pytest

from model_hub.models.evals_metric import EvalTemplate


@pytest.mark.e2e
@pytest.mark.django_db
class TestCodeEvalCreateAPI:
    url = "/model-hub/eval-templates/create-v2/"

    def test_create_code_eval(self, auth_client):
        response = auth_client.post(
            self.url,
            {
                "name": "my-code-eval",
                "eval_type": "code",
                "code": "def evaluate(output, expected):\n    return output == expected",
                "code_language": "python",
                "output_type": "pass_fail",
            },
            format="json",
        )
        assert response.status_code == 200
        result = response.data["result"]
        assert result["name"] == "my-code-eval"

        template = EvalTemplate.objects.get(id=result["id"])
        assert template.config["eval_type_id"] == "CustomCodeEval"
        assert "code" in template.config
        assert template.config["language"] == "python"

    def test_create_code_eval_without_code_rejected(self, auth_client):
        response = auth_client.post(
            self.url,
            {
                "name": "no-code-eval",
                "eval_type": "code",
                "output_type": "pass_fail",
            },
            format="json",
        )
        assert response.status_code == 400
        assert "code" in str(response.data["result"]).lower()

    def test_create_code_eval_javascript(self, auth_client):
        response = auth_client.post(
            self.url,
            {
                "name": "js-code-eval",
                "eval_type": "code",
                "code": "function evaluate(output, expected) { return output === expected; }",
                "code_language": "javascript",
                "output_type": "pass_fail",
            },
            format="json",
        )
        assert response.status_code == 200
        template = EvalTemplate.objects.get(id=response.data["result"]["id"])
        assert template.config["language"] == "javascript"

    def test_create_llm_eval_without_instructions_rejected(self, auth_client):
        """LLM evals still require instructions."""
        response = auth_client.post(
            self.url,
            {
                "name": "no-instructions",
                "eval_type": "llm",
                "output_type": "pass_fail",
            },
            format="json",
        )
        assert response.status_code == 400
