# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import json

from tcm_ai.knowledge.loader import TCMKnowledgeLoader, TCMAgentKnowledgeManager


def test_load_txt_file_splits_paragraphs(tmp_path):
    sample = tmp_path / "theory.txt"
    sample.write_text("第一段内容。\n\n第二段内容。", encoding="utf-8")

    loader = TCMKnowledgeLoader(str(tmp_path))
    items = loader.load_knowledge_files(recursive=False)

    assert len(items) >= 1
    joined = "\n".join(item["content"] for item in items)
    assert "第一段内容。" in joined
    assert "第二段内容。" in joined
    assert items[0]["type"] == "text"


def test_load_json_file_accepts_knowledge_list(tmp_path):
    sample = tmp_path / "notes.json"
    sample.write_text(
        json.dumps(
            [
                {
                    "title": "补气",
                    "content": "益气健脾",
                    "category": "基础理论",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    loader = TCMKnowledgeLoader(str(tmp_path))
    items = loader.load_knowledge_files(recursive=False)

    assert len(items) == 1
    assert items[0]["title"] == "补气"
    assert items[0]["file_path"].endswith("notes.json")


def test_search_knowledge_ranks_keyword_matches(tmp_path):
    manager = TCMAgentKnowledgeManager(str(tmp_path), index_path=str(tmp_path / "index.json"))
    manager.knowledge_base = [
        {"title": "A", "content": "气血不足常见乏力", "category": "基础理论"},
        {"title": "B", "content": " unrelated text ", "category": "基础理论"},
    ]
    manager.build_index()

    results = manager.search_knowledge("气血", top_k=2)

    assert len(results) == 1
    assert results[0]["title"] == "A"
