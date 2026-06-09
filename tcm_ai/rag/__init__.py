# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

__all__ = ["RAGPipeline"]


def __getattr__(name: str):
    if name == "RAGPipeline":
        from tcm_ai.rag.pipeline import RAGPipeline

        return RAGPipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
