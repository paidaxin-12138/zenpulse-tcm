"""向量索引路径的全局互斥锁（重建与检索互斥）。"""

from __future__ import annotations

import threading

_index_lock = threading.RLock()


def index_operation_lock():
    """在 build / rebuild / invalidate / search 等索引操作期间持有。"""
    return _index_lock
