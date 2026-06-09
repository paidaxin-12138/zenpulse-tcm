# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""诊断历史仓储：默认 JSON 实现，可选 SQLite（TCM_HISTORY_BACKEND=sql）。"""

from __future__ import annotations

from tcm_ai.core.json_io import read_json_file, update_json_file, write_json_file
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tcm_ai.core.paths import DATA_DIR

HISTORY_PATH = os.path.join(DATA_DIR, "diagnosis_history.json")
HISTORY_USER_DIR = os.path.join(DATA_DIR, "history")
HISTORY_DETAIL_DIR = os.path.join(DATA_DIR, "history_details")

MAX_ENTRIES = 200
SUMMARY_KEYS = (
    "id",
    "time",
    "syndrome",
    "diagnosis",
    "summary",
    "diagnosis_mode",
    "has_detail",
)


class DiagnosisHistoryRepository(ABC):
    @abstractmethod
    def list_entries(self, limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_entry(self, entry_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def add_entry(self, payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def clear(self, user_id: Optional[str] = None) -> int:
        raise NotImplementedError

    @abstractmethod
    def delete_entry(self, entry_id: str, user_id: Optional[str] = None) -> bool:
        raise NotImplementedError


class JsonDiagnosisHistoryRepository(DiagnosisHistoryRepository):
    DEFAULT_GLOBAL_PATH = HISTORY_PATH
    DEFAULT_USER_DIR = HISTORY_USER_DIR
    DEFAULT_DETAIL_DIR = HISTORY_DETAIL_DIR

    def __init__(
        self,
        global_path: str = HISTORY_PATH,
        user_dir: str = HISTORY_USER_DIR,
        detail_dir: str = HISTORY_DETAIL_DIR,
    ) -> None:
        self.global_path = global_path
        self.user_dir = user_dir
        self.detail_dir = detail_dir

    def _path_for_user(self, user_id: Optional[str]) -> str:
        if user_id:
            os.makedirs(self.user_dir, exist_ok=True)
            return os.path.join(self.user_dir, f"{user_id}.json")
        return self.global_path

    def _detail_scope(self, user_id: Optional[str]) -> str:
        scope = user_id or "_anonymous"
        path = os.path.join(self.detail_dir, scope)
        os.makedirs(path, exist_ok=True)
        return path

    def _detail_path(self, entry_id: str, user_id: Optional[str]) -> str:
        safe_id = entry_id.replace("/", "_").replace("\\", "_")
        return os.path.join(self._detail_scope(user_id), f"{safe_id}.json")

    def _ensure_file(self, user_id: Optional[str] = None) -> None:
        path = self._path_for_user(user_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            self._write([], user_id=user_id)

    def _read(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        self._ensure_file(user_id)
        path = self._path_for_user(user_id)
        data = read_json_file(path, [])
        return data if isinstance(data, list) else []

    def _write(self, items: List[Dict[str, Any]], user_id: Optional[str] = None) -> None:
        path = self._path_for_user(user_id)
        write_json_file(path, items[:MAX_ENTRIES])

    def _read_detail(self, entry_id: str, user_id: Optional[str]) -> Optional[Dict[str, Any]]:
        path = self._detail_path(entry_id, user_id)
        data = read_json_file(path, None)
        return data if isinstance(data, dict) else None

    def _write_detail(
        self, entry_id: str, detail: Dict[str, Any], user_id: Optional[str]
    ) -> None:
        path = self._detail_path(entry_id, user_id)
        write_json_file(path, detail)

    def _remove_detail(self, entry_id: str, user_id: Optional[str]) -> None:
        path = self._detail_path(entry_id, user_id)
        if os.path.isfile(path):
            os.remove(path)

    def _clear_details(self, user_id: Optional[str]) -> None:
        scope = self._detail_scope(user_id)
        if not os.path.isdir(scope):
            return
        for name in os.listdir(scope):
            if name.endswith(".json"):
                os.remove(os.path.join(scope, name))

    @staticmethod
    def _to_summary(entry: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": entry.get("id", ""),
            "time": entry.get("time", ""),
            "syndrome": entry.get("syndrome", ""),
            "diagnosis": entry.get("diagnosis", ""),
            "summary": entry.get("summary", ""),
            "diagnosis_mode": entry.get("diagnosis_mode", ""),
            "has_detail": bool(entry.get("has_detail")),
        }

    def list_entries(self, limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        items = self._read(user_id)[: max(1, min(limit, MAX_ENTRIES))]
        return [self._to_summary(item) for item in items]

    def get_entry(self, entry_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        for item in self._read(user_id):
            if item.get("id") != entry_id:
                continue
            entry = self._to_summary(item)
            detail = self._read_detail(entry_id, user_id)
            if detail:
                entry["detail"] = detail
            return entry
        return None

    def add_entry(self, payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "time": payload.get("time")
            or datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            "syndrome": payload.get("syndrome", ""),
            "diagnosis": payload.get("diagnosis", ""),
            "summary": payload.get("summary", ""),
            "diagnosis_mode": payload.get("diagnosis_mode", ""),
            "has_detail": False,
        }

        detail = payload.get("detail")
        if isinstance(detail, dict) and detail:
            self._write_detail(entry_id, detail, user_id)
            entry["has_detail"] = True
            entry["syndrome"] = entry["syndrome"] or detail.get("syndrome", "")
            entry["diagnosis"] = entry["diagnosis"] or detail.get("diagnosis", "")
            entry["summary"] = (
                entry["summary"]
                or detail.get("analysis")
                or detail.get("summary")
                or entry["syndrome"]
            )
            entry["diagnosis_mode"] = (
                entry["diagnosis_mode"] or detail.get("diagnosis_mode", "")
            )

        path = self._path_for_user(user_id)
        self._ensure_file(user_id)

        def _insert(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if not isinstance(items, list):
                items = []
            items.insert(0, entry)
            return items[:MAX_ENTRIES]

        update_json_file(path, [], _insert)

        result = self._to_summary(entry)
        if entry["has_detail"]:
            result["detail"] = self._read_detail(entry_id, user_id)
        return result

    def clear(self, user_id: Optional[str] = None) -> int:
        path = self._path_for_user(user_id)
        self._ensure_file(user_id)
        count_holder: List[int] = [0]

        def _clear(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if not isinstance(items, list):
                items = []
            count_holder[0] = len(items)
            return []

        update_json_file(path, [], _clear)
        self._clear_details(user_id)
        return count_holder[0]

    def delete_entry(self, entry_id: str, user_id: Optional[str] = None) -> bool:
        path = self._path_for_user(user_id)
        self._ensure_file(user_id)
        removed: List[bool] = [False]

        def _delete(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if not isinstance(items, list):
                items = []
            new_items = [item for item in items if item.get("id") != entry_id]
            removed[0] = len(new_items) != len(items)
            return new_items

        update_json_file(path, [], _delete)
        if not removed[0]:
            return False
        self._remove_detail(entry_id, user_id)
        return True


def get_diagnosis_history_repository() -> DiagnosisHistoryRepository:
    backend = os.environ.get("TCM_HISTORY_BACKEND", "json").strip().lower()
    if backend == "sql":
        from tcm_ai.repositories.sql_diagnosis_history import SqlDiagnosisHistoryRepository

        return SqlDiagnosisHistoryRepository()
    return JsonDiagnosisHistoryRepository()
