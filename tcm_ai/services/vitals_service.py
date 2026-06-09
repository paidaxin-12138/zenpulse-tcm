from __future__ import annotations

from typing import Any, Dict, List, Optional

from tcm_ai.domain.vitals.extractor import (
    dual_channel_length_delta,
    extract_vitals_from_samples,
    format_channel_mismatch_warning,
)
from tcm_ai.domain.vitals.models import VitalsAssessment
from tcm_ai.domain.vitals.rules import assess_vitals, failed_assessment
from tcm_ai.domain.vitals.rules_loader import load_vitals_rules


class VitalsService:
    def __init__(self, rules: Optional[Dict[str, Any]] = None) -> None:
        self._rules = rules or load_vitals_rules()

    def analyze_samples(
        self,
        samples: List[float],
        fs: float = 100.0,
        samples_ch2: Optional[List[float]] = None,
        source: str = "max30102_ble",
    ) -> VitalsAssessment:
        if not samples:
            return failed_assessment("采样数据为空", source=source)

        qcfg = self._rules.get("quality", {})
        min_sec = float(qcfg.get("min_samples_sec", 5))
        min_count = int(qcfg.get("min_sample_count", 500))
        duration = len(samples) / fs if fs else 0.0

        if len(samples) < min_count or duration < min_sec:
            return failed_assessment(
                f"采样不足（需至少 {min_sec}s / {min_count} 点）",
                source=source,
            )

        hr, spo2, quality = extract_vitals_from_samples(samples, fs, samples_ch2)
        if hr <= 0:
            return failed_assessment("未能从波形中提取有效心率", source=source)

        channel_warnings: List[str] = []
        if samples_ch2:
            tolerance = int(qcfg.get("channel_length_tolerance", 0))
            delta = dual_channel_length_delta(samples, samples_ch2)
            if delta > tolerance:
                merged_len = min(len(samples), len(samples_ch2))
                channel_warnings.append(
                    format_channel_mismatch_warning(len(samples), len(samples_ch2), merged_len)
                )
                penalty = float(qcfg.get("channel_mismatch_quality_penalty", 0.85))
                quality = round(quality * penalty, 3)

        result = assess_vitals(
            hr,
            spo2,
            source=source,
            quality_score=quality,
            sample_count=len(samples),
            duration_sec=duration,
            rules=self._rules,
        )
        if channel_warnings:
            result.alerts = [*result.alerts, *channel_warnings]
            result.limitations = [*result.limitations, *channel_warnings]
        return result

    def analyze_manual(
        self,
        heart_rate: int,
        pulse: Optional[int] = None,
        spo2: Optional[float] = None,
        source: str = "manual",
    ) -> VitalsAssessment:
        hr = float(heart_rate if heart_rate is not None else (pulse if pulse is not None else 0))
        spo2_val = float(spo2) if spo2 is not None else 0.0
        return assess_vitals(
            hr,
            spo2_val,
            source=source,
            quality_score=0.5,
            rules=self._rules,
        )
