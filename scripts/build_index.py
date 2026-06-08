#!/usr/bin/env python3
"""离线构建向量索引。"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tcm_ai.rag.pipeline import RAGPipeline


def main():
    parser = argparse.ArgumentParser(description="构建中医知识库向量索引")
    parser.add_argument("--force", action="store_true", help="强制删除并重建索引")
    args = parser.parse_args()

    pipeline = RAGPipeline()
    result = pipeline.rebuild_index(force=args.force)
    print(f"索引构建完成: {result['chunks']} 个分块 -> {result['index_path']}")


if __name__ == "__main__":
    main()
