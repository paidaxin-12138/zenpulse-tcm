# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np


def beat_snr_db(beat: Sequence[float]) -> float:
    arr = np.asarray(beat, dtype=float)
    if len(arr) < 4:
        return 0.0
    signal_power = float(np.var(arr))
    noise = float(np.var(np.diff(arr)))
    if noise <= 1e-12:
        return 40.0
    ratio = signal_power / noise
    return 10.0 * math.log10(max(ratio, 1e-12))


def rr_intervals_sec(peaks: List[int], fs: float) -> List[float]:
    if len(peaks) < 2:
        return []
    return [(peaks[i] - peaks[i - 1]) / fs for i in range(1, len(peaks))]


def compute_hrv_metrics(rr_sec: List[float]) -> Dict[str, float]:
    if not rr_sec:
        return {"rr_mean_ms": 0.0, "rr_std": 0.0, "rmssd_ms": 0.0, "lf_hf_ratio": 0.0}
    arr = np.asarray(rr_sec, dtype=float)
    rr_mean = float(np.mean(arr))
    rr_std = float(np.std(arr))
    if len(arr) > 1:
        diff = np.diff(arr)
        rmssd = float(np.sqrt(np.mean(diff**2)))
    else:
        rmssd = 0.0
    return {
        "rr_mean_ms": round(rr_mean * 1000, 2),
        "rr_std": round(rr_std, 4),
        "rmssd_ms": round(rmssd * 1000, 2),
        "lf_hf_ratio": compute_lf_hf_ratio(rr_sec),
    }


def compute_lf_hf_ratio(rr_sec: List[float]) -> float:
    if len(rr_sec) < 10:
        return 0.0
    times = np.cumsum(np.concatenate([[0.0], rr_sec]))
    duration = float(times[-1])
    if duration <= 0:
        return 0.0
    resample_fs = 4.0
    t_uniform = np.arange(0.0, duration, 1.0 / resample_fs)
    if len(t_uniform) < 16:
        return 0.0
    rr_series = np.interp(t_uniform, times[1:], rr_sec)
    rr_series = rr_series - np.mean(rr_series)
    from scipy.signal import welch

    freq, power = welch(rr_series, fs=resample_fs, nperseg=min(len(rr_series), 128))
    lf_mask = (freq >= 0.04) & (freq < 0.15)
    hf_mask = (freq >= 0.15) & (freq < 0.4)
    lf = float(np.trapezoid(power[lf_mask], freq[lf_mask])) if np.any(lf_mask) else 0.0
    hf = float(np.trapezoid(power[hf_mask], freq[hf_mask])) if np.any(hf_mask) else 0.0
    return round(lf / max(hf, 1e-6), 4)


def spectral_entropy(filtered: List[float], fs: float) -> float:
    if len(filtered) < int(fs):
        return 0.0
    arr = np.asarray(filtered, dtype=float)
    spectrum = np.abs(np.fft.rfft(arr))
    total = float(np.sum(spectrum))
    if total <= 0:
        return 0.0
    prob = spectrum / total
    prob = prob[prob > 0]
    entropy = -float(np.sum(prob * np.log(prob)))
    max_entropy = math.log(len(prob)) if len(prob) else 1.0
    return round(entropy / max_entropy, 4) if max_entropy else 0.0


def _beat_shape_metrics(beat: Sequence[float], fs: float) -> Dict[str, float]:
    arr = np.asarray(beat, dtype=float)
    foot = int(np.argmin(arr))
    peak = int(np.argmax(arr))
    amplitude = float(arr[peak] - arr[foot]) if peak != foot else float(np.max(arr) - np.min(arr))
    rise_time_ms = abs(peak - foot) / fs * 1000.0
    half = amplitude * 0.5 + float(arr[foot])
    above = np.where(arr >= half)[0]
    pulse_width_ms = ((above[-1] - above[0]) / fs * 1000.0) if len(above) >= 2 else 0.0
    return {
        "systolic_amplitude": amplitude,
        "rise_time_ms": rise_time_ms,
        "pulse_width_ms": pulse_width_ms,
        "skewness": float(_safe_skew(arr)),
        "kurtosis": float(_safe_kurtosis(arr)),
    }


def _safe_skew(arr: np.ndarray) -> float:
    std = float(np.std(arr))
    if std <= 1e-9:
        return 0.0
    mean = float(np.mean(arr))
    return float(np.mean(((arr - mean) / std) ** 3))


def _safe_kurtosis(arr: np.ndarray) -> float:
    std = float(np.std(arr))
    if std <= 1e-9:
        return 0.0
    mean = float(np.mean(arr))
    return float(np.mean(((arr - mean) / std) ** 4))


def aggregate_beat_features(beats: List[List[float]], fs: float) -> Dict[str, float]:
    if not beats:
        return {
            "systolic_amplitude": 0.0,
            "rise_time_ms": 0.0,
            "pulse_width_ms": 0.0,
            "dicrotic_depth": 0.0,
            "augmentation_index": 0.0,
            "skewness": 0.0,
            "kurtosis": 0.0,
        }
    metrics = [_beat_shape_metrics(beat, fs) for beat in beats]
    result: Dict[str, float] = {}
    for key in metrics[0]:
        values = [m[key] for m in metrics]
        result[key] = round(float(np.median(values)), 6)
    amps = [m["systolic_amplitude"] for m in metrics]
    result["dicrotic_depth"] = round(float(np.percentile(amps, 25) / max(np.percentile(amps, 75), 1e-6)), 4)
    result["augmentation_index"] = round(
        result["systolic_amplitude"] / max(result["pulse_width_ms"], 1.0),
        4,
    )
    return result


def session_features(
    filtered: List[float],
    peaks: List[int],
    beats: List[List[float]],
    fs: float,
    total_duration_sec: float,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    rr_sec = rr_intervals_sec(peaks, fs)
    hrv = compute_hrv_metrics(rr_sec)
    heart_rate = round(60.0 / hrv["rr_mean_ms"] * 1000, 1) if hrv["rr_mean_ms"] > 0 else 0.0
    research = aggregate_beat_features(beats, fs)
    research["lf_hf_ratio"] = hrv.get("lf_hf_ratio", 0.0)
    waveform_stats = {
        "heart_rate": heart_rate,
        **hrv,
        "spectral_entropy": spectral_entropy(filtered, fs),
        "valid_beat_count": len(beats),
        "duration_sec": round(total_duration_sec, 2),
    }
    return waveform_stats, research
