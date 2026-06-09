# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

#!/usr/bin/env python3
"""检查运行环境与可选自动构建向量索引。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tcm_ai.core.startup import run_startup_checks


def main() -> int:
    report = run_startup_checks(auto_build_index="--no-build" not in sys.argv)
    if report.get("missing_packages"):
        print("缺少依赖:", ", ".join(report["missing_packages"]))
        print("请执行: pip install -r requirements.txt")
        return 1
    if report.get("ollama_warning"):
        print("警告:", report["ollama_warning"])
        print("诊断将自动降级为规则引擎模式。")
    idx = report.get("index")
    if idx == "ready":
        print("向量索引: 已就绪")
    elif idx == "built":
        print(f"向量索引: 已自动构建 ({report.get('chunks')} chunks)")
    elif idx == "missing":
        print("向量索引: 缺失，请运行 python scripts/build_index.py --force")
    else:
        print("向量索引: 跳过（依赖未安装）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
