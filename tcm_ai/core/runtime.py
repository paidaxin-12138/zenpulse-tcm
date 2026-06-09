# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""运行环境判定（development / production）。"""

import os


def get_tcm_env() -> str:
    return (os.environ.get("TCM_ENV") or "development").strip().lower()


def is_production() -> bool:
    return get_tcm_env() in ("production", "prod")


def is_development() -> bool:
    return not is_production()
