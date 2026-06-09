# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

#!/usr/bin/env python3
"""检查并引导配置 LLM（Ollama / OpenAI 兼容）。"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tcm_ai.core.llm_setup import get_llm_setup_report, try_pull_ollama_model


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM 连通性检查与模型拉取")
    parser.add_argument("--pull", action="store_true", help="若模型缺失则尝试 ollama pull")
    args = parser.parse_args()

    report = get_llm_setup_report()
    print(f"Provider: {report['provider']}")
    print(f"Model:    {report['model']}")
    print(f"Base URL: {report['base_url']}")
    print()

    if report["provider"] == "ollama":
        print(f"Ollama 已安装: {'是' if report['ollama_installed'] else '否'}")
        if report["ollama_bin"]:
            print(f"路径: {report['ollama_bin']}")
        print(f"服务可达: {'是' if report['ollama_reachable'] else '否'}")
        if report["ollama_error"]:
            print(f"  → {report['ollama_error']}")
        if report["installed_models"]:
            print(f"已安装模型: {', '.join(report['installed_models'])}")
        print()

    if report["ready"]:
        print("✓ LLM 已就绪")
        return 0

    if report["model_error"]:
        print(f"✗ {report['model_error']}")
    print("\n建议步骤:")
    for i, step in enumerate(report["setup_steps"], 1):
        print(f"  {i}. {step}")

    if args.pull and report["provider"] == "ollama" and report["model"]:
        print(f"\n正在拉取 {report['model']} ...")
        result = try_pull_ollama_model(report["model"])
        if result.get("ok"):
            print("✓", result.get("message"))
            return 0
        print("✗", result.get("error"))
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
