import os

import pytest

from tcm_ai.repositories.diagnosis_history import MAX_ENTRIES
from tcm_ai.repositories.sql_diagnosis_history import SqlDiagnosisHistoryRepository


@pytest.fixture
def sql_repo(tmp_path, monkeypatch):
    db = tmp_path / "history.sqlite3"
    monkeypatch.setenv("TCM_HISTORY_DATABASE_URL", f"sqlite:///{db}")
    return SqlDiagnosisHistoryRepository(database_url=f"sqlite:///{db}")


def test_sql_history_crud(sql_repo):
    created = sql_repo.add_entry(
        {
            "syndrome": "气虚",
            "summary": "测试",
            "detail": {"analysis": "深度分析", "suggestions": ["早睡"]},
        },
        user_id="user-a",
    )
    assert created["has_detail"] is True
    assert created["detail"]["analysis"] == "深度分析"

    listed = sql_repo.list_entries(limit=10, user_id="user-a")
    assert len(listed) == 1
    assert listed[0]["has_detail"] is True
    assert "detail" not in listed[0]

    fetched = sql_repo.get_entry(created["id"], user_id="user-a")
    assert fetched["detail"]["suggestions"] == ["早睡"]

    assert sql_repo.delete_entry(created["id"], user_id="user-a") is True
    assert sql_repo.get_entry(created["id"], user_id="user-a") is None


def test_sql_history_user_isolation(sql_repo):
    a = sql_repo.add_entry({"syndrome": "A"}, user_id="u1")
    b = sql_repo.add_entry({"syndrome": "B"}, user_id="u2")
    assert len(sql_repo.list_entries(user_id="u1")) == 1
    assert sql_repo.get_entry(b["id"], user_id="u1") is None
    assert sql_repo.get_entry(a["id"], user_id="u2") is None


def test_sql_history_trim(sql_repo):
    for i in range(MAX_ENTRIES + 5):
        sql_repo.add_entry({"syndrome": f"s{i}"}, user_id="trim-user")
    assert len(sql_repo.list_entries(limit=MAX_ENTRIES + 10, user_id="trim-user")) == MAX_ENTRIES


def test_sql_history_clear_and_preserve_id(sql_repo):
    entry_id = "fixed-entry-id-001"
    created = sql_repo.add_entry({"id": entry_id, "syndrome": "保留 ID"}, user_id=None)
    assert created["id"] == entry_id
    assert len(sql_repo.list_entries(user_id=None)) == 1

    count = sql_repo.clear(user_id=None)
    assert count == 1
    assert sql_repo.list_entries(user_id=None) == []


def test_get_repository_sql_backend(tmp_path, monkeypatch):
    db = tmp_path / "via-factory.sqlite3"
    monkeypatch.setenv("TCM_HISTORY_BACKEND", "sql")
    monkeypatch.setenv("TCM_HISTORY_DATABASE_URL", f"sqlite:///{db}")

    from tcm_ai.repositories.diagnosis_history import get_diagnosis_history_repository

    repo = get_diagnosis_history_repository()
    entry = repo.add_entry({"syndrome": "工厂"}, user_id="x")
    assert entry["syndrome"] == "工厂"
    assert os.path.isfile(db)
