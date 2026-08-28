from abc import ABC


class FiApiKey(ABC):
    _fi_api_key = None

    @classmethod
    def set_api_key(cls, api_key):
        cls._fi_api_key = api_key

    @classmethod
    def get_api_key(cls):
        return cls._fi_api_key

    @classmethod
    def set_key(cls, api_key):
        cls._fi_api_key = api_key

    @classmethod
    def get_key(cls):
        return cls._fi_api_key

    @classmethod
    def is_set(cls):
        return cls._fi_api_key is not None
