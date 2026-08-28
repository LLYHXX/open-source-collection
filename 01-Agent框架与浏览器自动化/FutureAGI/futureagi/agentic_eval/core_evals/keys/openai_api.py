import os
from abc import ABC


class OpenAiApiKey(ABC):
    _openai_api_key = None

    @classmethod
    def set_key(cls, api_key):
        cls._openai_api_key = api_key

    @classmethod
    def get_key(cls):
        if os.environ.get("OPENAI_API_KEY"):
            cls.set_key(os.environ.get("OPENAI_API_KEY"))
        return cls._openai_api_key
