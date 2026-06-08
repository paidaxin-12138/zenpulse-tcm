#!/usr/bin/env python3
"""将 JSON 诊断历史迁移到 SQLite（TCM_HISTORY_BACKEND=sql 时使用）。"""

from __future__ import annotations

import argparse
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tcm_ai.core.paths import DATA_DIR  # noqa: E402
from tcm_ai.repositories.diagnosis_history import (  # noqa: E402
    HISTORY_PATH,
    HISTORY_USER_DIR,
    JsonDiagnosisHistoryRepository,
    MAX_ENTRIES,
)
from tcm_ai.repositories.sql_diagnosis_history import SqlDiagnosisHistoryRepository  # noqa: E402


def _user_ids_from_dir(user_dir: str) -> list[str | None]:
    users: list[str | None] = [None]
    if not os.path.isdir(user_dir):
        return users
    for path in glob.glob(os.path.join(user_dir, "*.json")):
        name = os.path.basename(path)
        if name.endswith(".json"):
            users.append(name[: -len(".json")])
    return users


def migrate(
    *,
    database_url: str = "",
    dry_run: bool = False,
) -> int:
    json_repo = JsonDiagnosisHistoryRepository()
    sql_repo = SqlDiagnosisHistoryRepository(database_url=database_url)
    migrated = 0
    skipped = 0

    for user_id in _user_ids_from_dir(HISTORY_USER_DIR):
        summaries = json_repo.list_entries(limit=MAX_ENTRIES, user_id=user_id)
        for summary in reversed(summaries):
            entry_id = summary.get("id", "")
            if not entry_id:
                continue
            if sql_repo.get_entry(entry_id, user_id=user_id):
                skipped += 1
                continue
            full = json_repo.get_entry(entry_id, user_id=user_id)
            if not full:
                skipped += 1
                continue
            payload = {
                "id": full["id"],
                "time": full.get("time", ""),
                "syndrome": full.get("syndrome", ""),
                "diagnosis": full.get("diagnosis", ""),
                "summary": full.get("summary", ""),
                "diagnosis_mode": full.get("diagnosis_mode", ""),
            }
            if full.get("detail"):
                payload["detail"] = full["detail"]
            if dry_run:
                print(f"would migrate user={user_id!r} id={entry_id}")
            else:
                sql_repo.add_entry(payload, user_id=user_id)
            migrated += 1

    print(
        f"JSON root: {HISTORY_PATH}\n"
        f"SQL target: {sql_repo.db_path}\n"
        f"migrated={migrated} skipped={skipped} dry_run={dry_run}"
    )
    return migrated


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate diagnosis history JSON → SQLite")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("TCM_HISTORY_DATABASE_URL", ""),
        help=f"sqlite URL (default: {DATA_DIR}/diagnosis_history.sqlite3)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    migrate(database_url=args.database_url, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
