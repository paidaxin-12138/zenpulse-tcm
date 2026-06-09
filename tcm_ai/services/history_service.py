# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import os
from typing import Any, Dict, List, Optional

from tcm_ai.repositories.diagnosis_history import (
    HISTORY_DETAIL_DIR as _DEFAULT_DETAIL_DIR,
    HISTORY_PATH as _DEFAULT_HISTORY_PATH,
    HISTORY_USER_DIR as _DEFAULT_USER_DIR,
    JsonDiagnosisHistoryRepository,
    get_diagnosis_history_repository,
)

# 兼容既有测试 monkeypatch
HISTORY_PATH = _DEFAULT_HISTORY_PATH
HISTORY_USER_DIR = _DEFAULT_USER_DIR
HISTORY_DETAIL_DIR = _DEFAULT_DETAIL_DIR

__all__ = ["DiagnosisHistoryService", "HISTORY_PATH", "HISTORY_USER_DIR", "HISTORY_DETAIL_DIR"]


class DiagnosisHistoryService:
    def __init__(self, repository=None) -> None:
        if repository is None:
            backend = os.environ.get("TCM_HISTORY_BACKEND", "json").strip().lower()
            if backend == "sql":
                self._repo = get_diagnosis_history_repository()
            else:
                self._repo = JsonDiagnosisHistoryRepository(
                    global_path=HISTORY_PATH,
                    user_dir=HISTORY_USER_DIR,
                    detail_dir=HISTORY_DETAIL_DIR,
                )
        else:
            self._repo = repository

    def list_entries(self, limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._repo.list_entries(limit=limit, user_id=user_id)

    def get_entry(self, entry_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        return self._repo.get_entry(entry_id, user_id=user_id)

    def add_entry(self, payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        return self._repo.add_entry(payload, user_id=user_id)

    def clear(self, user_id: Optional[str] = None) -> int:
        return self._repo.clear(user_id=user_id)

    def delete_entry(self, entry_id: str, user_id: Optional[str] = None) -> bool:
        return self._repo.delete_entry(entry_id, user_id=user_id)
