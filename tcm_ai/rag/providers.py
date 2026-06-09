# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import os
from functools import lru_cache
from typing import Any, Dict, List

import httpx

from tcm_ai.core.url_safety import validate_outbound_base_url

from langchain_community.embeddings import HuggingFaceEmbeddings, OllamaEmbeddings
from langchain_community.llms import Ollama

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError:
    from langchain_community.chat_models import ChatOpenAI
    from langchain_community.embeddings import OpenAIEmbeddings

from tcm_ai.core.paths import DEFAULT_BGE_PATH


def create_embeddings(cfg: Dict[str, Any]):
    provider = cfg.get("provider", "local")
    model = cfg.get("model") or DEFAULT_BGE_PATH
    base_url = (cfg.get("base_url") or "").rstrip("/")
    api_key = cfg.get("api_key") or "not-needed"

    if provider == "ollama":
        return OllamaEmbeddings(model=model, base_url=base_url or "http://127.0.0.1:11434")

    if provider == "openai":
        kwargs = {"model": model, "api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return OpenAIEmbeddings(**kwargs)

    model_path = model if os.path.isabs(model) else DEFAULT_BGE_PATH
    return HuggingFaceEmbeddings(
        model_name=model_path,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def invoke_llm(cfg: Dict[str, Any], prompt: str) -> str:
    provider = cfg.get("provider", "ollama")
    model = cfg.get("model", "deepseek-r1:1.5b")
    base_url = (cfg.get("base_url") or "http://127.0.0.1:11434").rstrip("/")
    api_key = cfg.get("api_key") or "not-needed"
    temperature = float(cfg.get("temperature", 0.3))

    if provider == "openai":
        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url or None,
            temperature=temperature,
        )
        response = llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    llm = Ollama(model=model, base_url=base_url, temperature=temperature, timeout=45)
    response = llm.invoke(prompt)
    return response if isinstance(response, str) else str(response)


def rerank_documents(
    cfg: Dict[str, Any],
    query: str,
    documents: List[Dict[str, Any]],
    top_n: int,
) -> List[Dict[str, Any]]:
    provider = cfg.get("provider", "none")
    if provider == "none" or not documents:
        return documents[:top_n]

    if provider == "local":
        return _rerank_local(cfg.get("model", "BAAI/bge-reranker-base"), query, documents, top_n)

    if provider == "api":
        return _rerank_http(cfg, query, documents, top_n)

    return documents[:top_n]


def _rerank_local(model_name: str, query: str, documents: List[Dict[str, Any]], top_n: int) -> List[Dict[str, Any]]:
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:
        raise RuntimeError("本地 Rerank 需要安装 sentence-transformers") from exc

    pairs = [[query, doc["content"]] for doc in documents]
    model = _get_cross_encoder(model_name)
    scores = model.predict(pairs)
    ranked = []
    for doc, score in zip(documents, scores):
        item = dict(doc)
        item["rerank_score"] = float(score)
        ranked.append(item)
    ranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    return ranked[:top_n]


@lru_cache(maxsize=4)
def _get_cross_encoder(model_name: str):
    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name)


def _rerank_http(
    cfg: Dict[str, Any],
    query: str,
    documents: List[Dict[str, Any]],
    top_n: int,
) -> List[Dict[str, Any]]:
    base_url = validate_outbound_base_url(cfg.get("base_url") or "", field_name="rerank.base_url")
    if not base_url:
        raise RuntimeError("Rerank API 需要配置 base_url")

    api_key = cfg.get("api_key") or ""
    model = cfg.get("model") or ""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "query": query,
        "documents": [doc["content"] for doc in documents],
        "top_n": top_n,
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(base_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    if isinstance(data, dict) and "results" in data:
        ranked_docs: List[Dict[str, Any]] = []
        for item in data["results"]:
            index = item.get("index", 0)
            doc = dict(documents[index])
            doc["rerank_score"] = float(item.get("relevance_score", item.get("score", 0)))
            ranked_docs.append(doc)
        return ranked_docs[:top_n]

    if isinstance(data, list):
        ranked_docs = []
        for item in data[:top_n]:
            index = item.get("index", 0)
            doc = dict(documents[index])
            doc["rerank_score"] = float(item.get("score", 0))
            ranked_docs.append(doc)
        return ranked_docs

    raise RuntimeError("无法解析 Rerank API 响应")
