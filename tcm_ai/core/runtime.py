"""运行环境判定（development / production）。"""

import os


def get_tcm_env() -> str:
    return (os.environ.get("TCM_ENV") or "development").strip().lower()


def is_production() -> bool:
    return get_tcm_env() in ("production", "prod")


def is_development() -> bool:
    return not is_production()
