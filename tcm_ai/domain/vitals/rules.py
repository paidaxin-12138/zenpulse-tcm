# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

from typing import Any, Dict, List, Optional

from tcm_ai.domain.vitals.models import VitalsAssessment
from tcm_ai.domain.vitals.rules_loader import load_vitals_rules

LIMITATIONS = [
    "数据来自 MAX30102 光学传感器估算，非医疗级设备",
    "血氧为算法近似值，不能用于临床诊断",
]


def assess_vitals(
    heart_rate: float,
    spo2: float,
    *,
    source: str = "max30102",
    quality_score: float = 1.0,
    sample_count: int = 0,
    duration_sec: float = 0.0,
    rules: Optional[Dict[str, Any]] = None,
) -> VitalsAssessment:
    rules = rules or load_vitals_rules()
    hr_cfg = rules.get("heart_rate", {})
    spo2_cfg = rules.get("spo2", {})

    brady_max = float(hr_cfg.get("bradycardia_max", 60))
    normal_max = float(hr_cfg.get("normal_max", 100))
    spo2_normal = float(spo2_cfg.get("normal_min", 95))
    spo2_mild = float(spo2_cfg.get("mild_hypoxia_min", 90))

    alerts: List[str] = []
    suggestions: List[str] = []

    if heart_rate <= 0:
        hr_status = "未知"
    elif heart_rate < brady_max:
        hr_status = "偏慢"
        alerts.append(f"心率偏慢（{heart_rate} bpm）")
        suggestions.append("如持续偏慢或伴头晕，建议休息后复测并咨询医生")
    elif heart_rate > normal_max:
        hr_status = "偏快"
        alerts.append(f"心率偏快（{heart_rate} bpm）")
        suggestions.append("请保持静止，避免剧烈运动后立即测量")
    else:
        hr_status = "正常"

    if spo2 <= 0:
        spo2_status = "未知"
    elif spo2 >= spo2_normal:
        spo2_status = "正常"
    elif spo2 >= spo2_mild:
        spo2_status = "偏低"
        alerts.append(f"血氧偏低（{spo2}%）")
        suggestions.append("请在通风处静止复测；持续偏低请就医")
    else:
        spo2_status = "过低"
        alerts.append(f"血氧过低（{spo2}%）")
        suggestions.append("请立即停止活动并就医")

    if hr_status == "正常" and spo2_status == "正常":
        overall = "正常"
    elif alerts:
        overall = "需关注"
    else:
        overall = "待确认"

    pulse = int(round(heart_rate)) if heart_rate > 0 else 0
    return VitalsAssessment(
        success=heart_rate > 0,
        heart_rate=heart_rate,
        pulse=pulse,
        spo2=spo2,
        hr_status=hr_status,
        spo2_status=spo2_status,
        overall_status=overall,
        alerts=alerts,
        suggestions=suggestions,
        quality_score=round(quality_score, 3),
        source=source,
        sample_count=sample_count,
        duration_sec=round(duration_sec, 2),
        limitations=list(LIMITATIONS),
    )


def failed_assessment(message: str, source: str = "max30102") -> VitalsAssessment:
    return VitalsAssessment(
        success=False,
        heart_rate=0.0,
        pulse=0,
        spo2=0.0,
        hr_status="未知",
        spo2_status="未知",
        overall_status="失败",
        alerts=[message],
        suggestions=["请检查传感器佩戴与蓝牙连接后重试"],
        quality_score=0.0,
        source=source,
        limitations=list(LIMITATIONS),
        error=message,
    )
