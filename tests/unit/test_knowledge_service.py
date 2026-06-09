# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import json
from pathlib import Path

import pytest

from tcm_ai.services.knowledge_service import KnowledgeService
from tcm_ai.services.patient_service import PatientService


@pytest.fixture
def knowledge_dir(tmp_path: Path) -> Path:
    cases = tmp_path / "cases"
    cases.mkdir()
    (cases / "clinical_cases.json").write_text("[]", encoding="utf-8")
    return tmp_path


def test_list_nested_case_files(knowledge_dir: Path) -> None:
    nested = {
        "cases": [
            {
                "case_id": "case_9001",
                "patient_id": "pt_9001",
                "age": 40,
                "gender": "男",
                "symptoms": "咳嗽",
                "diagnosis": "咳嗽",
                "syndrome": "风寒袭肺",
            }
        ]
    }
    (knowledge_dir / "cases" / "clinical_cases_001.json").write_text(
        json.dumps(nested, ensure_ascii=False),
        encoding="utf-8",
    )
    svc = KnowledgeService(str(knowledge_dir))
    data = svc.list_case_library(limit=10)
    assert data["total"] == 1
    assert data["cases"][0]["patient_id"] == "pt_9001"
    assert svc.get_case_library_entry("case_9001")["syndrome"] == "风寒袭肺"


def test_upload_file_bytes(knowledge_dir: Path) -> None:
    svc = KnowledgeService(str(knowledge_dir))
    result = svc.upload_file("note.txt", b"hello", subdir="imports")
    assert result["path"] == "imports/note.txt"
    assert (knowledge_dir / "imports" / "note.txt").read_bytes() == b"hello"


def test_case_library_pagination(knowledge_dir: Path) -> None:
    cases = [{"case_id": f"case_{i}", "symptoms": f"症状{i}", "diagnosis": "测试"} for i in range(5)]
    (knowledge_dir / "cases" / "batch.json").write_text(
        json.dumps({"cases": cases}, ensure_ascii=False),
        encoding="utf-8",
    )
    svc = KnowledgeService(str(knowledge_dir))
    assert svc.case_library_stats()["case_count"] == 5
    page1 = svc.list_case_library(limit=2, offset=0)
    page2 = svc.list_case_library(limit=2, offset=2)
    assert page1["total"] == 5
    assert len(page1["cases"]) == 2
    assert len(page2["cases"]) == 2
    assert page1["cases"][0]["case_id"] == "case_0"


def test_case_search_synonym_touteng(knowledge_dir: Path) -> None:
    nested = {
        "cases": [
            {
                "case_id": "case_h1",
                "symptoms": "头痛，失眠",
                "diagnosis": "头痛",
                "syndrome": "肝火上扰证",
            }
        ]
    }
    (knowledge_dir / "cases" / "clinical_cases_001.json").write_text(
        json.dumps(nested, ensure_ascii=False),
        encoding="utf-8",
    )
    svc = KnowledgeService(str(knowledge_dir))
    assert svc.list_case_library(q="头疼")["total"] == 1
    assert svc.list_case_library(q="头痛")["total"] == 1


def test_delete_file(knowledge_dir: Path) -> None:
    svc = KnowledgeService(str(knowledge_dir))
    target = knowledge_dir / "basic_theory" / "note.txt"
    target.parent.mkdir()
    target.write_text("内容", encoding="utf-8")
    result = svc.delete_file("basic_theory/note.txt")
    assert result["deleted"] == "basic_theory/note.txt"
    assert not target.exists()
