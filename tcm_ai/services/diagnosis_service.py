from typing import TYPE_CHECKING, Any, Dict, Optional

from tcm_ai.domain.constants import DEFAULT_PULSE_CHARACTERISTICS, DISCLAIMER
from tcm_ai.domain.diagnosis_parser import parse_diagnosis_markdown

if TYPE_CHECKING:
    from tcm_ai.services.tcm_agent import TCMAgent


class DiagnosisService:
    def __init__(self, tcm_agent: Optional["TCMAgent"] = None) -> None:
        self._tcm_agent = tcm_agent

    @property
    def tcm_agent(self) -> "TCMAgent":
        if self._tcm_agent is None:
            from tcm_ai.services.tcm_agent import TCMAgent

            self._tcm_agent = TCMAgent()
        return self._tcm_agent

    def build_pulse_characteristics(
        self,
        heart_rate: int,
        pulse: int,
        age: Optional[int] = None,
        gender: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            from tcm_ai.services.pulse_service import PulseDiagnosisTool

            pulse_tool = PulseDiagnosisTool(self.tcm_agent)
            prepared_pulse_data = {
                "heart_rate": heart_rate,
                "spo2": 98.0,
                "pulse_characteristics": {
                    "pulse_shape": "正常",
                    "pulse_strength": "中等",
                    "pulse_rate": "正常" if 60 <= pulse <= 100 else ("慢" if pulse < 60 else "快"),
                    "tcm_interpretation": "迟脉" if pulse < 60 else ("数脉" if pulse > 100 else "平和脉"),
                },
                "pulse_waveform": [],
            }
            pulse_result = pulse_tool.run(prepared_pulse_data)
            return {
                "pulse_type": pulse_result.get("pulse_type", "平和脉"),
                "description": pulse_result.get("pulse_info", {}).get(
                    "description",
                    "脉象平和，节律均匀，力度适中，一息四至，不浮不沉，不快不慢。",
                ),
                "characteristics": {
                    "rate": prepared_pulse_data["pulse_characteristics"]["pulse_rate"],
                    "rhythm": "整齐",
                    "strength": prepared_pulse_data["pulse_characteristics"]["pulse_strength"],
                    "depth": "适中",
                },
                "possible_conditions": [
                    pulse_result.get("pulse_info", {}).get(
                        "interpretation", "气血调和，阴阳平衡，健康状态良好。"
                    )
                ],
                "treatment_recommendations": [
                    pulse_result.get("pulse_info", {}).get(
                        "suggestion", "保持良好的生活习惯，均衡饮食，适量运动，保持心情舒畅。"
                    )
                ],
            }
        except Exception as exc:
            print(f"脉搏诊断错误: {exc}")
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
        pulse_chars: Dict[str, Any],
    ) -> Dict[str, Any]:
        structured = self._structured_from_diagnosis({**diagnosis, "diagnosis": diagnosis_text})
        return {
            "diagnosis": diagnosis_text,
            "source": diagnosis.get("source", ""),
            "pulse_characteristics": pulse_chars,
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
        heart_rate = stm_data.get("heart_rate")
        pulse = stm_data.get("pulse", heart_rate)

        if heart_rate is not None and pulse is not None:
            stm_data["pulse_characteristics"] = self.build_pulse_characteristics(
                int(heart_rate), int(pulse), stm_data.get("age"), stm_data.get("gender")
            )

        pulse_chars = stm_data.get("pulse_characteristics", DEFAULT_PULSE_CHARACTERISTICS)

        if vision_data:
            diagnosis = self.tcm_agent.get_tcm_diagnosis(vision_data, stm_data)
            diagnosis_result = diagnosis["diagnosis"]

            if "脉象" not in diagnosis_result and "脉搏" not in diagnosis_result:
                diagnosis_result += (
                    f"\n### 脉象分析\n- **脉象类型**：{pulse_chars['pulse_type']}\n"
                    f"- **脉象描述**：{pulse_chars['description']}\n"
                )

            return self._format_response(diagnosis, diagnosis_result, pulse_chars)

        simple_diagnosis = (
            "1. 中医辨证：气血不足\n"
            "2. 证候分析：根据健康指标分析，您的身体状况基本正常。建议保持良好的生活习惯。\n"
            "3. 建议：1. 饮食均衡，多食用新鲜蔬菜水果；2. 保持充足睡眠，避免熬夜；"
            "3. 适当运动，增强体质；4. 定期体检。\n\n"
            f"### 脉象分析\n- **脉象类型**：{pulse_chars['pulse_type']}\n"
            f"- **脉象描述**：{pulse_chars['description']}\n"
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
        return self._format_response(fallback, simple_diagnosis, pulse_chars)
