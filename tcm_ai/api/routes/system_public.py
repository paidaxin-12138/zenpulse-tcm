"""公开系统状态（供 C 端展示依赖与健康信息）。"""

import os
import socket

from fastapi import APIRouter, HTTPException

from tcm_ai.core.branding import load_branding
from tcm_ai.core.llm_setup import get_llm_setup_report
from tcm_ai.core.runtime import is_production
from tcm_ai.core.startup import check_ollama, check_python_packages, index_ready

router = APIRouter(tags=["系统"])


def _guess_lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


@router.get("/api/public/branding")
def public_branding():
    """Web / 管理端 / 小程序共用的品牌与跨端链接。"""
    return load_branding()


@router.get("/api/system/status")
def public_system_status():
    missing = check_python_packages()
    ollama_msg = check_ollama()
    llm_report = get_llm_setup_report()
    idx = index_ready()
    return {
        "rag_deps_ok": len(missing) == 0,
        "missing_packages": missing,
        "index_ready": idx,
        "ollama_ok": ollama_msg is None,
        "ollama_message": ollama_msg,
        "llm_ready": llm_report.get("ready", False),
        "llm_mode_hint": "llm" if ollama_msg is None else "rule_fallback",
    }


@router.get("/api/public/dev-hints")
def public_dev_hints():
    """小程序真机联调：返回建议的后端局域网地址（仅开发环境）。"""
    if is_production():
        raise HTTPException(status_code=404, detail="Not Found")
    port = int(os.environ.get("TCM_PORT", "8000"))
    lan_ip = _guess_lan_ip()
    return {
        "port": port,
        "lan_ip": lan_ip,
        "suggested_api_base": f"http://{lan_ip}:{port}/api",
        "suggested_web_url": f"http://{lan_ip}:{port}/",
        "llm": get_llm_setup_report(),
        "checklist": [
            "手机与电脑连接同一 Wi-Fi",
            f"小程序设置页填入: http://{lan_ip}:{port}/api",
            "微信开发者工具 → 详情 → 本地设置 → 不校验合法域名",
            "若仍失败，检查 macOS 防火墙是否放行 8000 端口",
        ],
    }
