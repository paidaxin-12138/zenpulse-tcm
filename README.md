<!-- Copyright (c) 2026 paidaxin-12138 — CC BY-NC 4.0 — see LICENSE -->

# 中医 AI 诊断系统

## 项目结构

```
中医/
├── admin/                  # 管理端 UI
├── frontend/               # C 端 Web
├── wechat-miniprogram/     # 微信小程序
├── deploy/                 # systemd unit
├── docs/DEPLOYMENT.md      # 生产部署（Docker / systemd）
├── data/                   # 运行时配置（admin_config.json）
├── scripts/                # 运维脚本
│   ├── build_index.py
│   ├── check_env.py        # 环境自检
│   ├── setup_llm.py        # LLM 连通性检查
│   └── setup_ollama.sh     # 安装 Ollama + 拉模型
├── tests/
│   ├── unit/
│   ├── integration/
│   └── legacy/             # 旧手动脚本（pytest 自动 skip）
├── tcm_knowledge/          # 知识库数据
├── vector_store/           # 向量索引
├── tcm_ai/                 # 后端核心
├── Dockerfile
├── docker-compose.yml
├── web_server.py           # 启动入口
└── requirements.txt
```

## 快速启动

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/check_env.py          # 检查依赖与索引（可选 --no-build）
python3 scripts/setup_llm.py         # 检查 LLM / Ollama 连通性
bash scripts/setup_ollama.sh         # 安装 Ollama 并拉取模型（macOS/Linux）
cp data/admin_config.example.json data/admin_config.json   # 首次（或自动生成）
python web_server.py                 # http://localhost:8000
```

启动时会自动：检查 RAG 依赖、检测 Ollama、在索引缺失时尝试构建向量库。

环境变量：`TCM_HOST`（默认 `0.0.0.0`）、`TCM_PORT`（默认 `8000`）、`TCM_ENV`（`development` / `production`，**Docker/systemd 默认 production**；本地开发请 `export TCM_ENV=development`）。

**重要：** 修改 `tcm_ai/` 或 API 路由后，需**重启** `python web_server.py` 才能生效（默认无热重载）。

## 生产部署

详见 **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**：

```bash
docker compose up -d --build
docker compose exec tcm-ai python scripts/check_env.py
```

## 主要入口

| 用途 | 地址 |
|------|------|
| 用户诊断 Web | http://localhost:8000/ |
| 管理端 | http://localhost:8000/admin |

### 用户端 Web 功能

- **智能诊断** — 体征采集、望诊上传/**摄像头拍照**、AI 诊断（LLM 不可用时自动规则降级）
- **中药百科** — 公开知识检索（`POST /api/knowledge/search`）
- **诊断历史** — Web 端仅存于浏览器 localStorage；小程序登录后同步服务端（`/api/diagnosis/history`，需微信 Token）

### 管理端

管理端（`/admin`）登录后可操作：

1. **概览** — 知识库/索引/模型/RAG 状态一览与快捷跳转
2. **患者管理** — 真实患者档案 CRUD、就诊记录（`data/patients.json`）
3. **知识库** — 文档列表 / 临床案例库 / 索引状态；**关键词搜索**
4. **Embedding / LLM / Rerank** — 模型配置与连通性测试
5. **RAG 检索** — 调试问答、调用日志与统计
6. **系统** — CORS、**异步/同步**重建向量索引、Admin Key、**RBAC 多角色 Key**

首次 Admin Key 见 `data/admin_config.json` 中的 `admin_api_key`（已在 `.gitignore`）。

| API 文档 | http://localhost:8000/docs |
| CLI 诊断 | `python -m tcm_ai.main` |

## RBAC（可选）

在 `data/admin_config.json` 中设置：

```json
"rbac": {
  "enabled": true,
  "keys": [
    { "name": "只读", "key": "your-viewer-key", "role": "viewer" },
    { "name": "运维", "key": "your-editor-key", "role": "editor" }
  ]
}
```

主 `admin_api_key` 始终为 **admin** 权限。角色：`viewer`（只读）< `editor`（写入/RAG）< `admin`（配置/同步重建/轮换密钥）。

## 数据域说明

| 域 | 存储 | 说明 |
|----|------|------|
| 患者档案 | `data/patients.json` + `data/visits/` | 管理端「患者管理」 |
| 诊断历史 | `data/history/{user_id}.json` 或 SQLite | 小程序用户隔离；`TCM_HISTORY_BACKEND=sql` 时用 `data/diagnosis_history.sqlite3` |
| 临床案例库 | `tcm_knowledge/cases/*.json` | RAG 参考资料，只读浏览 |
| 知识文档 | `tcm_knowledge/`（非 cases） | 可导入/上传/删除 |
| 系统配置 | `data/admin_config.json` | 模型与 Admin Key |

## API 概览

**诊断**

- `POST /api/diagnose` — multipart 多模态诊断
- `POST /api/diagnose/json` — JSON + base64（小程序）
- `GET /api/health-metrics` — 随机体征采样
- `GET/POST/DELETE /api/diagnosis/history` — 诊断历史（**需微信 Bearer Token**，按用户隔离）

**微信小程序**

- `POST /api/wx/login` — `wx.login` code 换 token（含 `expires_in`）
- `POST /api/wx/refresh` — 刷新 Token（过期宽限内免重新 wx.login）
- `GET /api/wx/me` — 当前登录用户
- `PUT /api/wx/profile` — 更新昵称/头像
- `GET /api/wx/session` — 校验登录态

在 `data/admin_config.json` 配置 `wechat_miniprogram.app_id` / `app_secret`；开发期可设 `dev_mode: true`（无 AppSecret 时自动启用模拟 openid）。

**知识检索**

- `POST /api/knowledge/search` — 公开向量检索（失败时关键词降级）

**管理端**（需 `X-Admin-API-Key`）

- `GET /api/admin/me` — 当前 Key 角色
- `GET /api/admin/metrics` — 运行指标（uptime、索引、限流后端等）
- `GET/POST/PUT/DELETE /api/admin/patients` — 患者 CRUD
- `POST /api/admin/rag/rebuild-index` — **同步**重建（admin）
- `POST /api/admin/rag/rebuild-index/async` — 异步重建（editor+）
- 更多见 `/docs`

## 生产安全

部署生产环境前请确认：

1. 设置 `TCM_ENV=production`（启动时校验配置，不合规将拒绝启动）
2. `wechat_miniprogram.dev_mode`: **false**
3. `wechat_miniprogram.token_secret`: 随机密钥（见 `docs/DEPLOYMENT.md`）
4. `server.cors_origins`: 填写实际域名，**勿用** `*`
5. 生产建议关闭 `allow_public_diagnose` / `allow_public_knowledge_search`
6. Admin Key 重新生成；管理端登录后使用 **HttpOnly Cookie** 会话（API Key 不再写入 sessionStorage）

详见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#安全建议)。

## 测试

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/unit tests/integration -q
# CI 使用 requirements-ci.txt；本地完整环境用 requirements.txt
```

## 重构文档

见 [重构文档.md](重构文档.md)。

## 许可证

Copyright (c) 2026 [paidaxin-12138](https://github.com/paidaxin-12138)

本仓库采用 [知识共享 署名-非商业性使用 4.0 国际许可协议](https://creativecommons.org/licenses/by-nc/4.0/)（CC BY-NC 4.0）进行许可。您可以自由地共享、复制、传播本作品的**非商业**用途，但须署名原作者。

完整许可文本见仓库根目录 [LICENSE](LICENSE)。
