# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import os
import shutil
from typing import Any, Callable, Dict, List, Optional, Tuple

from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from tcm_ai.knowledge.loader import TCMAgentKnowledgeManager
from tcm_ai.core.config_store import load_config
from tcm_ai.core.index_lock import index_operation_lock
from tcm_ai.core.paths import KNOWLEDGE_DIR, VECTOR_INDEX_PATH, VECTOR_STORE_DIR, normalize_knowledge_path

ProgressCallback = Callable[[Dict[str, Any]], None]
EMBED_BATCH_SIZE = 32


def _knowledge_documents(knowledge_items: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
    documents: List[str] = []
    metadata: List[Dict[str, Any]] = []

    for item in knowledge_items:
        if "content" in item:
            content = item["content"]
        elif item.get("category") == "临床案例":
            content = (
                f"患者信息：{item.get('age', '')}岁 {item.get('gender', '')}\n"
                f"症状：{item.get('symptoms', '')}\n"
                f"诊断：{item.get('diagnosis', '')}\n"
                f"证型：{item.get('syndrome', '')}\n"
                f"治疗：{item.get('treatment', '')}\n"
                f"疗效：{item.get('efficacy', '')}"
            )
        else:
            continue

        documents.append(content)
        metadata.append(
            {
                "title": item.get("title", "未知标题"),
                "source": item.get("source", "未知来源"),
                "type": item.get("type", "text"),
                "category": item.get("category", "其他"),
                "section": item.get("section", ""),
                "file_path": item.get("file_path", ""),
            }
        )
    return documents, metadata


def _index_ready(index_path: str) -> bool:
    if not os.path.isdir(index_path):
        return False
    return any(name.endswith(".sqlite3") or name == "chroma.sqlite3" for name in os.listdir(index_path))


class VectorIndexService:
    def __init__(self) -> None:
        self._vector_store: Optional[Chroma] = None
        self._embeddings = None
        self._index_path = VECTOR_INDEX_PATH

    def _get_embeddings(self):
        if self._embeddings is None:
            from tcm_ai.rag.providers import create_embeddings

            config = load_config()
            self._embeddings = create_embeddings(config["embedding"])
        return self._embeddings

    def _emit(
        self,
        callback: Optional[ProgressCallback],
        phase: str,
        progress: int,
        message: str,
        **extra: Any,
    ) -> None:
        if callback:
            callback(
                {
                    "phase": phase,
                    "progress": max(0, min(100, progress)),
                    "message": message,
                    **extra,
                }
            )

    def build_index(
        self,
        force: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
        batch_size: int = EMBED_BATCH_SIZE,
    ) -> Dict[str, Any]:
        with index_operation_lock():
            return self._build_index_locked(force, progress_callback, batch_size)

    def _build_index_locked(
        self,
        force: bool,
        progress_callback: Optional[ProgressCallback],
        batch_size: int,
    ) -> Dict[str, Any]:
        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        self._emit(progress_callback, "preparing", 2, "准备索引目录…")

        if force and os.path.exists(self._index_path):
            shutil.rmtree(self._index_path)
            self._emit(progress_callback, "preparing", 5, "已清除旧索引")

        self._emit(progress_callback, "loading", 8, "加载知识库…")
        knowledge_manager = TCMAgentKnowledgeManager(KNOWLEDGE_DIR)
        knowledge_items = knowledge_manager.load_all_knowledge()
        raw_docs, raw_meta = _knowledge_documents(knowledge_items)
        if not raw_docs:
            raise RuntimeError("知识库为空，无法构建向量索引")

        self._emit(
            progress_callback,
            "loading",
            15,
            f"已加载 {len(knowledge_items)} 条知识条目",
            documents=len(raw_docs),
        )

        self._emit(progress_callback, "splitting", 18, "文本分块中…")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["。", "！", "？", "；", "\n", "\n\n"],
        )
        documents = splitter.create_documents(raw_docs, metadatas=raw_meta)
        self._emit(
            progress_callback,
            "splitting",
            25,
            f"分块完成，共 {len(documents)} 个片段",
            chunks=len(documents),
        )

        embeddings = self._get_embeddings()
        self._emit(progress_callback, "embedding", 28, "初始化向量库…")
        vector_store = Chroma(
            persist_directory=self._index_path,
            embedding_function=embeddings,
        )

        total_batches = max(1, (len(documents) + batch_size - 1) // batch_size)
        for batch_index, start in enumerate(range(0, len(documents), batch_size), start=1):
            batch = documents[start : start + batch_size]
            vector_store.add_documents(batch)
            progress = 28 + int(67 * batch_index / total_batches)
            self._emit(
                progress_callback,
                "embedding",
                progress,
                f"向量化批次 {batch_index}/{total_batches}",
                current_batch=batch_index,
                total_batches=total_batches,
            )

        self._vector_store = vector_store
        self._emit(
            progress_callback,
            "finalizing",
            98,
            "写入索引文件…",
        )
        self._emit(
            progress_callback,
            "completed",
            100,
            f"索引构建完成，共 {len(documents)} 个分块",
            chunks=len(documents),
        )
        return {"chunks": len(documents), "index_path": self._index_path}

    def get_store(self) -> Chroma:
        with index_operation_lock():
            config = load_config()
            embeddings = self._get_embeddings()

            if self._vector_store is not None:
                return self._vector_store

            if not _index_ready(self._index_path):
                if config["rag"].get("rebuild_on_missing_index", True):
                    self._build_index_locked(force=False, progress_callback=None, batch_size=EMBED_BATCH_SIZE)
                else:
                    raise RuntimeError("向量索引不存在，请先在管理端重建索引")

            self._vector_store = Chroma(
                persist_directory=self._index_path,
                embedding_function=embeddings,
            )
            return self._vector_store

    def invalidate(self) -> None:
        with index_operation_lock():
            self._vector_store = None
            self._embeddings = None

    def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        with index_operation_lock():
            store = self.get_store()
            results = store.similarity_search_with_score(query, k=top_k)
            items: List[Dict[str, Any]] = []
            for doc, score in results:
                file_path = normalize_knowledge_path(
                    doc.metadata.get("file_path", ""), KNOWLEDGE_DIR
                )
                source = normalize_knowledge_path(
                    doc.metadata.get("source", ""), KNOWLEDGE_DIR
                ) or file_path
                items.append(
                    {
                        "title": doc.metadata.get("title", ""),
                        "content": doc.page_content,
                        "source": source,
                        "category": doc.metadata.get("category", ""),
                        "section": doc.metadata.get("section", ""),
                        "file_path": file_path,
                        "score": float(score),
                    }
                )
            return items
