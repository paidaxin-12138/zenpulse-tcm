# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

from typing import List, Tuple

import numpy as np
from scipy import signal


def merge_dual_channel(ch1: List[float], ch2: List[float]) -> List[float]:
    if not ch1:
        return list(ch2)
    if not ch2:
        return list(ch1)
    n = min(len(ch1), len(ch2))
    return [float((ch1[i] + ch2[i]) / 2) for i in range(n)]


def dual_channel_length_delta(ch1: List[float], ch2: List[float]) -> int:
    if not ch1 or not ch2:
        return 0
    return abs(len(ch1) - len(ch2))


def format_channel_mismatch_warning(ch1_len: int, ch2_len: int, merged_len: int) -> str:
    return (
        f"双通道采样点数不一致（CH1={ch1_len}，CH2={ch2_len}），"
        f"已按较短通道合并 {merged_len} 点，结果仅供参考"
    )


def extract_ac(raw: List[float]) -> Tuple[List[float], float]:
    if not raw:
        return [], 0.0
    arr = np.asarray(raw, dtype=float)
    dc = float(np.mean(arr))
    return (arr - dc).tolist(), dc


def estimate_heart_rate(ac: List[float], fs: float) -> float:
    if len(ac) < fs * 2:
        return 0.0
    nyquist = 0.5 * fs
    low = 0.5 / nyquist
    high = min(5.0 / nyquist, 0.99)
    b, a = signal.butter(2, [low, high], btype="band")
    filtered = signal.filtfilt(b, a, np.asarray(ac, dtype=float))
    threshold = float(np.mean(filtered) + np.std(filtered) * 0.6)
    peaks: List[int] = []
    for i in range(1, len(filtered) - 1):
        if filtered[i] > threshold and filtered[i] > filtered[i - 1] and filtered[i] > filtered[i + 1]:
            peaks.append(i)
    if len(peaks) < 2:
        return 0.0
    intervals = [(peaks[i] - peaks[i - 1]) / fs for i in range(1, len(peaks))]
    avg_interval = float(np.mean(intervals))
    if avg_interval <= 0:
        return 0.0
    hr = 60.0 / avg_interval
    return round(max(40.0, min(180.0, hr)), 1)


def estimate_spo2(ac: List[float], dc: float) -> float:
    if not ac or dc <= 0:
        return 0.0
    arr = np.asarray(ac, dtype=float)
    ac_ratio = float(np.std(arr) / max(abs(dc), 1e-6))
    spo2 = 100.0 - ac_ratio * 8.0
    return round(max(70.0, min(100.0, spo2)), 1)


def extract_vitals_from_samples(
    samples: List[float],
    fs: float = 100.0,
    samples_ch2: List[float] | None = None,
) -> Tuple[float, float, float]:
    merged = merge_dual_channel(samples, samples_ch2 or [])
    ac, dc = extract_ac(merged)
    hr = estimate_heart_rate(ac, fs)
    spo2 = estimate_spo2(ac, dc)
    quality = min(1.0, len(merged) / max(fs * 10, 1))
    return hr, spo2, quality
