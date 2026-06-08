from tcm_ai.core.llm_setup import build_setup_steps, check_ollama_reachable


def test_build_setup_steps_when_ollama_missing():
    steps = build_setup_steps("ollama", None, "unreachable", "deepseek-r1:1.5b", [])
    assert any("安装 Ollama" in s for s in steps)
    assert any("ollama pull" in s for s in steps)


def test_check_ollama_unreachable():
    err = check_ollama_reachable("http://127.0.0.1:59999")
    assert err is not None
