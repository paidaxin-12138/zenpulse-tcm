"""JSONL 追加写入与按大小轮转。"""

from __future__ import annotations

import json
import os
import shutil
from typing import Any

from tcm_ai.core.json_io import _file_lock

DEFAULT_JSONL_MAX_BYTES = 10 * 1024 * 1024
DEFAULT_JSONL_MAX_ROTATIONS = 5


def _rotate_jsonl(path: str, max_rotations: int) -> None:
    if max_rotations <= 0:
        os.remove(path)
        return
    oldest = f"{path}.{max_rotations}"
    if os.path.exists(oldest):
        os.remove(oldest)
    for index in range(max_rotations - 1, 0, -1):
        src = f"{path}.{index}"
        dst = f"{path}.{index + 1}"
        if os.path.exists(src):
            shutil.move(src, dst)
    shutil.move(path, f"{path}.1")


def append_jsonl_record(
    path: str,
    record: dict[str, Any],
    *,
    max_bytes: int = DEFAULT_JSONL_MAX_BYTES,
    max_rotations: int = DEFAULT_JSONL_MAX_ROTATIONS,
) -> None:
    """追加一行 JSON；超过 max_bytes 时轮转历史文件。"""
    line = json.dumps(record, ensure_ascii=False) + "\n"
    encoded = line.encode("utf-8")
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    with _file_lock(path):
        current_size = os.path.getsize(path) if os.path.isfile(path) else 0
        if current_size > 0 and current_size + len(encoded) > max_bytes:
            _rotate_jsonl(path, max_rotations)
        with open(path, "ab") as handle:
            handle.write(encoded)
