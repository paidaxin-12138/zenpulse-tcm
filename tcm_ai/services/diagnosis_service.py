# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from tcm_ai.domain.constants import DEFAULT_PULSE_CHARACTERISTICS, DEFAULT_VITALS_ASSESSMENT, DISCLAIMER
from tcm_ai.domain.vitals.rules import failed_assessment
from tcm_ai.domain.diagnosis_parser import parse_diagnosis_markdown
from tcm_ai.domain.pulse.models import PulseResult
from tcm_ai.services.pulse_engine import PulseEngine
from tcm_ai.services.vitals_service import VitalsService

if TYPE_CHECKING:
    from tcm_ai.services.tcm_agent import TCMAgent

logger = logging.getLogger(__name__)

_CLINICAL_EXCLUDE = frozenset(
    {
        "success",
        "research_features",
        "research_features_note",
        "calibration_version",
        "error",
    }
)


def _clinical_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in data.items() if key not in _CLINICAL_EXCLUDE}


def _is_valid_passthrough_assessment(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    if not data.get("success"):
        return False
    heart_rate = data.get("heart_rate")
    try:
        return heart_rate is not None and float(heart_rate) > 0
    except (TypeError, ValueError):
        return False


class DiagnosisService:
    def __init__(self, tcm_agent: Optional["TCMAgent"] = None) -> None:
        self._tcm_agent = tcm_agent
        self._pulse_engine = PulseEngine()
        self._vitals_service = VitalsService()

    @property
    def tcm_agent(self) -> "TCMAgent":
        if self._tcm_agent is None:
            from tcm_ai.services.tcm_agent import TCMAgent

            self._tcm_agent = TCMAgent()
        return self._tcm_agent

    def analyze_pulse_request(self, payload: Dict[str, Any]) -> PulseResult:
        imu_payload = payload.get("imu")
        result = self._pulse_engine.analyze_from_waveform(
            payload["samples"],
            fs=float(payload.get("fs") or 100.0),
            imu=imu_payload,
            capability_level=str(payload.get("capability_level") or "L1"),
            source=str(payload.get("source") or "ppg"),
        )
        if result.success:
            result = self._pulse_engine.enrich_with_knowledge(result, self.tcm_agent)
        return result

    def resolve_vitals_assessment(self, stm_data: Dict[str, Any]) -> Dict[str, Any]:
        precomputed = stm_data.get("vitals_assessment")
        if _is_valid_passthrough_assessment(precomputed):
            return dict(precomputed)

        samples = stm_data.get("max30102_samples") or stm_data.get("pulse_waveform") or []
        samples_ch2 = stm_data.get("max30102_samples_ch2")
        fs = float(stm_data.get("pulse_fs") or stm_data.get("sample_fs") or 100.0)
        source = str(stm_data.get("pulse_source") or stm_data.get("vitals_source") or "manual")

        if samples and source.startswith("max30102"):
            try:
                result = self._vitals_service.analyze_samples(
                    samples,
                    fs=fs,
                    samples_ch2=samples_ch2,
                    source=source,
                )
                return result.to_dict()
            except Exception as exc:
                logger.warning("生理参数分析错误: %s", exc)
                return failed_assessment(
                    str(exc) or "生理参数分析失败",
                    source=source,
                ).to_dict()

        heart_rate = stm_data.get("heart_rate")
        pulse = stm_data.get("pulse", heart_rate)
        if heart_rate is not None and pulse is not None:
            result = self._vitals_service.analyze_manual(
                int(heart_rate),
                int(pulse),
                spo2=stm_data.get("spo2"),
                source=source,
            )
            return result.to_dict()

        return dict(DEFAULT_VITALS_ASSESSMENT)

    def resolve_pulse(self, stm_data: Dict[str, Any]) -> Dict[str, Any]:
        waveform = stm_data.get("pulse_waveform") or []
        fs = float(stm_data.get("pulse_fs") or 100.0)
        heart_rate = stm_data.get("heart_rate")
        pulse = stm_data.get("pulse", heart_rate)
        min_samples = fs * 15

        if waveform and len(waveform) >= min_samples:
            result = self._pulse_engine.analyze_from_waveform(
                waveform,
                fs=fs,
                imu=stm_data.get("imu"),
                capability_level="L1",
                source=str(stm_data.get("pulse_source") or "ppg"),
            )
        elif stm_data.get("pulse_analysis"):
            return _clinical_from_dict(dict(stm_data["pulse_analysis"]))
        elif heart_rate is not None and pulse is not None:
            result = self._pulse_engine.analyze_manual(
                int(heart_rate),
                int(pulse),
                source=str(stm_data.get("pulse_source") or "manual"),
                capability_level="L0",
            )
        else:
            return dict(DEFAULT_PULSE_CHARACTERISTICS)

        if result.success:
            result = self._pulse_engine.enrich_with_knowledge(result, self.tcm_agent)
        return result.to_clinical_dict()

    def build_pulse_characteristics(
        self,
        heart_rate: int,
        pulse: int,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        pulse_waveform: Optional[list] = None,
        pulse_fs: float = 100.0,
        pulse_source: str = "manual",
    ) -> Dict[str, Any]:
        stm_data = {
            "heart_rate": heart_rate,
            "pulse": pulse,
            "age": age,
            "gender": gender,
            "pulse_waveform": pulse_waveform or [],
            "pulse_fs": pulse_fs,
            "pulse_source": pulse_source,
        }
        try:
            return self.resolve_pulse(stm_data)
        except Exception as exc:
            logger.warning("脉搏诊断错误: %s", exc)
            return dict(DEFAULT_PULSE_CHARACTERISTICS)

    @staticmethod
    def _structured_from_diagnosis(diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        if diagnosis.get("structured"):
            return dict(diagnosis["structured"])
        parsed = parse_diagnosis_markdown(diagnosis.get("diagnosis", ""))
        fusion_data = diagnosis.get("fusion_data") or {}
        if fusion_data.get("syndrome") and not parsed.get("syndrome"):
            parsed["syndrome"] = fusion_data["syndrome"]
        return parsed

    @staticmethod
    def _fusion_summary(diagnosis: Dict[str, Any]) -> Optional[str]:
        if diagnosis.get("fusion_summary"):
            return diagnosis["fusion_summary"]
        fusion_data = diagnosis.get("fusion_data")
        if not fusion_data:
            return None
        from tcm_ai.domain.fusion import FusionEngine

        return FusionEngine.summarize_fusion_data(fusion_data)

    def _format_response(
        self,
        diagnosis: Dict[str, Any],
        diagnosis_text: str,
        vitals: Dict[str, Any],
    ) -> Dict[str, Any]:
        structured = self._structured_from_diagnosis({**diagnosis, "diagnosis": diagnosis_text})
        return {
            "diagnosis": diagnosis_text,
            "source": diagnosis.get("source", ""),
            "vitals_assessment": vitals,
            "pulse_characteristics": {},
            "disclaimer": DISCLAIMER,
            "syndrome": structured.get("syndrome", ""),
            "analysis": structured.get("analysis", ""),
            "suggestions": structured.get("suggestions", []),
            "prescriptions": structured.get("prescriptions", []),
            "face_analysis": structured.get("face_analysis", []),
            "tongue_analysis": structured.get("tongue_analysis", []),
            "eye_analysis": structured.get("eye_analysis", []),
            "fusion_summary": self._fusion_summary(diagnosis),
            "diagnosis_mode": diagnosis.get("diagnosis_mode")
            or ("metrics" if not diagnosis.get("fusion_data") else None),
            "llm_fallback_reason": diagnosis.get("llm_fallback_reason"),
        }

    def run(self, vision_data: Dict[str, Any], stm_data: Dict[str, Any]) -> Dict[str, Any]:
        stm_data = dict(stm_data)
        vitals = self.resolve_vitals_assessment(stm_data)
        stm_data["vitals_assessment"] = vitals
        if vitals.get("heart_rate"):
            stm_data["heart_rate"] = int(vitals["heart_rate"])
            stm_data["pulse"] = int(vitals.get("pulse") or vitals["heart_rate"])
        if vitals.get("spo2"):
            stm_data["spo2"] = vitals["spo2"]

        vitals_block = (
            f"\n### 生理参数（MAX30102）\n"
            f"- **心率**：{vitals.get('heart_rate', '--')} bpm（{vitals.get('hr_status', '')}）\n"
            f"- **血氧**：{vitals.get('spo2', '--')}%（{vitals.get('spo2_status', '')}）\n"
            f"- **综合**：{vitals.get('overall_status', '')}\n"
        )

        if vision_data:
            diagnosis = self.tcm_agent.get_tcm_diagnosis(vision_data, stm_data)
            diagnosis_result = diagnosis["diagnosis"]

            if "生理参数" not in diagnosis_result and "心率" not in diagnosis_result:
                diagnosis_result += vitals_block

            return self._format_response(diagnosis, diagnosis_result, vitals)

        simple_diagnosis = (
            "1. 中医辨证：气血不足\n"
            "2. 证候分析：根据健康指标分析，您的身体状况基本正常。建议保持良好的生活习惯。\n"
            "3. 建议：1. 饮食均衡，多食用新鲜蔬菜水果；2. 保持充足睡眠，避免熬夜；"
            "3. 适当运动，增强体质；4. 定期体检。\n"
            f"{vitals_block}"
        )
        fallback = {
            "diagnosis": simple_diagnosis,
            "source": "中医智能诊断系统(基于健康指标)",
            "diagnosis_mode": "metrics",
            "structured": {
                "syndrome": "气血不足",
                "analysis": "根据健康指标分析，您的身体状况基本正常。建议保持良好的生活习惯。",
                "suggestions": [
                    "饮食均衡，多食用新鲜蔬菜水果",
                    "保持充足睡眠，避免熬夜",
                    "适当运动，增强体质",
                    "定期体检",
                ],
                "prescriptions": [],
                "face_analysis": [],
                "tongue_analysis": [],
                "eye_analysis": [],
            },
        }
        return self._format_response(fallback, simple_diagnosis, vitals)
