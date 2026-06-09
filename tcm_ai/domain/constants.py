DISCLAIMER = "本结果仅供参考，不能替代专业医疗诊断，如有不适请及时就医。"

DEFAULT_VITALS_ASSESSMENT = {
    "success": False,
    "heart_rate": 0.0,
    "pulse": 0,
    "spo2": 0.0,
    "hr_status": "未知",
    "spo2_status": "未知",
    "overall_status": "待测量",
    "alerts": ["未采集到 MAX30102 数据"],
    "suggestions": ["请通过蓝牙连接腕带采集，或手动填写心率"],
    "quality_score": 0.0,
    "source": "fallback",
    "sample_count": 0,
    "duration_sec": 0.0,
    "limitations": ["数据来自 MAX30102 光学传感器估算，非医疗级设备"],
}

DEFAULT_PULSE_CHARACTERISTICS = {
    "pulse_type": "平和脉",
    "description": "脉象数据不可用，已使用默认占位说明。",
    "confidence": 0.0,
    "source": "fallback",
    "capability_level": "L0",
    "limitations": ["脉象分析失败或数据缺失"],
    "characteristics": {
        "rate": "正常",
        "rhythm": "齐",
        "strength": None,
        "depth": None,
        "shape": None,
    },
    "waveform_stats": {},
    "research_features": {},
    "pulse_waveform": [],
    "quality": {"score": 0.0, "valid_beat_ratio": 0.0},
    "possible_conditions": [],
    "treatment_recommendations": [],
}
