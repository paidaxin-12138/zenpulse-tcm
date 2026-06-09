from __future__ import annotations

import math
from typing import List


def synthetic_pulse_waveform(
    duration_sec: float = 20.0,
    fs: float = 100.0,
    bpm: float = 72.0,
    amplitude: float = 300.0,
) -> List[float]:
    """测试/模拟用合成脉搏波。"""
    samples: List[float] = []
    n = int(duration_sec * fs)
    period = 60.0 / bpm
    for i in range(n):
        t = i / fs
        phase = (t % period) / period
        beat = amplitude * max(0.0, math.sin(math.pi * phase)) ** 1.5
        samples.append(1000.0 + beat + 10.0 * math.sin(t * 13.7))
    return samples
