# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VitalsAssessment:
    success: bool
    heart_rate: float
    pulse: int
    spo2: float
    hr_status: str
    spo2_status: str
    overall_status: str
    alerts: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    source: str = "manual"
    sample_count: int = 0
    duration_sec: float = 0.0
    limitations: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
