"""生理参数 API 与采集约束。"""

# 100 Hz × 150 s；覆盖毕设 ~10s 采集并防止超大 payload DoS
VITALS_MAX_SAMPLES = 15_000
