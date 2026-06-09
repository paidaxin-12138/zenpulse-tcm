# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import signal

from tcm_ai.domain.pulse.motion import imu_axes_to_ms2


def extract_ac_component(raw: List[float]) -> Tuple[List[float], float]:
    if not raw:
        return [], 0.0
    arr = np.asarray(raw, dtype=float)
    dc = float(np.mean(arr))
    ac = (arr - dc).tolist()
    return ac, dc


def bandpass(
    samples: List[float],
    fs: float,
    low_hz: float = 0.5,
    high_hz: float = 5.0,
    order: int = 2,
) -> List[float]:
    if len(samples) < max(int(fs * 2), 8):
        return list(samples)
    nyquist = 0.5 * fs
    low = max(low_hz / nyquist, 1e-6)
    high = min(high_hz / nyquist, 0.99)
    if low >= high:
        return list(samples)
    b, a = signal.butter(order, [low, high], btype="band")
    filtered = signal.filtfilt(b, a, np.asarray(samples, dtype=float))
    return filtered.tolist()


def downsample_waveform(samples: List[float], fs: float, target_hz: float = 20.0) -> List[float]:
    if not samples or fs <= target_hz:
        return [round(float(v), 6) for v in samples]
    step = max(int(round(fs / target_hz)), 1)
    return [round(float(samples[i]), 6) for i in range(0, len(samples), step)]


def subtract_motion_component(
    ac: List[float],
    imu: Optional[Dict[str, Any]],
    fs: float,
) -> List[float]:
    """L2：用 ACC 模长变化做轻量减振（非 LMS，仅减相关低频分量）。"""
    if not imu or not ac:
        return ac
    ax = imu.get("acc_x") or imu.get("ax") or []
    ay = imu.get("acc_y") or imu.get("ay") or []
    az = imu.get("acc_z") or imu.get("az") or []
    if not ax or not ay or not az:
        return ac

    imu_fs = float(imu.get("fs") or fs)
    n = len(ac)
    idx = np.linspace(0, min(len(ax), len(ay), len(az)) - 1, n)
    x = np.interp(idx, np.arange(len(ax)), imu_axes_to_ms2(ax))
    y = np.interp(idx, np.arange(len(ay)), imu_axes_to_ms2(ay))
    z = np.interp(idx, np.arange(len(az)), imu_axes_to_ms2(az))
    mag = np.sqrt(x**2 + y**2 + z**2)
    mag = mag - np.median(mag)
    if imu_fs != fs:
        mag = mag * (fs / imu_fs)
    ac_arr = np.asarray(ac, dtype=float)
    scale = float(np.std(ac_arr) / max(np.std(mag), 1e-6))
    return (ac_arr - 0.15 * scale * mag).tolist()
