from tcm_ai.core.config_store import load_config


def get_settings():
    """统一配置入口，供诊断端与管理端共用。"""
    return load_config()
