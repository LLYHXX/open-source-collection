"""
NVIDIA NIM Provider
"""

from typing import Dict, Optional
from openai import OpenAI
from utils.logger import get_logger

logger = get_logger(__name__)


class NvidiaNIMProvider:
    """NVIDIA NIM API provider (OpenAI-compatible)."""

    def __init__(self, config: Dict):
        """Initialize NVIDIA NIM provider."""
        self.config = config or {}
        self.api_key = (self.config.get("api_key") or "").strip()
        self.model = self.config.get("model", "nvidia/nemotron-3-ultra-550b-a55b")
        self.temperature = float(self.config.get("temperature", 0.7))
        self.max_tokens = int(self.config.get("max_tokens", 2000) or 2000)
        self.base_url = (self.config.get("base_url") or "").strip() or "https://integrate.api.nvidia.com/v1"
        self.timeout = float(self.config.get("timeout", 60) or 60)
        self.site_url = self.config.get("site_url", "https://github.com/zakirkun/deep-eye")
        self.site_name = self.config.get("site_name", "Deep Eye")

        if (
            not self.api_key
            or self.api_key.startswith("your-")
            or "your-nvidia-nim-api-key-here" in self.api_key
        ):
            raise ValueError("NVIDIA NIM API key not provided or still a placeholder")

        # Initialize OpenAI client with NVIDIA NIM base URL
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate response using NVIDIA NIM.

        Args:
            prompt: Input prompt
            **kwargs: Additional arguments

        Returns:
            Generated response
        """
        try:
            extra_headers = {}
            if self.site_url:
                extra_headers["HTTP-Referer"] = self.site_url
            if self.site_name:
                extra_headers["X-Title"] = self.site_name

            create_kwargs = {
                "model": kwargs.get("model", self.model),
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a security expert specializing in penetration testing and vulnerability research.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            }
            if extra_headers:
                create_kwargs["extra_headers"] = extra_headers

            response = self.client.chat.completions.create(**create_kwargs)

            if not response.choices:
                return ""

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"NVIDIA NIM generation error: {e}")
            raise