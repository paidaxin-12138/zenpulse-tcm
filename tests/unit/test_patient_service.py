from pathlib import Path

import pytest

from tcm_ai.services.patient_service import PatientService


@pytest.fixture
def patient_service(tmp_path: Path) -> PatientService:
    return PatientService(
        patients_path=str(tmp_path / "patients.json"),
        visits_dir=str(tmp_path / "visits"),
    )


def test_patient_crud(patient_service: PatientService) -> None:
    created = patient_service.create_patient({"name": "张三", "gender": "男", "age": 35})
    assert created["name"] == "张三"
    assert created["patient_id"].startswith("P")

    listed = patient_service.list_patients(q="张三")
    assert listed["total"] == 1

    updated = patient_service.update_patient(
        created["patient_id"], {"phone": "13800000000", "notes": "复诊提醒"}
    )
    assert updated["phone"] == "13800000000"

    visit = patient_service.create_visit(
        created["patient_id"],
        {"chief_complaint": "头痛", "syndrome": "肝阳上亢", "diagnosis": "头痛"},
    )
    visits = patient_service.list_visits(created["patient_id"])
    assert visits["total"] == 1
    assert visits["visits"][0]["visit_id"] == visit["visit_id"]

    patient_service.delete_patient(created["patient_id"])
    with pytest.raises(KeyError):
        patient_service.get_patient(created["patient_id"])


def test_create_patient_requires_name(patient_service: PatientService) -> None:
    with pytest.raises(ValueError):
        patient_service.create_patient({"name": "  "})
