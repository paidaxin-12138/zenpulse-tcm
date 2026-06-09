from unittest.mock import MagicMock, patch

from tcm_ai.rag import vector_index as vi


def test_knowledge_documents_builds_case_content():
    docs, meta = vi._knowledge_documents(
        [
            {"title": "t1", "content": "正文", "category": "基础理论"},
            {
                "title": "case1",
                "category": "临床案例",
                "age": 45,
                "gender": "女",
                "symptoms": "乏力",
                "diagnosis": "虚劳",
                "syndrome": "气血两虚",
                "treatment": "补气养血",
                "efficacy": "好转",
            },
        ]
    )

    assert len(docs) == 2
    assert docs[0] == "正文"
    assert "气血两虚" in docs[1]
    assert meta[1]["category"] == "临床案例"


def test_index_ready_detects_chroma_sqlite(tmp_path):
    index_dir = tmp_path / "chroma"
    index_dir.mkdir()
    assert vi._index_ready(str(index_dir)) is False

    (index_dir / "chroma.sqlite3").write_text("x", encoding="utf-8")
    assert vi._index_ready(str(index_dir)) is True


def test_vector_index_search_maps_results():
    service = vi.VectorIndexService()
    mock_doc = MagicMock()
    mock_doc.page_content = "内容片段"
    mock_doc.metadata = {
        "title": "标题",
        "source": "theory/a.txt",
        "category": "基础理论",
        "section": "第一章",
        "file_path": "theory/a.txt",
    }
    mock_store = MagicMock()
    mock_store.similarity_search_with_score.return_value = [(mock_doc, 0.12)]

    with patch.object(service, "get_store", return_value=mock_store):
        results = service.search("气血", top_k=1)

    assert len(results) == 1
    assert results[0]["title"] == "标题"
    assert results[0]["content"] == "内容片段"
    assert results[0]["score"] == 0.12
