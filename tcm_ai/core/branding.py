# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""全平台品牌与跨端链接配置。"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from tcm_ai.core.paths import DATA_DIR

BRANDING_PATH = os.path.join(DATA_DIR, "branding.json")

DEFAULT_BRANDING: Dict[str, Any] = {
    "brandName": "御心调理",
    "productName": "ZenPulse AI",
    "tagline": "中医智慧诊疗",
    "links": {"web": "/", "admin": "/admin", "legal": "/legal/privacy"},
    "miniprogram": {
        "name": "御心调理",
        "shortName": "御心调理",
        "hint": "微信搜索「御心调理」",
    },
    "radius": {
        "sm": "12px",
        "md": "16px",
        "lg": "20px",
        "xl": "24px",
        "2xl": "32px",
    },
}


def load_branding() -> Dict[str, Any]:
    if not os.path.isfile(BRANDING_PATH):
        return dict(DEFAULT_BRANDING)
    try:
        with open(BRANDING_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return dict(DEFAULT_BRANDING)
        merged = dict(DEFAULT_BRANDING)
        merged.update(data)
        if isinstance(data.get("links"), dict):
            merged["links"] = {**DEFAULT_BRANDING["links"], **data["links"]}
        if isinstance(data.get("miniprogram"), dict):
            merged["miniprogram"] = {
                **DEFAULT_BRANDING["miniprogram"],
                **data["miniprogram"],
            }
        if isinstance(data.get("radius"), dict):
            merged["radius"] = {**DEFAULT_BRANDING["radius"], **data["radius"]}
        return merged
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_BRANDING)
