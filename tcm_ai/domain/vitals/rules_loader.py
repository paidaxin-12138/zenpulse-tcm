# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict

import yaml

from tcm_ai.core.paths import PROJECT_ROOT

DEFAULT_RULES_PATH = os.path.join(PROJECT_ROOT, "config", "vitals_rules.yaml")


@lru_cache(maxsize=1)
def load_vitals_rules(path: str = DEFAULT_RULES_PATH) -> Dict[str, Any]:
    if not os.path.isfile(path):
        return _defaults()
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    base = _defaults()
    for section, values in data.items():
        if isinstance(values, dict) and isinstance(base.get(section), dict):
            base[section].update(values)
        else:
            base[section] = values
    return base


def _defaults() -> Dict[str, Any]:
    return {
        "meta": {"version": "builtin", "device": "MAX30102"},
        "heart_rate": {"bradycardia_max": 60, "normal_max": 100, "tachycardia_min": 100},
        "spo2": {"normal_min": 95, "mild_hypoxia_min": 90},
        "quality": {"min_samples_sec": 5, "min_sample_count": 500},
    }
