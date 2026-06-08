from tcm_ai.domain.rules import RuleEngine


def test_rule_engine_pale_tongue():
    vision = {
        "tongue": {
            "color": {"hsv": [10.0, 0.2, 0.6]},
            "coating": {"coating_ratio": 0.2},
        }
    }
    stm = {"heart_rate": 75, "systolic_pressure": 120, "diastolic_pressure": 80}
    result = RuleEngine.diagnose(vision, stm)
    assert "diagnosis" in result
    assert result["source"].endswith("(基于规则模式)")
