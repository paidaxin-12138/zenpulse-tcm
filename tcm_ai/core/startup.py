"""启动时环境自检与可选索引构建。"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from tcm_ai.core.config_store import load_config
from tcm_ai.core.paths import VECTOR_INDEX_PATH


def check_python_packages() -> List[str]:
    missing: List[str] = []
    for pkg, pip_name in (
        ("langchain_community", "langchain-community"),
        ("langchain_text_splitters", "langchain-text-splitters"),
        ("chromadb", "chromadb"),
        ("sentence_transformers", "sentence-transformers"),
    ):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pip_name)
    return missing


def index_ready() -> bool:
    if not os.path.isdir(VECTOR_INDEX_PATH):
        return False
    return any(
        name.endswith(".sqlite3") or name == "chroma.sqlite3"
        for name in os.listdir(VECTOR_INDEX_PATH)
    )


def check_ollama() -> Optional[str]:
    from tcm_ai.core.llm_setup import check_llm_model_ready

    config = load_config()
    llm = config.get("llm", {})
    if llm.get("provider") != "ollama":
        return None
    return check_llm_model_ready()


def ensure_index(auto_build: bool = True) -> Dict[str, Any]:
    if index_ready():
        return {"index": "ready", "path": VECTOR_INDEX_PATH}
    if not auto_build:
        return {"index": "missing", "path": VECTOR_INDEX_PATH}
    config = load_config()
    if not config.get("rag", {}).get("rebuild_on_missing_index", True):
        return {"index": "missing", "auto_build": False}
    missing = check_python_packages()
    if missing:
        return {"index": "missing", "auto_build": False, "missing_packages": missing}
    from tcm_ai.rag.pipeline import RAGPipeline

    result = RAGPipeline().rebuild_index(force=False)
    return {"index": "built", "chunks": result.get("chunks"), "path": VECTOR_INDEX_PATH}


def run_startup_checks(auto_build_index: bool = True) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "missing_packages": check_python_packages(),
        "ollama_warning": check_ollama(),
    }
    if not report["missing_packages"]:
        report.update(ensure_index(auto_build=auto_build_index))
    else:
        report["index"] = "skipped_missing_deps"
    return report
