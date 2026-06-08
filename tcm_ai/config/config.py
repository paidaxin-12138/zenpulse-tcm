import os

from tcm_ai.core.settings import get_settings


class Config:
    """兼容旧代码的配置入口，实际值来自 admin_config。"""

    _settings = None

    @classmethod
    def refresh(cls):
        cls._settings = get_settings()

    @classmethod
    def llm_model(cls) -> str:
        if cls._settings is None:
            cls.refresh()
        return cls._settings["llm"]["model"]

    @classmethod
    def ollama_base_url(cls) -> str:
        if cls._settings is None:
            cls.refresh()
        return cls._settings["llm"]["base_url"]

    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

    @staticmethod
    def ensure_directories():
        os.makedirs(Config.DATA_DIR, exist_ok=True)


config = Config()
config.ensure_directories()
