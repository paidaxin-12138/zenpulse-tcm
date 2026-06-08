from tcm_ai.domain.diagnosis_parser import parse_diagnosis_markdown


SAMPLE = """1. 中医辨证：气血不足
2. 望诊部位分析：
   面部分析：面色苍白无华，提示气血不足
   舌苔分析：舌质淡嫩，提示气血不足
3. 证候分析：根据望诊和生理参数分析，患者主要表现为气血不足。
4. 调理建议：
- 避免过度劳累，保证充足睡眠
- 宜多食用红枣、桂圆
5. 中药药方：
1. 八珍汤加减（补益气血）
2. 归脾汤加减（益气补血）
"""


def test_parse_syndrome_and_analysis():
    parsed = parse_diagnosis_markdown(SAMPLE)
    assert parsed["syndrome"] == "气血不足"
    assert "气血不足" in parsed["analysis"]
    assert len(parsed["face_analysis"]) == 1
    assert len(parsed["tongue_analysis"]) == 1
    assert any("睡眠" in s for s in parsed["suggestions"])
    assert any("八珍汤" in p for p in parsed["prescriptions"])


def test_parse_empty():
    parsed = parse_diagnosis_markdown("")
    assert parsed["syndrome"] == ""
    assert parsed["suggestions"] == []
