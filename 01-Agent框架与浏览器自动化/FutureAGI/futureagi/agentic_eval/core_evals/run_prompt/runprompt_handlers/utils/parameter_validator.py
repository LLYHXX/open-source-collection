"""
Parameter validation for LLM API calls.

This module validates model parameters against provider/model-specific limits
BEFORE making API calls, preventing errors and providing clear feedback.

Key validations:
- max_tokens: Caps to model's max_output_tokens limit
- temperature: Validates range (0-2 typically, model-specific)
- top_p: Validates range (0-1)
- frequency_penalty/presence_penalty: Validates range (-2 to 2 for OpenAI)

Design decisions:
- Auto-cap values with warnings (fail-safe) rather than hard errors
- Use cached get_model_info() from model_pricing.py for performance
- Fallback to LiteLLM's model_cost dictionary if not in registry
- Log all adjustments for debugging and monitoring
- Conservative fallbacks when model info unavailable
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

import litellm
import structlog

from agentic_eval.core_evals.run_prompt.model_pricing import get_model_info

logger = structlog.get_logger(__name__)


@dataclass
class ValidationResult:
    """
    Result of parameter validation.

    Attributes:
        value: The validated/adjusted parameter value
        was_adjusted: Whether the value was modified
        original_value: Original value before adjustment (if adjusted)
        reason: Why the value was adjusted (if adjusted)
    """

    value: Any
    was_adjusted: bool = False
    original_value: Optional[Any] = None
    reason: Optional[str] = None


class ParametersValidator:
    """
    Validates and adjusts model parameters to provider/model limits.

    Uses cached get_model_info() from AVAILABLE_MODELS registry for performance,
    with fallback to LiteLLM's model_cost dictionary. Auto-caps values that
    exceed limits with warnings.

    Example:
        validator = ParametersValidator(model="gpt-4")
        result = validator.validate_max_tokens(16000)
        # result.value = 4096 (capped to GPT-4's limit)
        # result.was_adjusted = True
        # result.reason = "Exceeds model's max_tokens limit of 4096"
    """

    # Default limits when model info unavailable
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE_MIN = 0.0
    DEFAULT_TEMPERATURE_MAX = 2.0
    DEFAULT_TOP_P_MIN = 0.0
    DEFAULT_TOP_P_MAX = 1.0
    DEFAULT_PENALTY_MIN = -2.0
    DEFAULT_PENALTY_MAX = 2.0

    def __init__(self, model: str):
        """
        Initialize validator for a specific model.

        Args:
            model: Model name (e.g., "gpt-4", "claude-3-opus-20240229")
        """
        self.model = model
        self._model_info = self._get_model_info()

    def _get_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get model information using cached get_model_info().

        Uses the custom model registry (AVAILABLE_MODELS) first with fuzzy matching,
        then falls back to LiteLLM's model_cost dictionary.

        Returns:
            Model info dict or None if not found
        """
        try:
            # Try cached get_model_info() from model_pricing.py
            # This uses AVAILABLE_MODELS with fuzzy matching and is cached via @lru_cache
            model_info = get_model_info(self.model)
            if model_info:
                return model_info

            # Fallback to LiteLLM's model_cost dictionary
            if self.model in litellm.model_cost:
                return litellm.model_cost[self.model]

            # Try without provider prefix (e.g., "openai/gpt-4" -> "gpt-4")
            model_without_prefix = self.model.split("/")[-1]
            if model_without_prefix in litellm.model_cost:
                return litellm.model_cost[model_without_prefix]

            logger.debug(
                "model_info_not_found",
                model=self.model,
                message="Using default parameter limits",
            )
            return None

        except Exception as e:
            logger.warning(
                "model_info_retrieval_error",
                model=self.model,
                error=str(e),
                message="Using default parameter limits",
            )
            return None

    def validate_max_tokens(
        self, max_tokens: Optional[int], default: Optional[int] = None
    ) -> ValidationResult:
        """
        Validate and cap max_tokens to model's limit.

        Args:
            max_tokens: Requested max_tokens (None to skip validation)
            default: Default value if max_tokens is None (None to return None)

        Returns:
            ValidationResult with validated value (None if both max_tokens and default are None)

        Example:
            >>> validator = ParametersValidator("gpt-4")
            >>> result = validator.validate_max_tokens(16000)
            >>> result.value  # 4096 (capped to GPT-4's limit)
            >>> result.was_adjusted  # True
        """
        # If no value provided and no default, return None
        if max_tokens is None and default is None:
            return ValidationResult(value=None)

        # Use requested value or default
        desired_tokens = max_tokens if max_tokens is not None else default

        # Get model's max output tokens with multiple fallback strategies
        model_max = None

        # 1. Try custom model registry (AVAILABLE_MODELS via get_model_info)
        if self._model_info:
            # Check for 'max_tokens' field (used in AVAILABLE_MODELS)
            model_max = self._model_info.get("max_tokens")
            # Also check for 'max_output_tokens' (LiteLLM format)
            if model_max is None:
                model_max = self._model_info.get("max_output_tokens")

        # 2. Fallback to LiteLLM's get_max_tokens function
        if model_max is None:
            try:
                model_max = litellm.get_max_tokens(self.model)
            except Exception:
                pass

        # If no model limit found, use requested value (no capping)
        if model_max is None:
            logger.debug(
                "max_tokens_limit_unknown",
                model=self.model,
                using_value=desired_tokens,
                message="Model's max_tokens limit not found, using requested value",
            )
            return ValidationResult(value=desired_tokens)

        # Cap to model's limit if exceeded
        if desired_tokens > model_max:
            logger.warning(
                "max_tokens_exceeded_limit",
                model=self.model,
                requested=desired_tokens,
                model_limit=model_max,
                adjusted_to=model_max,
            )
            return ValidationResult(
                value=model_max,
                was_adjusted=True,
                original_value=desired_tokens,
                reason=f"Exceeds model's max_tokens limit of {model_max}",
            )

        return ValidationResult(value=desired_tokens)

    def validate_temperature(self, temperature: Optional[float]) -> ValidationResult:
        """
        Validate temperature parameter.

        Most models support 0.0 - 2.0 range. Some models (like o1) only support
        temperature=1 and this should be handled by drop_params.

        Args:
            temperature: Requested temperature (None for no validation)

        Returns:
            ValidationResult with validated value
        """
        if temperature is None:
            return ValidationResult(value=None)

        # Get model-specific temperature limits (future enhancement)
        # For now, use standard OpenAI range: 0.0 - 2.0
        min_temp = self.DEFAULT_TEMPERATURE_MIN
        max_temp = self.DEFAULT_TEMPERATURE_MAX

        # Cap to valid range
        if temperature < min_temp:
            logger.warning(
                "temperature_below_minimum",
                model=self.model,
                requested=temperature,
                minimum=min_temp,
                adjusted_to=min_temp,
            )
            return ValidationResult(
                value=min_temp,
                was_adjusted=True,
                original_value=temperature,
                reason=f"Below minimum of {min_temp}",
            )

        if temperature > max_temp:
            logger.warning(
                "temperature_above_maximum",
                model=self.model,
                requested=temperature,
                maximum=max_temp,
                adjusted_to=max_temp,
            )
            return ValidationResult(
                value=max_temp,
                was_adjusted=True,
                original_value=temperature,
                reason=f"Exceeds maximum of {max_temp}",
            )

        return ValidationResult(value=temperature)

    def validate_top_p(self, top_p: Optional[float]) -> ValidationResult:
        """
        Validate top_p parameter.

        Standard range is 0.0 - 1.0 for all providers.

        Args:
            top_p: Requested top_p (None for no validation)

        Returns:
            ValidationResult with validated value
        """
        if top_p is None:
            return ValidationResult(value=None)

        # Standard top_p range: 0.0 - 1.0
        min_top_p = self.DEFAULT_TOP_P_MIN
        max_top_p = self.DEFAULT_TOP_P_MAX

        # Cap to valid range
        if top_p < min_top_p:
            logger.warning(
                "top_p_below_minimum",
                model=self.model,
                requested=top_p,
                minimum=min_top_p,
                adjusted_to=min_top_p,
            )
            return ValidationResult(
                value=min_top_p,
                was_adjusted=True,
                original_value=top_p,
                reason=f"Below minimum of {min_top_p}",
            )

        if top_p > max_top_p:
            logger.warning(
                "top_p_above_maximum",
                model=self.model,
                requested=top_p,
                maximum=max_top_p,
                adjusted_to=max_top_p,
            )
            return ValidationResult(
                value=max_top_p,
                was_adjusted=True,
                original_value=top_p,
                reason=f"Exceeds maximum of {max_top_p}",
            )

        return ValidationResult(value=top_p)

    def validate_penalty(
        self, penalty: Optional[float], penalty_name: str = "penalty"
    ) -> ValidationResult:
        """
        Validate frequency_penalty or presence_penalty.

        OpenAI supports -2.0 to 2.0 range. Some providers don't support these
        parameters at all (handled by drop_params).

        Args:
            penalty: Requested penalty value (None for no validation)
            penalty_name: Name of penalty for logging ("frequency_penalty" or "presence_penalty")

        Returns:
            ValidationResult with validated value
        """
        if penalty is None:
            return ValidationResult(value=None)

        # OpenAI penalty range: -2.0 to 2.0
        min_penalty = self.DEFAULT_PENALTY_MIN
        max_penalty = self.DEFAULT_PENALTY_MAX

        # Cap to valid range
        if penalty < min_penalty:
            logger.warning(
                f"{penalty_name}_below_minimum",
                model=self.model,
                requested=penalty,
                minimum=min_penalty,
                adjusted_to=min_penalty,
            )
            return ValidationResult(
                value=min_penalty,
                was_adjusted=True,
                original_value=penalty,
                reason=f"Below minimum of {min_penalty}",
            )

        if penalty > max_penalty:
            logger.warning(
                f"{penalty_name}_above_maximum",
                model=self.model,
                requested=penalty,
                maximum=max_penalty,
                adjusted_to=max_penalty,
            )
            return ValidationResult(
                value=max_penalty,
                was_adjusted=True,
                original_value=penalty,
                reason=f"Exceeds maximum of {max_penalty}",
            )

        return ValidationResult(value=penalty)

    def validate_all(
        self,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        default_max_tokens: int = 4096,
    ) -> Dict[str, ValidationResult]:
        """
        Validate all parameters at once.

        Args:
            max_tokens: Requested max_tokens
            temperature: Requested temperature
            top_p: Requested top_p
            frequency_penalty: Requested frequency_penalty
            presence_penalty: Requested presence_penalty
            default_max_tokens: Default max_tokens if none provided

        Returns:
            Dict mapping parameter names to ValidationResults

        Example:
            >>> validator = ParametersValidator("gpt-4")
            >>> results = validator.validate_all(
            ...     max_tokens=16000,
            ...     temperature=3.0,
            ...     top_p=0.9
            ... )
            >>> results["max_tokens"].value  # 4096 (capped)
            >>> results["temperature"].value  # 2.0 (capped)
            >>> results["top_p"].value  # 0.9 (unchanged)
        """
        results = {
            "max_tokens": self.validate_max_tokens(max_tokens, default_max_tokens),
            "temperature": self.validate_temperature(temperature),
            "top_p": self.validate_top_p(top_p),
            "frequency_penalty": self.validate_penalty(
                frequency_penalty, "frequency_penalty"
            ),
            "presence_penalty": self.validate_penalty(
                presence_penalty, "presence_penalty"
            ),
        }

        # Log summary if any adjustments were made
        adjusted = {k: v for k, v in results.items() if v.was_adjusted}
        if adjusted:
            logger.info(
                "parameters_adjusted",
                model=self.model,
                adjustments={
                    k: {
                        "from": v.original_value,
                        "to": v.value,
                        "reason": v.reason,
                    }
                    for k, v in adjusted.items()
                },
            )

        return results
