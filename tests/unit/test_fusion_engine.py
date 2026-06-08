from tcm_ai.domain.fusion import FusionEngine


def test_process_vision_data_defaults():
    result = FusionEngine.process_vision_data({})
    assert result["face"] is None
    assert result["quality"]["overall_quality"] == 0.0


def test_fuse_with_tongue_pale():
    vision = FusionEngine.process_vision_data(
        {
            "tongue": {
                "color": {"hsv": [10.0, 0.2, 0.6]},
                "coating": {"coating_ratio": 0.2},
            }
        }
    )
    stm = FusionEngine.process_stm_data({"heart_rate": 75, "systolic_pressure": 120, "diastolic_pressure": 80})
    fusion = FusionEngine.fuse(vision, stm)
    assert fusion["weighted_features"].get("tongue_color") == "淡白"
    assert fusion["overall_confidence"] >= 0
