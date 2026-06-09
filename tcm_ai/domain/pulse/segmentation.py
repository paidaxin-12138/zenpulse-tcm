# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

from typing import List, Tuple

import numpy as np


def find_peaks(filtered: List[float], fs: float, min_distance_sec: float = 0.35) -> List[int]:
    if len(filtered) < 3:
        return []
    data = np.asarray(filtered, dtype=float)
    threshold = float(np.mean(data) + 0.55 * np.std(data))
    min_distance = max(int(min_distance_sec * fs), 1)

    dy = np.diff(data)
    candidates: List[int] = []
    for i in range(1, len(dy)):
        idx = i
        if data[idx] <= threshold:
            continue
        if dy[i - 1] <= 0 or dy[i] >= 0:
            continue
        candidates.append(idx)

    if not candidates:
        return []

    peaks: List[int] = []
    last = -min_distance
    for idx in candidates:
        if idx - last >= min_distance:
            peaks.append(idx)
            last = idx
        elif peaks and data[idx] > data[peaks[-1]]:
            peaks[-1] = idx
            last = idx
    return peaks


def extract_beats(
    filtered: List[float],
    peaks: List[int],
    fs: float,
    beat_window_sec: float = 0.8,
) -> List[List[float]]:
    if not peaks:
        return []
    half = int(beat_window_sec * fs * 0.5)
    beats: List[List[float]] = []
    n = len(filtered)
    for peak in peaks:
        start = max(0, peak - half)
        end = min(n, peak + half)
        segment = filtered[start:end]
        if len(segment) >= max(int(0.2 * fs), 4):
            beats.append(segment)
    return beats
