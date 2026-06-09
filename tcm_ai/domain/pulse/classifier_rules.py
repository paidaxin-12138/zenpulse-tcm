# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from tcm_ai.domain.pulse.models import PulseCharacteristics
from tcm_ai.domain.pulse.rules_loader import load_pulse_rules


@dataclass
class ClinicalLabel:
    pulse_type: str
    characteristics: PulseCharacteristics
    confidence: float
    description: str


def classify_rate_rhythm(
    heart_rate: float,
    rr_std: float,
    rules: Optional[Dict[str, Any]] = None,
    valid_beat_count: int = 0,
) -> ClinicalLabel:
    rules = rules or load_pulse_rules()
    rate_rules = rules.get("rate", {})
    rhythm_rules = rules.get("rhythm", {})

    chi_max = float(rate_rules.get("chi_max_hr", 60))
    shu_min = float(rate_rules.get("shu_min_hr", 90))
    rr_std_max = float(rhythm_rules.get("rr_std_max", 0.12))
    min_beats_rhythm = int(rhythm_rules.get("min_valid_beats_for_rhythm", 15))

    if heart_rate < chi_max:
        rate = "迟"
        pulse_type = "迟脉"
        description = "脉来迟慢，一息不足四至（基于脉搏波频次分析，不含浮沉）。"
        confidence = 0.85
    elif heart_rate > shu_min:
        rate = "数"
        pulse_type = "数脉"
        description = "脉来数急，一息五至以上（基于脉搏波频次分析，不含浮沉）。"
        confidence = 0.85
    else:
        rate = "正常"
        pulse_type = "平和脉"
        description = "脉率正常，节律均匀（基于容积脉搏波，不含浮沉与形态脉名）。"
        confidence = 0.8

    rhythm = (
        "不齐"
        if rr_std > rr_std_max and heart_rate > 0 and valid_beat_count >= min_beats_rhythm
        else "齐"
    )
    if rhythm == "不齐":
        pulse_type = "不齐脉"
        description = "脉律不齐，至数间隔变异增大（建议结合临床进一步确认）。"
        confidence = min(confidence, 0.75)

    return ClinicalLabel(
        pulse_type=pulse_type,
        characteristics=PulseCharacteristics(
            rate=rate,
            rhythm=rhythm,
            strength=None,
            depth=None,
            shape=None,
        ),
        confidence=confidence,
        description=description,
    )


def classify_manual(pulse: int, rules: Optional[Dict[str, Any]] = None) -> ClinicalLabel:
    rules = rules or load_pulse_rules()
    chi_max = int(rules.get("rate", {}).get("chi_max_hr", 60))
    shu_min = int(rules.get("rate", {}).get("shu_min_hr", 90))

    if pulse < chi_max:
        return classify_rate_rhythm(float(pulse), 0.0, rules)
    if pulse > shu_min:
        return classify_rate_rhythm(float(pulse), 0.0, rules)
    return classify_rate_rhythm(float(pulse), 0.0, rules)
