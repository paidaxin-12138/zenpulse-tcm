import copy
import json
import os
import secrets
from typing import Any, Dict, Optional

from tcm_ai.core.json_io import write_json_file

from tcm_ai.core.paths import ADMIN_CONFIG_PATH, DATA_DIR, DEFAULT_BGE_PATH

MASK = "***"

DEFAULT_CONFIG: Dict[str, Any] = {
    "admin_api_key": "",
    "embedding": {
        "provider": "local",
        "model": DEFAULT_BGE_PATH,
        "base_url": "http://127.0.0.1:11434",
        "api_key": "",
    },
    "llm": {
        "provider": "ollama",
        "model": "deepseek-r1:1.5b",
        "base_url": "http://127.0.0.1:11434",
        "api_key": "",
        "temperature": 0.3,
    },
    "rerank": {
        "provider": "none",
        "model": "BAAI/bge-reranker-base",
        "base_url": "",
        "api_key": "",
        "top_n": 5,
    },
    "rag": {
        "retrieval_top_k": 20,
        "final_top_k": 5,
        "enable_llm_answer": True,
        "rebuild_on_missing_index": True,
    },
    "server": {
        "cors_origins": [
            "http://127.0.0.1:8000",
            "http://localhost:8000",
        ],
        "allow_public_diagnose": True,
        "allow_public_knowledge_search": True,
        "rate_limit_per_minute": 60,
        "admin_session_ttl_hours": 8,
        "admin_session_secret": "",
    },
    "rbac": {
        "enabled": False,
        "keys": [],
    },
    "wechat_miniprogram": {
        "app_id": "",
        "app_secret": "",
        "dev_mode": False,
        "token_ttl_hours": 72,
        "token_refresh_grace_hours": 168,
        "token_secret": "",
    },
}

NESTED_SECRET_FIELDS = (
    ("embedding", "api_key"),
    ("llm", "api_key"),
    ("rerank", "api_key"),
)


def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> Dict[str, Any]:
    _ensure_data_dir()
    if not os.path.exists(ADMIN_CONFIG_PATH):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["admin_api_key"] = secrets.token_urlsafe(32)
        save_config(config)
        return config

    with open(ADMIN_CONFIG_PATH, "r", encoding="utf-8") as f:
        stored = json.load(f)
    config = _deep_merge(DEFAULT_CONFIG, stored)
    if not config.get("admin_api_key"):
        config["admin_api_key"] = secrets.token_urlsafe(32)
        save_config(config)
    return config


def save_config(config: Dict[str, Any]) -> None:
    _ensure_data_dir()
    write_json_file(ADMIN_CONFIG_PATH, config)


def mask_config(config: Dict[str, Any]) -> Dict[str, Any]:
    masked = copy.deepcopy(config)
    if masked.get("admin_api_key"):
        masked["admin_api_key"] = MASK
        masked["admin_api_key_set"] = True
    else:
        masked["admin_api_key_set"] = False

    rbac = masked.get("rbac") or {}
    if rbac.get("keys"):
        masked["rbac"] = {
            **rbac,
            "keys": [
                {**k, "key": MASK if k.get("key") else ""}
                for k in rbac["keys"]
            ],
        }

    for section, field in NESTED_SECRET_FIELDS:
        if masked.get(section, {}).get(field):
            masked[section][field] = MASK
            masked[section][f"{field}_set"] = True
        else:
            masked[section][f"{field}_set"] = False

    wx_cfg = masked.get("wechat_miniprogram") or {}
    if wx_cfg.get("app_secret"):
        wx_cfg["app_secret"] = MASK
        wx_cfg["app_secret_set"] = True
    else:
        wx_cfg["app_secret_set"] = False
    if wx_cfg.get("token_secret"):
        wx_cfg["token_secret"] = MASK
        wx_cfg["token_secret_set"] = True
    else:
        wx_cfg["token_secret_set"] = False
    masked["wechat_miniprogram"] = wx_cfg
    return masked


def merge_config_update(current: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(current)

    if "admin_api_key" in update:
        value = update["admin_api_key"]
        if value and value != MASK:
            merged["admin_api_key"] = value

    for section, field in NESTED_SECRET_FIELDS:
        if section not in update or field not in update[section]:
            continue
        value = update[section][field]
        if value and value != MASK:
            merged[section][field] = value

    for key, value in update.items():
        if key == "admin_api_key":
            continue
        if key == "rbac" and isinstance(value, dict):
            merged_rbac = merged.get("rbac") or {"enabled": False, "keys": []}
            if "enabled" in value:
                merged_rbac["enabled"] = bool(value["enabled"])
            if value.get("keys") is not None:
                merged_rbac["keys"] = value["keys"]
            merged["rbac"] = merged_rbac
            continue
        if key == "wechat_miniprogram" and isinstance(value, dict):
            merged_wx = merged.get("wechat_miniprogram") or {}
            for sub_key, sub_value in value.items():
                if sub_key in ("app_secret", "token_secret") and sub_value == MASK:
                    continue
                merged_wx[sub_key] = sub_value
            merged["wechat_miniprogram"] = merged_wx
            continue
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            for sub_key, sub_value in value.items():
                if sub_key.endswith("_set") or sub_key == "api_key":
                    continue
                merged[key][sub_key] = sub_value
        elif not isinstance(value, dict):
            merged[key] = value
    return merged


def verify_admin_api_key(provided: Optional[str]) -> bool:
    from tcm_ai.api.admin_auth import verify_admin_api_key as _verify

    return _verify(provided)


def regenerate_admin_api_key() -> str:
    config = load_config()
    new_key = secrets.token_urlsafe(32)
    config["admin_api_key"] = new_key
    save_config(config)
    return new_key
