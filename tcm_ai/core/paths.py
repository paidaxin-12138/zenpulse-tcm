# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import os

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
KNOWLEDGE_DIR = os.path.join(PROJECT_ROOT, "tcm_knowledge")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
VECTOR_STORE_DIR = os.path.join(PROJECT_ROOT, "vector_store")
ADMIN_CONFIG_PATH = os.path.join(DATA_DIR, "admin_config.json")
PATIENTS_PATH = os.path.join(DATA_DIR, "patients.json")
VISITS_DIR = os.path.join(DATA_DIR, "visits")
DEFAULT_BGE_PATH = os.path.join(MODELS_DIR, "bge-small-zh-v1.5")
VECTOR_INDEX_PATH = os.path.join(VECTOR_STORE_DIR, "tcm_knowledge_index")


def normalize_knowledge_path(file_path: str, knowledge_dir: str = KNOWLEDGE_DIR) -> str:
    """将知识文件路径规范为相对 tcm_knowledge/ 的路径。"""
    if not file_path:
        return ""
    normalized = str(file_path).replace("\\", "/")
    root = os.path.normpath(knowledge_dir).replace("\\", "/")
    abs_path = os.path.normpath(file_path).replace("\\", "/")
    if abs_path.startswith(root):
        return abs_path[len(root) :].lstrip("/")
    marker = "tcm_knowledge/"
    idx = normalized.find(marker)
    if idx >= 0:
        return normalized[idx + len(marker) :]
    return normalized.lstrip("/")
