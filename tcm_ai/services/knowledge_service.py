# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from tcm_ai.core.paths import KNOWLEDGE_DIR
from tcm_ai.knowledge.loader import TCMAgentKnowledgeManager


class KnowledgeService:
    """知识库文件与索引管理。"""

    ALLOWED_EXTENSIONS = {".txt", ".json", ".md"}

    def __init__(self, knowledge_dir: str = KNOWLEDGE_DIR) -> None:
        self.knowledge_dir = knowledge_dir
        self._manager: Optional[TCMAgentKnowledgeManager] = None

    @property
    def manager(self) -> TCMAgentKnowledgeManager:
        if self._manager is None:
            self._manager = TCMAgentKnowledgeManager(self.knowledge_dir)
        return self._manager

    def _resolve_safe_path(self, relative_path: str) -> Path:
        rel = relative_path.replace("\\", "/").lstrip("/")
        target = (Path(self.knowledge_dir) / rel).resolve()
        root = Path(self.knowledge_dir).resolve()
        if not str(target).startswith(str(root)):
            raise ValueError("非法路径")
        return target

    def list_files(self) -> List[Dict[str, Any]]:
        files: List[Dict[str, Any]] = []
        for root, _, names in os.walk(self.knowledge_dir):
            for name in names:
                if name.startswith("."):
                    continue
                path = os.path.join(root, name)
                rel = os.path.relpath(path, self.knowledge_dir)
                files.append(
                    {
                        "path": rel.replace("\\", "/"),
                        "category": rel.split(os.sep)[0] if os.sep in rel else "root",
                        "size_bytes": os.path.getsize(path),
                        "extension": os.path.splitext(name)[1].lower(),
                    }
                )
        files.sort(key=lambda item: item["path"])
        return files

    def stats(self) -> Dict[str, Any]:
        files = self.list_files()
        by_category: Dict[str, int] = {}
        for item in files:
            by_category[item["category"]] = by_category.get(item["category"], 0) + 1
        return {
            "knowledge_dir": self.knowledge_dir,
            "total_files": len(files),
            "by_category": by_category,
        }

    def search_keywords(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        self.manager.load_all_knowledge()
        return self.manager.search_knowledge(query, top_k)

    def upload_text(
        self,
        relative_path: str,
        content: str,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        ext = Path(relative_path).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"不支持的文件类型: {ext}")

        target = self._resolve_safe_path(relative_path)
        if target.exists() and not overwrite:
            raise FileExistsError(f"文件已存在: {relative_path}")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self._manager = None
        return {"path": relative_path.replace("\\", "/"), "size_bytes": target.stat().st_size}

    def upload_file(
        self,
        filename: str,
        content: bytes,
        subdir: str = "imports",
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        safe_name = Path(filename).name
        if not safe_name or safe_name.startswith("."):
            raise ValueError("无效文件名")
        ext = Path(safe_name).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"不支持的文件类型: {ext}")

        sub = subdir.replace("\\", "/").strip("/")
        relative_path = f"{sub}/{safe_name}" if sub else safe_name
        target = self._resolve_safe_path(relative_path)
        if target.exists() and not overwrite:
            raise FileExistsError(f"文件已存在: {relative_path}")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        self._manager = None
        return {
            "path": relative_path,
            "size_bytes": target.stat().st_size,
            "filename": safe_name,
        }

    def delete_file(self, relative_path: str) -> Dict[str, str]:
        target = self._resolve_safe_path(relative_path)
        if not target.is_file():
            raise FileNotFoundError(relative_path)
        target.unlink()
        self._manager = None
        return {"deleted": relative_path.replace("\\", "/")}

    @staticmethod
    def _case_summary(case: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        case_id = case.get("case_id") or case.get("patient_id") or case.get("id", "")
        return {
            "case_id": case_id,
            "patient_id": case.get("patient_id") or case.get("id", ""),
            "source_file": source_file,
            "age": case.get("age"),
            "gender": case.get("gender"),
            "syndrome": case.get("syndrome", ""),
            "diagnosis": case.get("diagnosis", ""),
            "symptoms": case.get("symptoms", ""),
            "treatment": case.get("treatment", ""),
            "efficacy": case.get("efficacy", ""),
            "date": case.get("date", ""),
            "doctor": case.get("doctor", ""),
            "hospital": case.get("hospital", ""),
            "source": case.get("source", ""),
        }

    @staticmethod
    def _extract_cases_from_json(data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if isinstance(data, dict):
            nested = data.get("cases")
            if isinstance(nested, list):
                return [row for row in nested if isinstance(row, dict)]
            return [data]
        return []

    def _iter_all_cases(self):
        cases_dir = Path(self.knowledge_dir) / "cases"
        if not cases_dir.is_dir():
            return
        for file_path in sorted(cases_dir.glob("*.json")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for case in self._extract_cases_from_json(data):
                    row = dict(case)
                    row["_source_file"] = file_path.name
                    yield row
            except (json.JSONDecodeError, OSError):
                continue

    _CASE_SEARCH_FIELDS = (
        "case_id",
        "patient_id",
        "symptoms",
        "diagnosis",
        "syndrome",
        "gender",
        "doctor",
        "hospital",
    )

    @staticmethod
    def _case_haystack(case: Dict[str, Any]) -> str:
        return " ".join(str(case.get(k, "")) for k in KnowledgeService._CASE_SEARCH_FIELDS).lower()

    def _count_all_cases(self) -> int:
        return sum(1 for _ in self._iter_all_cases())

    @staticmethod
    def _case_search_needles(q: str) -> List[str]:
        q = q.strip().lower()
        if not q:
            return []
        needles = {q}
        # 常见同义检索
        if "头疼" in q:
            needles.add(q.replace("头疼", "头痛"))
        if "头痛" in q:
            needles.add(q.replace("头痛", "头疼"))
        return list(needles)

    def list_case_library(
        self, limit: int = 50, offset: int = 0, q: str = ""
    ) -> Dict[str, Any]:
        needles = self._case_search_needles(q) if q else None
        page: List[Dict[str, Any]] = []
        total = 0
        for case in self._iter_all_cases():
            if needles and not any(needle in self._case_haystack(case) for needle in needles):
                continue
            if total >= offset and len(page) < limit:
                page.append(self._case_summary(case, case["_source_file"]))
            total += 1
        return {"total": total, "offset": offset, "limit": limit, "cases": page}

    def case_library_stats(self) -> Dict[str, Any]:
        cases_dir = Path(self.knowledge_dir) / "cases"
        files = self.list_files()
        case_files = [f for f in files if f["path"].startswith("cases/")]
        total_cases = self._count_all_cases()
        return {
            "cases_dir": str(cases_dir),
            "file_count": len(case_files),
            "case_count": total_cases,
            "files": case_files,
        }

    def get_case_library_entry(self, case_id: str) -> Dict[str, Any]:
        for case in self._iter_all_cases():
            cid = case.get("case_id") or case.get("patient_id") or case.get("id")
            if cid == case_id:
                return self._case_summary(case, case["_source_file"])
        raise KeyError(case_id)
