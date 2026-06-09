# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import multiprocessing
import os
import sys

import pytest

from tcm_ai.core.index_lock import index_operation_lock, reset_file_lock_for_tests


def test_index_lock_reentrant_in_same_thread():
    reset_file_lock_for_tests()
    with index_operation_lock():
        with index_operation_lock():
            pass


def _hold_lock(lock_dir: str, ready, release):
    import tcm_ai.core.index_lock as mod

    mod._lock_path = os.path.join(lock_dir, ".index.lock")
    mod.reset_file_lock_for_tests()
    with mod.index_operation_lock():
        ready.set()
        release.wait(timeout=5)


@pytest.mark.skipif(sys.platform == "win32", reason="fcntl 文件锁仅 Unix")
def test_index_lock_blocks_second_process(tmp_path):
    reset_file_lock_for_tests()
    lock_dir = str(tmp_path)
    import tcm_ai.core.index_lock as mod

    mod._lock_path = os.path.join(lock_dir, ".index.lock")

    ready = multiprocessing.Event()
    release = multiprocessing.Event()
    proc = multiprocessing.Process(
        target=_hold_lock,
        args=(lock_dir, ready, release),
    )
    proc.start()
    assert ready.wait(timeout=5)

    import fcntl

    fd = os.open(mod._lock_path, os.O_CREAT | os.O_RDWR)
    try:
        with pytest.raises(BlockingIOError):
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        os.close(fd)

    release.set()
    proc.join(timeout=5)
    assert proc.exitcode == 0
