import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from tcm_ai.core.json_io import read_json_file, update_json_file, write_json_file
from tcm_ai.core.paths import PATIENTS_PATH, VISITS_DIR


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class PatientService:
    """真实患者档案与就诊记录（与 RAG 病例库分离）。"""

    def __init__(
        self,
        patients_path: str = PATIENTS_PATH,
        visits_dir: str = VISITS_DIR,
    ) -> None:
        self.patients_path = Path(patients_path)
        self.visits_dir = Path(visits_dir)

    def _ensure_dirs(self) -> None:
        self.patients_path.parent.mkdir(parents=True, exist_ok=True)
        self.visits_dir.mkdir(parents=True, exist_ok=True)

    def _load_patients(self) -> List[Dict[str, Any]]:
        self._ensure_dirs()
        if not self.patients_path.is_file():
            self._save_patients([])
            return []
        data = read_json_file(str(self.patients_path), [])
        if not isinstance(data, list):
            raise ValueError("patients.json 格式应为数组")
        return data

    def _save_patients(self, patients: List[Dict[str, Any]]) -> None:
        self._ensure_dirs()
        write_json_file(str(self.patients_path), patients)

    def _new_patient_id(self) -> str:
        stamp = datetime.now().strftime("%Y%m%d")
        suffix = secrets.token_hex(3)
        return f"P{stamp}{suffix}"

    @staticmethod
    def _patient_summary(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "patient_id": row["patient_id"],
            "name": row.get("name", ""),
            "gender": row.get("gender", ""),
            "age": row.get("age"),
            "phone": row.get("phone", ""),
            "id_number": row.get("id_number", ""),
            "address": row.get("address", ""),
            "constitution": row.get("constitution", ""),
            "allergies": row.get("allergies", ""),
            "notes": row.get("notes", ""),
            "status": row.get("status", "active"),
            "created_at": row.get("created_at", ""),
            "updated_at": row.get("updated_at", ""),
        }

    def list_patients(
        self, limit: int = 50, offset: int = 0, q: str = ""
    ) -> Dict[str, Any]:
        patients = [self._patient_summary(p) for p in self._load_patients()]
        if q:
            needle = q.lower()
            patients = [
                p
                for p in patients
                if needle
                in " ".join(
                    str(p.get(k, ""))
                    for k in ("patient_id", "name", "phone", "gender", "notes")
                ).lower()
            ]
        page = patients[offset : offset + limit]
        return {"total": len(patients), "offset": offset, "limit": limit, "patients": page}

    def get_patient(self, patient_id: str) -> Dict[str, Any]:
        for row in self._load_patients():
            if row.get("patient_id") == patient_id:
                return self._patient_summary(row)
        raise KeyError(patient_id)

    def create_patient(self, data: Dict[str, Any]) -> Dict[str, Any]:
        patient_id = (data.get("patient_id") or "").strip() or self._new_patient_id()
        now = _now_iso()
        row = {
            "patient_id": patient_id,
            "name": data.get("name", "").strip(),
            "gender": data.get("gender", "").strip(),
            "age": data.get("age"),
            "phone": data.get("phone", "").strip(),
            "id_number": data.get("id_number", "").strip(),
            "address": data.get("address", "").strip(),
            "constitution": data.get("constitution", "").strip(),
            "allergies": data.get("allergies", "").strip(),
            "notes": data.get("notes", "").strip(),
            "status": data.get("status") or "active",
            "created_at": now,
            "updated_at": now,
        }
        if not row["name"]:
            raise ValueError("姓名不能为空")

        def _add(patients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if not isinstance(patients, list):
                patients = []
            if any(p.get("patient_id") == patient_id for p in patients):
                raise ValueError(f"患者 ID 已存在: {patient_id}")
            patients.append(row)
            return patients

        self._ensure_dirs()
        update_json_file(str(self.patients_path), [], _add)
        self._save_visits(patient_id, [])
        return self._patient_summary(row)

    def update_patient(self, patient_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        def _apply(patients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if not isinstance(patients, list):
                patients = []
            for i, row in enumerate(patients):
                if row.get("patient_id") != patient_id:
                    continue
                merged = {**row, **updates, "patient_id": patient_id, "updated_at": _now_iso()}
                if "name" in updates and not str(merged.get("name", "")).strip():
                    raise ValueError("姓名不能为空")
                patients[i] = merged
                result.clear()
                result.update(self._patient_summary(merged))
                return patients
            raise KeyError(patient_id)

        self._ensure_dirs()
        update_json_file(str(self.patients_path), [], _apply)
        return result

    def delete_patient(self, patient_id: str) -> Dict[str, str]:
        def _remove(patients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if not isinstance(patients, list):
                patients = []
            new_rows = [p for p in patients if p.get("patient_id") != patient_id]
            if len(new_rows) == len(patients):
                raise KeyError(patient_id)
            return new_rows

        self._ensure_dirs()
        update_json_file(str(self.patients_path), [], _remove)
        visit_file = self.visits_dir / f"{patient_id}.json"
        if visit_file.is_file():
            visit_file.unlink()
        return {"deleted": patient_id}

    def _visit_path(self, patient_id: str) -> Path:
        safe = patient_id.replace("/", "_").replace("\\", "_")
        return self.visits_dir / f"{safe}.json"

    def _load_visits(self, patient_id: str) -> List[Dict[str, Any]]:
        self.get_patient(patient_id)
        path = self._visit_path(patient_id)
        if not path.is_file():
            return []
        data = read_json_file(str(path), [])
        return data if isinstance(data, list) else []

    def _save_visits(self, patient_id: str, visits: List[Dict[str, Any]]) -> None:
        self._ensure_dirs()
        path = self._visit_path(patient_id)
        write_json_file(str(path), visits)

    def list_visits(self, patient_id: str) -> Dict[str, Any]:
        visits = self._load_visits(patient_id)
        visits.sort(key=lambda v: v.get("visit_date", ""), reverse=True)
        return {"patient_id": patient_id, "total": len(visits), "visits": visits}

    def create_visit(self, patient_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        visit_id = f"V{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(2)}"
        row = {
            "visit_id": visit_id,
            "patient_id": patient_id,
            "visit_date": data.get("visit_date") or datetime.now().strftime("%Y-%m-%d"),
            "chief_complaint": data.get("chief_complaint", "").strip(),
            "symptoms": data.get("symptoms", "").strip(),
            "diagnosis": data.get("diagnosis", "").strip(),
            "syndrome": data.get("syndrome", "").strip(),
            "treatment": data.get("treatment", "").strip(),
            "efficacy": data.get("efficacy", "").strip(),
            "notes": data.get("notes", "").strip(),
            "source": data.get("source") or "manual",
            "created_at": _now_iso(),
        }
        self.get_patient(patient_id)
        path = str(self._visit_path(patient_id))

        def _append(visits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if not isinstance(visits, list):
                visits = []
            visits.append(row)
            return visits

        self._ensure_dirs()
        update_json_file(path, [], _append)
        return row
