"""
Unit tests for _setup_eval_params in PromptTemplateViewSet.

Tests cover the fix for multi-modal (image/audio) data extraction
when running evaluations in the workbench. Previously, image and audio
data from multi-modal messages was discarded, causing evaluators to
receive text content instead of media data.

Fixes: CORE-BACKEND-Z4F / TH-1571

Run with: set -a && source .env.test.local && set +a && pytest model_hub/tests/test_setup_eval_params.py -v
"""

import pytest

from model_hub.views.prompt_template import PromptTemplateViewSet


@pytest.mark.unit
class TestSetupEvalParams:
    """Tests for PromptTemplateViewSet._setup_eval_params"""

    def setup_method(self):
        self.viewset = PromptTemplateViewSet()

    # ── Text-only (existing behaviour) ──────────────────────────

    def test_input_prompt_returns_user_text(self):
        chat_history = [
            {"role": "user", "content": "What is AI?"},
            {"role": "assistant", "content": "AI is artificial intelligence."},
        ]
        mappings = {"query": "input_prompt"}
        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
        )
        assert result["query"] == "What is AI?"

    def test_output_prompt_returns_assistant_response(self):
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        mappings = {"output": "output_prompt"}
        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
        )
        assert result["output"] == "Hi there!"

    def test_variable_mapping_returns_variable_value(self):
        chat_history = [
            {"role": "user", "content": "Check this"},
            {"role": "assistant", "content": "Done"},
        ]
        mappings = {"context": "my_var"}
        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={"my_var": "some context value"},
        )
        assert result["context"] == "some context value"

    def test_missing_variable_returns_empty_string(self):
        chat_history = [
            {"role": "user", "content": "Check"},
            {"role": "assistant", "content": "Done"},
        ]
        mappings = {"context": "nonexistent_var"}
        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
        )
        assert result["context"] == ""

    def test_multiple_user_messages_joined(self):
        chat_history = [
            {"role": "user", "content": "First message"},
            {"role": "user", "content": "Second message"},
            {"role": "assistant", "content": "Response"},
        ]
        mappings = {"query": "input_prompt"}
        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
        )
        assert result["query"] == "First message\nSecond message"

    # ── Image params (new behaviour) ────────────────────────────

    def test_image_key_with_input_images_returns_image_url(self):
        """When 'image' is mapped to input_prompt and input_images exist,
        the image URL should be used instead of text content."""
        chat_history = [
            {"role": "user", "content": "what is this image"},
            {"role": "assistant", "content": "It is a logo."},
        ]
        mappings = {"image": "input_prompt"}
        input_images = ["data:image/png;base64,iVBORw0KGgoAAAANS..."]

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
            input_images=input_images,
        )
        assert result["image"] == "data:image/png;base64,iVBORw0KGgoAAAANS..."

    def test_input_image_key_with_input_images_returns_image_url(self):
        """Same as above but for the 'input_image' key name."""
        chat_history = [
            {"role": "user", "content": "describe this"},
            {"role": "assistant", "content": "A photo."},
        ]
        mappings = {"input_image": "input_prompt"}
        input_images = ["https://example.com/photo.jpg"]

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
            input_images=input_images,
        )
        assert result["input_image"] == "https://example.com/photo.jpg"

    def test_image_key_without_input_images_falls_back_to_text(self):
        """When no images are extracted, even image keys fall back to text."""
        chat_history = [
            {"role": "user", "content": "some text"},
            {"role": "assistant", "content": "response"},
        ]
        mappings = {"image": "input_prompt"}

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
            input_images=[],
        )
        assert result["image"] == "some text"

    def test_non_image_key_ignores_input_images(self):
        """A non-image key mapped to input_prompt should still get text,
        even when input_images are available."""
        chat_history = [
            {"role": "user", "content": "Evaluate this"},
            {"role": "assistant", "content": "OK"},
        ]
        mappings = {"query": "input_prompt"}
        input_images = ["https://example.com/img.png"]

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
            input_images=input_images,
        )
        assert result["query"] == "Evaluate this"

    # ── Audio params (new behaviour) ────────────────────────────

    def test_audio_key_with_input_audios_returns_audio_url(self):
        """When 'audio' is mapped to input_prompt and input_audios exist,
        the audio URL should be used instead of text content."""
        chat_history = [
            {"role": "user", "content": "transcribe this audio"},
            {"role": "assistant", "content": "Hello world."},
        ]
        mappings = {"audio": "input_prompt"}
        input_audios = ["https://example.com/audio.wav"]

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
            input_audios=input_audios,
        )
        assert result["audio"] == "https://example.com/audio.wav"

    def test_input_audio_key_with_input_audios_returns_audio_url(self):
        chat_history = [
            {"role": "user", "content": "check quality"},
            {"role": "assistant", "content": "Good quality."},
        ]
        mappings = {"input_audio": "input_prompt"}
        input_audios = ["data:audio/wav;base64,UklGR..."]

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
            input_audios=input_audios,
        )
        assert result["input_audio"] == "data:audio/wav;base64,UklGR..."

    def test_generated_audio_key_with_input_audios_returns_audio_url(self):
        chat_history = [
            {"role": "user", "content": "evaluate tts"},
            {"role": "assistant", "content": "Done."},
        ]
        mappings = {"generated_audio": "input_prompt"}
        input_audios = ["https://example.com/tts_output.mp3"]

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
            input_audios=input_audios,
        )
        assert result["generated_audio"] == "https://example.com/tts_output.mp3"

    def test_audio_key_without_input_audios_falls_back_to_text(self):
        chat_history = [
            {"role": "user", "content": "some text"},
            {"role": "assistant", "content": "response"},
        ]
        mappings = {"audio": "input_prompt"}

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
            input_audios=[],
        )
        assert result["audio"] == "some text"

    def test_non_audio_key_ignores_input_audios(self):
        chat_history = [
            {"role": "user", "content": "Check this"},
            {"role": "assistant", "content": "OK"},
        ]
        mappings = {"query": "input_prompt"}
        input_audios = ["https://example.com/audio.wav"]

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
            input_audios=input_audios,
        )
        assert result["query"] == "Check this"

    # ── Mixed mappings ──────────────────────────────────────────

    def test_mixed_mappings_with_image_and_text(self):
        """An image eval that needs both image data and text output."""
        chat_history = [
            {"role": "user", "content": "what is this image"},
            {"role": "assistant", "content": "It shows a logo."},
        ]
        mappings = {
            "image": "input_prompt",
            "output": "output_prompt",
        }
        input_images = ["https://bucket.s3.amazonaws.com/img.png"]

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
            input_images=input_images,
        )
        assert result["image"] == "https://bucket.s3.amazonaws.com/img.png"
        assert result["output"] == "It shows a logo."

    def test_mixed_mappings_with_audio_and_variable(self):
        """An audio eval that needs audio data and a variable."""
        chat_history = [
            {"role": "user", "content": "transcribe"},
            {"role": "assistant", "content": "Hello world"},
        ]
        mappings = {
            "audio": "input_prompt",
            "generated_transcript": "output_prompt",
        }
        input_audios = ["https://example.com/recording.wav"]

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
            input_audios=input_audios,
        )
        assert result["audio"] == "https://example.com/recording.wav"
        assert result["generated_transcript"] == "Hello world"

    def test_no_media_params_passed_defaults_to_none(self):
        """When input_images and input_audios are not passed, it defaults gracefully."""
        chat_history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        mappings = {"query": "input_prompt"}

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
        )
        assert result["query"] == "hello"

    def test_image_key_prefers_first_image(self):
        """When multiple images exist, the first one is used."""
        chat_history = [
            {"role": "user", "content": "compare these"},
            {"role": "assistant", "content": "They differ."},
        ]
        mappings = {"image": "input_prompt"}
        input_images = [
            "https://example.com/first.png",
            "https://example.com/second.png",
        ]

        result = self.viewset._setup_eval_params(
            chat_history=chat_history,
            mappings=mappings,
            variable_combination={},
            input_images=input_images,
        )
        assert result["image"] == "https://example.com/first.png"
