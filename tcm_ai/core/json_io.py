# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""JSON 文件原子读写与进程间文件锁。"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from contextlib import contextmanager
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_thread_locks: dict[str, threading.Lock] = {}
_thread_locks_guard = threading.Lock()


def _thread_lock_for(path: str) -> threading.Lock:
    abs_path = os.path.abspath(path)
    with _thread_locks_guard:
        lock = _thread_locks.get(abs_path)
        if lock is None:
            lock = threading.Lock()
            _thread_locks[abs_path] = lock
        return lock


@contextmanager
def _file_lock(path: str):
    """同进程 + Unix 进程间 flock，降低 JSON 读-改-写竞态。"""
    abs_path = os.path.abspath(path)
    thread_lock = _thread_lock_for(abs_path)
    thread_lock.acquire()
    lock_path = abs_path + ".lock"
    lock_fd = None
    try:
        os.makedirs(os.path.dirname(lock_path) or ".", exist_ok=True)
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
        if sys.platform != "win32":
            import fcntl

            fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield
    finally:
        if lock_fd is not None:
            if sys.platform != "win32":
                import fcntl

                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
        thread_lock.release()


def _read_unlocked(path: str, default: Any) -> Any:
    if not os.path.isfile(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_unlocked(path: str, data: Any, *, indent: int = 2) -> None:
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def read_json_file(path: str, default: Any) -> Any:
    with _file_lock(path):
        return _read_unlocked(path, default)


def write_json_file(path: str, data: Any, *, indent: int = 2) -> None:
    with _file_lock(path):
        _write_unlocked(path, data, indent=indent)


def update_json_file(
    path: str,
    default: T,
    updater: Callable[[T], T],
    *,
    indent: int = 2,
) -> T:
    """原子读-改-写（同一路径在锁内完成）。"""
    with _file_lock(path):
        current = _read_unlocked(path, default)
        updated = updater(current)
        _write_unlocked(path, updated, indent=indent)
        return updated
