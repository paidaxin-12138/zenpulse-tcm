# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from tcm_ai.core.config_store import load_config


def get_settings():
    """统一配置入口，供诊断端与管理端共用。"""
    return load_config()
