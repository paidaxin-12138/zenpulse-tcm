# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

from typing import Any, Dict, List, Optional

from tcm_ai.domain.pulse.classifier_rules import classify_manual, classify_rate_rhythm
from tcm_ai.domain.pulse.features import session_features
from tcm_ai.domain.pulse.models import PulseCharacteristics, PulseResult, QualityReport
from tcm_ai.domain.pulse.motion import normalize_imu_payload
from tcm_ai.domain.pulse.preprocess import downsample_waveform, extract_ac_component, subtract_motion_component
from tcm_ai.domain.pulse.quality import collect_valid_beats
from tcm_ai.domain.pulse.rules_loader import load_pulse_rules

L1_LIMITATIONS = [
    "当前设备为容积脉搏波，无法感知指压深浅，不提供浮沉判断",
    "形态脉（滑/涩/弦等）尚未完成本设备标定，未输出脉名",
]


class PpgWaveformAnalyzer:
    """域层脉搏波分析（供 PulseEngine 与 STM 适配器共用）。"""

    def __init__(self, rules: Optional[Dict[str, Any]] = None) -> None:
        self._rules = rules or load_pulse_rules()

    @property
    def calibration_version(self) -> str:
        return str(self._rules.get("meta", {}).get("calibration_version", "builtin"))

    def analyze_from_waveform(
        self,
        samples: List[float],
        fs: float = 100.0,
        imu: Optional[Dict[str, Any]] = None,
        capability_level: str = "L1",
        source: str = "ppg",
    ) -> PulseResult:
        if not samples:
            return self._failed("empty_samples", "波形数据为空", source, capability_level)

        min_duration = float(self._rules.get("quality", {}).get("min_still_duration_sec", 15))
        duration_sec = len(samples) / fs
        if duration_sec < min_duration * 0.5:
            return self._failed(
                "sample_too_short",
                f"采样时长不足 {min_duration}s",
                source,
                capability_level,
            )

        imu_norm = normalize_imu_payload(imu)
        ac, _dc = extract_ac_component(samples)
        ac = subtract_motion_component(ac, imu_norm, fs)
        peaks, beats, filtered, quality = collect_valid_beats(ac, fs, imu_norm, self._rules)
        if quality.error:
            return self._failed(
                quality.error,
                quality.warnings[0] if quality.warnings else quality.error,
                source,
                capability_level,
                quality,
            )

        waveform_stats, research = session_features(filtered, peaks, beats, fs, duration_sec)
        heart_rate = float(waveform_stats.get("heart_rate") or 0)
        rr_std = float(waveform_stats.get("rr_std") or 0)
        label = classify_rate_rhythm(
            heart_rate,
            rr_std,
            self._rules,
            valid_beat_count=quality.valid_beat_count,
        )

        waveform_stats["valid_beat_ratio"] = quality.valid_beat_ratio
        waveform_stats["still_duration_sec"] = quality.still_duration_sec
        confidence = round(label.confidence * quality.score, 3)

        return self._build_result(
            label=label,
            confidence=confidence,
            source=source,
            capability_level=capability_level,
            waveform_stats=waveform_stats,
            research_features=research,
            pulse_waveform=downsample_waveform(filtered, fs),
            quality=quality,
        )

    def analyze_manual(
        self,
        heart_rate: int,
        pulse: int,
        source: str = "manual",
        capability_level: str = "L0",
    ) -> PulseResult:
        bpm = int(pulse if pulse is not None else heart_rate)
        label = classify_manual(bpm, self._rules)
        quality = QualityReport(
            score=0.45,
            valid_beat_ratio=0.0,
            still_duration_sec=0.0,
            motion_rejected_sec=0.0,
            valid_beat_count=0,
            warnings=["手动录入，未采集脉搏波形"],
        )
        limitations = list(L1_LIMITATIONS) + ["基于用户填写心率，非波形分析"]
        return PulseResult(
            success=True,
            pulse_type=label.pulse_type,
            description=label.description,
            confidence=round(min(label.confidence, 0.5), 3),
            source=source,
            capability_level=capability_level,
            limitations=limitations,
            calibration_version=self.calibration_version,
            characteristics=label.characteristics,
            waveform_stats={"heart_rate": float(bpm)},
            research_features={},
            pulse_waveform=[],
            quality=quality,
            possible_conditions=[],
            treatment_recommendations=[],
        )

    def _build_result(
        self,
        *,
        label,
        confidence: float,
        source: str,
        capability_level: str,
        waveform_stats: Dict[str, Any],
        research_features: Dict[str, Any],
        pulse_waveform: List[float],
        quality: QualityReport,
    ) -> PulseResult:
        return PulseResult(
            success=True,
            pulse_type=label.pulse_type,
            description=label.description,
            confidence=confidence,
            source=source,
            capability_level=capability_level,
            limitations=list(L1_LIMITATIONS),
            calibration_version=self.calibration_version,
            characteristics=label.characteristics,
            waveform_stats=waveform_stats,
            research_features=research_features,
            pulse_waveform=pulse_waveform,
            quality=quality,
        )

    def _failed(
        self,
        error_code: str,
        message: str,
        source: str,
        capability_level: str,
        quality: Optional[QualityReport] = None,
    ) -> PulseResult:
        q = quality or QualityReport(
            score=0.0,
            valid_beat_ratio=0.0,
            still_duration_sec=0.0,
            motion_rejected_sec=0.0,
            valid_beat_count=0,
            warnings=[message],
            error=error_code,
        )
        return PulseResult(
            success=False,
            pulse_type="",
            description=message,
            confidence=0.0,
            source=source,
            capability_level=capability_level,
            limitations=list(L1_LIMITATIONS),
            calibration_version=self.calibration_version,
            characteristics=PulseCharacteristics(),
            waveform_stats={},
            research_features={},
            pulse_waveform=[],
            quality=q,
            error=error_code,
        )
