"""
RunPrompt Handlers - Clean handler architecture for model execution.

This package provides a Strategy Pattern implementation for handling different
model types (LLM, TTS, STT, Custom, Image, Video, Embeddings, etc.).

Public API:
    - ModelHandlerFactory: Create appropriate handler based on context
    - ModelHandlerContext: Immutable context data for handlers
    - HandlerResponse: Standardized response format
    - BaseModelHandler: Abstract base class for handlers

Example usage:
    ```python
    from agentic_eval.core_evals.run_prompt.runprompt_handlers import (
        ModelHandlerFactory,
        ModelHandlerContext,
    )

    # Create context from RunPrompt instance
    context = ModelHandlerContext.from_run_prompt(
        run_prompt_instance,
        template_id=template_id,
        version=version,
    )

    # Get appropriate handler
    handler = ModelHandlerFactory.create_handler(context)

    # Execute synchronously
    response = handler.execute_sync(streaming=False)

    # Convert to legacy format
    result, value_info = response.to_value_info()
    ```
"""

from .base_handler import (
    BaseModelHandler,
    HandlerResponse,
    ModelHandlerContext,
)
from .factory import ModelHandlerFactory
from .handlers import (
    LLMHandler,
    TTSHandler,
    STTHandler,
    CustomModelHandler,
    ImageHandler,
)

__all__ = [
    "BaseModelHandler",
    "HandlerResponse",
    "ModelHandlerContext",
    "ModelHandlerFactory",
    "LLMHandler",
    "TTSHandler",
    "STTHandler",
    "CustomModelHandler",
    "ImageHandler",
]
