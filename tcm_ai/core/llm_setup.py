"""LLM（Ollama / OpenAI 兼容）连通性与模型检查。"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from tcm_ai.core.config_store import load_config


def _llm_cfg() -> Dict[str, Any]:
    return load_config().get("llm") or {}


def check_ollama_reachable(base_url: Optional[str] = None) -> Optional[str]:
    cfg = _llm_cfg()
    if cfg.get("provider") != "ollama":
        return None
    base = (base_url or cfg.get("base_url") or "http://127.0.0.1:11434").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=5) as resp:
            if resp.status != 200:
                return f"Ollama 响应异常: HTTP {resp.status}"
    except Exception as exc:
        return f"Ollama 不可用 ({base}): {exc}"
    return None


def list_ollama_models(base_url: Optional[str] = None) -> List[str]:
    cfg = _llm_cfg()
    base = (base_url or cfg.get("base_url") or "http://127.0.0.1:11434").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return []
    names: List[str] = []
    for item in payload.get("models") or []:
        name = item.get("name") or item.get("model")
        if name:
            names.append(str(name))
    return names


def check_llm_model_ready() -> Optional[str]:
    cfg = _llm_cfg()
    provider = cfg.get("provider", "ollama")
    model = (cfg.get("model") or "").strip()
    if provider == "openai":
        if not (cfg.get("api_key") or "").strip():
            return "LLM provider=openai 但未配置 api_key"
        return None
    if provider != "ollama":
        return None
    err = check_ollama_reachable()
    if err:
        return err
    if not model:
        return "未配置 llm.model"
    models = list_ollama_models()
    if not models:
        return f"Ollama 无已安装模型，请执行: ollama pull {model}"
    if model in models:
        return None
    base_name = model.split(":")[0]
    if any(m == model or m.startswith(base_name + ":") for m in models):
        return None
    return f"模型 {model} 未安装。已安装: {', '.join(models[:5])}。请执行: ollama pull {model}"


def get_llm_setup_report() -> Dict[str, Any]:
    cfg = _llm_cfg()
    provider = cfg.get("provider", "ollama")
    model = cfg.get("model", "")
    base_url = (cfg.get("base_url") or "http://127.0.0.1:11434").rstrip("/")
    ollama_bin = shutil.which("ollama")
    reachable_err = check_ollama_reachable() if provider == "ollama" else None
    models = list_ollama_models() if provider == "ollama" and not reachable_err else []
    model_err = check_llm_model_ready()
    return {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "ollama_installed": bool(ollama_bin),
        "ollama_bin": ollama_bin or "",
        "ollama_reachable": reachable_err is None if provider == "ollama" else None,
        "ollama_error": reachable_err,
        "installed_models": models,
        "model_ready": model_err is None,
        "model_error": model_err,
        "ready": model_err is None,
        "setup_steps": build_setup_steps(provider, ollama_bin, reachable_err, model, models),
    }


def build_setup_steps(
    provider: str,
    ollama_bin: Optional[str],
    reachable_err: Optional[str],
    model: str,
    installed_models: List[str],
) -> List[str]:
    steps: List[str] = []
    if provider == "openai":
        steps.append("在管理端 LLM 配置中填写 OpenAI 兼容 base_url、model、api_key")
        steps.append("点击「测试 LLM」验证连通性")
        return steps
    if not ollama_bin:
        steps.append("安装 Ollama: brew install ollama  或访问 https://ollama.com/download")
        steps.append("启动服务: ollama serve  （macOS 安装后通常自动启动）")
    elif reachable_err:
        steps.append("启动 Ollama: ollama serve")
        steps.append(f"确认 {load_config().get('llm', {}).get('base_url', 'http://127.0.0.1:11434')} 可访问")
    if model and model not in installed_models and not any(
        m.startswith(model.split(":")[0] + ":") for m in installed_models
    ):
        steps.append(f"拉取模型: ollama pull {model}")
    if not steps:
        steps.append("LLM 已就绪，可发起诊断或管理端 RAG 测试")
    return steps


def try_pull_ollama_model(model: str) -> Dict[str, Any]:
    if not shutil.which("ollama"):
        return {"ok": False, "error": "未找到 ollama 命令，请先安装 Ollama"}
    if not model:
        return {"ok": False, "error": "未指定模型名"}
    try:
        proc = subprocess.run(
            ["ollama", "pull", model],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if proc.returncode != 0:
            return {"ok": False, "error": (proc.stderr or proc.stdout or "pull 失败").strip()}
        return {"ok": True, "message": f"已拉取模型 {model}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "拉取超时（>10 分钟）"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
