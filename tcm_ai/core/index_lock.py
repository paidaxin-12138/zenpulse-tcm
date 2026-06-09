# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""向量索引路径的全局互斥锁（线程 + 跨进程文件锁）。"""

from __future__ import annotations

import os
import sys
import threading
from contextlib import contextmanager
from typing import Iterator

from tcm_ai.core.paths import VECTOR_STORE_DIR

_index_lock = threading.RLock()
_file_lock_depth = threading.local()
_lock_fd: int | None = None
_lock_path = os.path.join(VECTOR_STORE_DIR, ".index.lock")


def _acquire_file_lock() -> None:
    global _lock_fd
    depth = getattr(_file_lock_depth, "value", 0)
    if depth == 0 and sys.platform != "win32":
        import fcntl

        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        fd = os.open(_lock_path, os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX)
        _lock_fd = fd
    _file_lock_depth.value = depth + 1


def _release_file_lock() -> None:
    global _lock_fd
    depth = getattr(_file_lock_depth, "value", 0)
    if depth <= 1:
        if _lock_fd is not None and sys.platform != "win32":
            import fcntl

            fcntl.flock(_lock_fd, fcntl.LOCK_UN)
            os.close(_lock_fd)
            _lock_fd = None
        _file_lock_depth.value = 0
    else:
        _file_lock_depth.value = depth - 1


@contextmanager
def index_operation_lock() -> Iterator[None]:
    """在 build / rebuild / invalidate / search 等索引操作期间持有。"""
    with _index_lock:
        _acquire_file_lock()
        try:
            yield
        finally:
            _release_file_lock()


def reset_file_lock_for_tests() -> None:
    """测试用：释放可能遗留的文件锁状态。"""
    global _lock_fd
    if _lock_fd is not None and sys.platform != "win32":
        try:
            import fcntl

            fcntl.flock(_lock_fd, fcntl.LOCK_UN)
            os.close(_lock_fd)
        except OSError:
            pass
    _lock_fd = None
    _file_lock_depth.value = 0
