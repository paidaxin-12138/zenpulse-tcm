# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""诊断历史 SQLite 仓储。"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tcm_ai.db.sqlite import ensure_database, parse_sqlite_path
from tcm_ai.repositories.diagnosis_history import (
    MAX_ENTRIES,
    DiagnosisHistoryRepository,
)

_SCHEMA_READY: set[str] = set()


def _now_str() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def _user_key(user_id: Optional[str]) -> Optional[str]:
    return user_id or None


class SqlDiagnosisHistoryRepository(DiagnosisHistoryRepository):
    def __init__(self, database_url: str = "") -> None:
        self.db_path = parse_sqlite_path(
            database_url
            or os.environ.get("TCM_HISTORY_DATABASE_URL", "")
        )
        if self.db_path not in _SCHEMA_READY:
            ensure_database(self.db_path)
            _SCHEMA_READY.add(self.db_path)

    def _connect(self):
        from tcm_ai.db.sqlite import connect

        return connect(self.db_path)

    @staticmethod
    def _row_to_summary(row) -> Dict[str, Any]:
        detail_json = row["detail_json"]
        return {
            "id": row["id"],
            "time": row["time"],
            "syndrome": row["syndrome"] or "",
            "diagnosis": row["diagnosis"] or "",
            "summary": row["summary"] or "",
            "diagnosis_mode": row["diagnosis_mode"] or "",
            "has_detail": bool(detail_json),
        }

    def list_entries(self, limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        lim = max(1, min(limit, MAX_ENTRIES))
        uid = _user_key(user_id)
        with self._connect() as conn:
            if uid is None:
                rows = conn.execute(
                    """
                    SELECT id, time, syndrome, diagnosis, summary, diagnosis_mode, detail_json
                    FROM diagnosis_history
                    WHERE user_id IS NULL
                    ORDER BY time DESC
                    LIMIT ?
                    """,
                    (lim,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, time, syndrome, diagnosis, summary, diagnosis_mode, detail_json
                    FROM diagnosis_history
                    WHERE user_id = ?
                    ORDER BY time DESC
                    LIMIT ?
                    """,
                    (uid, lim),
                ).fetchall()
        return [self._row_to_summary(row) for row in rows]

    def get_entry(self, entry_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        uid = _user_key(user_id)
        with self._connect() as conn:
            if uid is None:
                row = conn.execute(
                    """
                    SELECT id, time, syndrome, diagnosis, summary, diagnosis_mode, detail_json
                    FROM diagnosis_history
                    WHERE id = ? AND user_id IS NULL
                    """,
                    (entry_id,),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT id, time, syndrome, diagnosis, summary, diagnosis_mode, detail_json
                    FROM diagnosis_history
                    WHERE id = ? AND user_id = ?
                    """,
                    (entry_id, uid),
                ).fetchone()
        if not row:
            return None
        entry = self._row_to_summary(row)
        if row["detail_json"]:
            try:
                entry["detail"] = json.loads(row["detail_json"])
            except json.JSONDecodeError:
                entry["detail"] = {}
        return entry

    def add_entry(self, payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        entry_id = str(payload.get("id") or uuid.uuid4())
        now = _now_str()
        entry = {
            "id": entry_id,
            "time": payload.get("time") or now,
            "syndrome": payload.get("syndrome", ""),
            "diagnosis": payload.get("diagnosis", ""),
            "summary": payload.get("summary", ""),
            "diagnosis_mode": payload.get("diagnosis_mode", ""),
            "has_detail": False,
        }
        detail = payload.get("detail")
        detail_json = None
        if isinstance(detail, dict) and detail:
            detail_json = json.dumps(detail, ensure_ascii=False)
            entry["has_detail"] = True
            entry["syndrome"] = entry["syndrome"] or detail.get("syndrome", "")
            entry["diagnosis"] = entry["diagnosis"] or detail.get("diagnosis", "")
            entry["summary"] = (
                entry["summary"]
                or detail.get("analysis")
                or detail.get("summary")
                or entry["syndrome"]
            )
            entry["diagnosis_mode"] = entry["diagnosis_mode"] or detail.get("diagnosis_mode", "")

        uid = _user_key(user_id)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO diagnosis_history (
                    id, user_id, time, syndrome, diagnosis, summary,
                    diagnosis_mode, detail_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    uid,
                    entry["time"],
                    entry["syndrome"],
                    entry["diagnosis"],
                    entry["summary"],
                    entry["diagnosis_mode"],
                    detail_json,
                    now,
                    now,
                ),
            )
            if uid is None:
                conn.execute(
                    """
                    DELETE FROM diagnosis_history
                    WHERE user_id IS NULL AND id NOT IN (
                        SELECT id FROM diagnosis_history
                        WHERE user_id IS NULL
                        ORDER BY time DESC
                        LIMIT ?
                    )
                    """,
                    (MAX_ENTRIES,),
                )
            else:
                conn.execute(
                    """
                    DELETE FROM diagnosis_history
                    WHERE user_id = ? AND id NOT IN (
                        SELECT id FROM diagnosis_history
                        WHERE user_id = ?
                        ORDER BY time DESC
                        LIMIT ?
                    )
                    """,
                    (uid, uid, MAX_ENTRIES),
                )
            conn.commit()

        result = {
            "id": entry["id"],
            "time": entry["time"],
            "syndrome": entry["syndrome"],
            "diagnosis": entry["diagnosis"],
            "summary": entry["summary"],
            "diagnosis_mode": entry["diagnosis_mode"],
            "has_detail": entry["has_detail"],
        }
        if entry["has_detail"] and isinstance(detail, dict):
            result["detail"] = detail
        return result

    def clear(self, user_id: Optional[str] = None) -> int:
        uid = _user_key(user_id)
        with self._connect() as conn:
            if uid is None:
                cur = conn.execute(
                    "SELECT COUNT(*) AS c FROM diagnosis_history WHERE user_id IS NULL"
                )
                count = int(cur.fetchone()["c"])
                conn.execute("DELETE FROM diagnosis_history WHERE user_id IS NULL")
            else:
                cur = conn.execute(
                    "SELECT COUNT(*) AS c FROM diagnosis_history WHERE user_id = ?",
                    (uid,),
                )
                count = int(cur.fetchone()["c"])
                conn.execute("DELETE FROM diagnosis_history WHERE user_id = ?", (uid,))
            conn.commit()
        return count

    def delete_entry(self, entry_id: str, user_id: Optional[str] = None) -> bool:
        uid = _user_key(user_id)
        with self._connect() as conn:
            if uid is None:
                cur = conn.execute(
                    "DELETE FROM diagnosis_history WHERE id = ? AND user_id IS NULL",
                    (entry_id,),
                )
            else:
                cur = conn.execute(
                    "DELETE FROM diagnosis_history WHERE id = ? AND user_id = ?",
                    (entry_id, uid),
                )
            conn.commit()
            return cur.rowcount > 0
