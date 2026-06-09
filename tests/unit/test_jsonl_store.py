import json

from tcm_ai.core.jsonl_store import append_jsonl_record


def test_append_jsonl_record_writes_line(tmp_path):
    path = tmp_path / "sessions.jsonl"
    append_jsonl_record(str(path), {"session_id": "s1", "ok": True})

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["session_id"] == "s1"


def test_append_jsonl_rotates_when_exceeding_max_bytes(tmp_path):
    path = tmp_path / "sessions.jsonl"
    path.write_text('{"old": true}\n', encoding="utf-8")

    append_jsonl_record(
        str(path),
        {"session_id": "new"},
        max_bytes=20,
        max_rotations=2,
    )

    assert path.read_text(encoding="utf-8").strip().endswith('"new"}')
    rotated = tmp_path / "sessions.jsonl.1"
    assert rotated.is_file()
    assert '"old": true' in rotated.read_text(encoding="utf-8")
