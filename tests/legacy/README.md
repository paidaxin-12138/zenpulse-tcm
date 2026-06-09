<!-- Copyright (c) 2026 paidaxin-12138 — CC BY-NC 4.0 — see LICENSE -->

# 遗留手动测试脚本

本目录下的脚本为重构前的**手动调试脚本**，需要完整依赖（LangChain、向量模型、OpenCV 等）且会调用真实 LLM。

**请勿在 CI 中运行。** 正式自动化测试见：

- `tests/unit/` — 单元测试
- `tests/integration/` — API 集成测试

## 运行方式（需先安装 requirements.txt）

```bash
python tests/legacy/test_diagnosis.py
python tests/legacy/test_fusion.py
```

## 迁移对照

| 遗留脚本 | 替代测试 |
|---------|---------|
| `test_diagnosis.py` | `tests/integration/test_diagnose_api.py` + `tests/unit/test_rule_engine.py` |
| `test_fusion.py` | `tests/unit/test_fusion_engine.py` |
| `test_pulse_tool.py` | `tests/unit/test_pulse_service.py` |
| `test_vector_db.py` | 管理端「重建索引」+ RAG 问答验证 |
| `test_face_detection.py` | 需 GPU/模型，保留为手动脚本 |
