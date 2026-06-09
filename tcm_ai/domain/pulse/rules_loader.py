# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict

import yaml

from tcm_ai.core.paths import PROJECT_ROOT

DEFAULT_RULES_PATH = os.path.join(PROJECT_ROOT, "config", "pulse_rules.yaml")


@lru_cache(maxsize=1)
def load_pulse_rules(path: str = DEFAULT_RULES_PATH) -> Dict[str, Any]:
    if not os.path.isfile(path):
        return _fallback_rules()
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return _merge_defaults(data)


def _fallback_rules() -> Dict[str, Any]:
    return _merge_defaults({})


def _merge_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    base = {
        "meta": {"calibration_version": "builtin", "device_profile": "generic"},
        "rate": {
            "calibration_status": "validated",
            "chi_max_hr": 60,
            "shu_min_hr": 90,
        },
        "rhythm": {
            "calibration_status": "validated",
            "rr_std_max": 0.12,
            "rr_cv_max": 0.15,
            "min_valid_beats_for_rhythm": 15,
        },
        "strength": {"calibration_status": "placeholder"},
        "shape": {"calibration_status": "placeholder"},
        "quality": {
            "min_valid_beats": 15,
            "min_still_duration_sec": 15,
            "min_beat_snr_db": 3,
            "motion_acc_rms_max": 0.15,
            "window_sec": 5,
            "window_hop_sec": 2,
        },
    }
    for section, values in data.items():
        if isinstance(values, dict) and isinstance(base.get(section), dict):
            base[section].update(values)
        else:
            base[section] = values
    return base
