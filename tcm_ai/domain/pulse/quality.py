from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from tcm_ai.domain.pulse.features import beat_snr_db
from tcm_ai.domain.pulse.models import QualityReport
from tcm_ai.domain.pulse.motion import window_is_moving
from tcm_ai.domain.pulse.preprocess import bandpass
from tcm_ai.domain.pulse.rules_loader import load_pulse_rules
from tcm_ai.domain.pulse.segmentation import extract_beats, find_peaks


def sliding_windows(
    samples: Sequence[float],
    fs: float,
    win_sec: float,
    hop_sec: float,
) -> List[Tuple[int, int]]:
    n = len(samples)
    win = max(int(win_sec * fs), 1)
    hop = max(int(hop_sec * fs), 1)
    windows: List[Tuple[int, int]] = []
    start = 0
    while start + win <= n:
        windows.append((start, start + win))
        start += hop
    if not windows and n > 0:
        windows.append((0, n))
    return windows


def collect_valid_beats(
    samples: Sequence[float],
    fs: float,
    imu: Optional[Dict[str, Any]] = None,
    rules: Optional[Dict[str, Any]] = None,
) -> Tuple[List[int], List[List[float]], List[float], QualityReport]:
    rules = rules or load_pulse_rules()
    qcfg = rules.get("quality", {})
    min_beats = int(qcfg.get("min_valid_beats", 15))
    min_snr = float(qcfg.get("min_beat_snr_db", 3))
    win_sec = float(qcfg.get("window_sec", 5))
    hop_sec = float(qcfg.get("window_hop_sec", 2))
    min_still = float(qcfg.get("min_still_duration_sec", 15))

    total_sec = len(samples) / fs if fs else 0.0
    all_peaks: List[int] = []
    all_beats: List[List[float]] = []
    still_sec = 0.0
    motion_rejected = 0.0
    warnings: List[str] = []

    for start, end in sliding_windows(samples, fs, win_sec, hop_sec):
        window = samples[start:end]
        window_dur = (end - start) / fs
        if imu and window_is_moving(imu, start / fs, end / fs, rules):
            motion_rejected += window_dur
            continue

        filtered = bandpass(list(window), fs)
        peaks = find_peaks(filtered, fs)
        beats = extract_beats(filtered, peaks, fs)
        good_beats = [b for b in beats if beat_snr_db(b) >= min_snr]
        if not good_beats:
            continue

        still_sec += window_dur
        offset_peaks = [start + p for p in peaks]
        all_peaks.extend(offset_peaks)
        all_beats.extend(good_beats)

    valid_ratio = min(1.0, len(all_beats) / max(min_beats, 1))
    score = min(1.0, 0.5 * valid_ratio + 0.5 * min(still_sec / max(min_still, 1e-6), 1.0))

    error = None
    if len(all_beats) < min_beats:
        error = "insufficient_valid_beats"
        warnings.append("有效心搏不足，请保持静止后重测")
    if still_sec < min_still:
        warnings.append("有效静止时长不足")

    quality = QualityReport(
        score=round(score, 3),
        valid_beat_ratio=round(valid_ratio, 3),
        still_duration_sec=round(still_sec, 2),
        motion_rejected_sec=round(motion_rejected, 2),
        valid_beat_count=len(all_beats),
        warnings=warnings,
        error=error,
    )
    return all_peaks, all_beats, bandpass(list(samples), fs), quality
