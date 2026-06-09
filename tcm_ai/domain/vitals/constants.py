# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""生理参数 API 与采集约束。"""

# 100 Hz × 150 s；覆盖毕设 ~10s 采集并防止超大 payload DoS
VITALS_MAX_SAMPLES = 15_000
