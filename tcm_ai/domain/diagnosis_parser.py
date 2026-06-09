# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import re
from typing import Any, Dict, List


def _lines_to_bullets(text: str) -> List[str]:
    items: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*•]\s*", "", line)
        line = re.sub(r"^\d+[.)]\s*", "", line)
        if line and not line.endswith("：") and line not in ("生活调理：", "饮食建议：", "中药药方："):
            items.append(line)
    return items


def parse_diagnosis_markdown(text: str) -> Dict[str, Any]:
    """从 Markdown/纯文本诊断报告中提取结构化字段。"""
    result: Dict[str, Any] = {
        "syndrome": "",
        "analysis": "",
        "face_analysis": [],
        "tongue_analysis": [],
        "eye_analysis": [],
        "suggestions": [],
        "prescriptions": [],
    }
    if not text:
        return result

    syndrome_match = re.search(
        r"(?:中医辨证|1\.\s*中医辨证)[：:]\s*(.+?)(?:\n|$)", text
    )
    if syndrome_match:
        result["syndrome"] = syndrome_match.group(1).strip()

    analysis_match = re.search(
        r"(?:证候分析|3\.\s*证候分析)[：:]\s*(.+?)(?=\n\d+\.|\n###|\n\d+\.\s*调理|\Z)",
        text,
        re.DOTALL,
    )
    if analysis_match:
        result["analysis"] = analysis_match.group(1).strip()

    face_match = re.search(r"面部分析[：:]\s*(.+?)(?:\n|$)", text)
    if face_match:
        result["face_analysis"] = [face_match.group(1).strip()]

    tongue_match = re.search(r"舌苔分析[：:]\s*(.+?)(?:\n|$)", text)
    if tongue_match:
        result["tongue_analysis"] = [tongue_match.group(1).strip()]

    eye_match = re.search(r"眼睛分析[：:]\s*(.+?)(?:\n|$)", text)
    if eye_match:
        result["eye_analysis"] = [eye_match.group(1).strip()]

    suggestions_match = re.search(
        r"(?:调理建议|4\.\s*调理建议)[：:]\s*(.+?)(?=\n\d+\.\s*中药|\n5\.\s*中药|\Z)",
        text,
        re.DOTALL,
    )
    if suggestions_match:
        result["suggestions"] = _lines_to_bullets(suggestions_match.group(1))

    prescriptions_match = re.search(
        r"(?:中药药方|5\.\s*中药药方)[：:]\s*(.+?)(?=\n###|\Z)",
        text,
        re.DOTALL,
    )
    if prescriptions_match:
        result["prescriptions"] = _lines_to_bullets(prescriptions_match.group(1))

    if not result["syndrome"]:
        for line in text.splitlines():
            if "证" in line and len(line) < 40:
                result["syndrome"] = line.strip()
                break

    return result


def merge_structured(
    primary: Dict[str, Any], fallback: Dict[str, Any]
) -> Dict[str, Any]:
    merged = dict(fallback)
    for key, value in primary.items():
        if isinstance(value, list):
            merged[key] = value if value else fallback.get(key, [])
        elif value:
            merged[key] = value
    return merged
