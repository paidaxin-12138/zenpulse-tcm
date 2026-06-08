from tcm_ai.core.paths import KNOWLEDGE_DIR, normalize_knowledge_path


def test_normalize_knowledge_path_relative():
    rel = normalize_knowledge_path("herbal_medicine/中药学.txt", KNOWLEDGE_DIR)
    assert rel == "herbal_medicine/中药学.txt"


def test_normalize_knowledge_path_windows_absolute():
    raw = r"C:\Users\lenovo\Desktop\中医\tcm_knowledge\herbal_medicine\中药学.txt"
    rel = normalize_knowledge_path(raw, KNOWLEDGE_DIR)
    assert rel == "herbal_medicine/中药学.txt"
