# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from tcm_ai.domain.pulse.rules_loader import load_pulse_rules

# MPU6050 默认 ±2g：16384 LSB/g
MPU6050_LSB_PER_G = 16384.0
GRAVITY_MS2 = 9.80665


def imu_axes_to_ms2(values: List[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return arr
    if np.max(np.abs(arr)) > 32:
        arr = arr / MPU6050_LSB_PER_G * GRAVITY_MS2
    return arr


def normalize_imu_payload(imu: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not imu:
        return None
    payload = dict(imu)
    for key in ("acc_x", "acc_y", "acc_z", "ax", "ay", "az"):
        raw = payload.get(key)
        if raw:
            converted = imu_axes_to_ms2(list(raw))
            payload[key] = converted.tolist()
    payload["fs"] = float(payload.get("fs") or 50)
    payload["units"] = "m/s2"
    return payload


def window_is_moving(
    imu: Dict[str, Any],
    start_sec: float,
    end_sec: float,
    rules: Optional[Dict[str, Any]] = None,
) -> bool:
    rules = rules or load_pulse_rules()
    threshold = float(rules.get("quality", {}).get("motion_acc_rms_max", 0.15))
    fs = float(imu.get("fs") or 50)
    ax = imu.get("acc_x") or imu.get("ax") or []
    ay = imu.get("acc_y") or imu.get("ay") or []
    az = imu.get("acc_z") or imu.get("az") or []
    if not ax or not ay or not az:
        return False

    start_i = max(int(start_sec * fs), 0)
    end_i = min(int(end_sec * fs), len(ax), len(ay), len(az))
    if end_i <= start_i:
        return False

    arr_x = imu_axes_to_ms2(ax[start_i:end_i])
    arr_y = imu_axes_to_ms2(ay[start_i:end_i])
    arr_z = imu_axes_to_ms2(az[start_i:end_i])
    magnitude = np.sqrt(arr_x**2 + arr_y**2 + arr_z**2)
    baseline = float(np.median(magnitude)) if len(magnitude) else 0.0
    detrended = magnitude - baseline
    rms = float(np.sqrt(np.mean(detrended**2))) if len(detrended) else 0.0
    return rms > threshold
