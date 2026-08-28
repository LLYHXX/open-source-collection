from agentcc.services.log_ingestion import _compute_cost


def test_compute_cost_uses_tts_input_characters():
    entry = {
        "model": "tts-1",
        "metadata": {
            "input_characters": "1000",
        },
    }

    assert _compute_cost(entry) == 0.015


def test_compute_cost_uses_stt_audio_seconds():
    entry = {
        "model": "whisper-1",
        "metadata": {
            "audio_seconds": "30",
        },
    }

    assert _compute_cost(entry) == 0.003


def test_compute_cost_does_not_charge_for_zero_generated_images(monkeypatch):
    captured = {}

    def fake_get_model_info(model):
        return {"mode": "image_generation"}

    def fake_calculate_total_cost(model, usage):
        captured.update(usage)
        return {"total_cost": 0}

    monkeypatch.setattr(
        "agentic_eval.core_evals.run_prompt.model_pricing.get_model_info",
        fake_get_model_info,
    )
    monkeypatch.setattr(
        "agentic_eval.core_evals.fi_utils.token_count_helper.calculate_total_cost",
        fake_calculate_total_cost,
    )

    entry = {
        "model": "gpt-image-1",
        "metadata": {
            "images_generated": 0,
        },
    }

    _compute_cost(entry)

    assert captured["images_generated"] == 0
