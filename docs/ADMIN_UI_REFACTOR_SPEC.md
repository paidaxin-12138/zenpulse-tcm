<!-- Copyright (c) 2026 paidaxin-12138 — CC BY-NC 4.0 — see LICENSE -->

# 中医 AI 诊断系统 · 管理端 UI 模块重构说明书

> 供 **Stitch** 等前端重构工具使用。  
> 分析范围：管理端 `admin/index.html`（单文件 HTML/CSS/JS）。  
> 对照参考：C 端用户界面见 [FRONTEND_UI_REFACTOR_SPEC.md](./FRONTEND_UI_REFACTOR_SPEC.md)。

**代码路径**：`/Users/macmini/Downloads/中医/admin/index.html` + `admin/app.js`  
**访问地址**：http://localhost:8000/admin  
**后端路由**：`tcm_ai/api/routes/admin.py`（前缀 `/api/admin`）  
**最后同步代码**：2026-06-08

---

## 0. 实现状态速查（2026-06-08）

| 功能 | 状态 |
|------|------|
| 鉴权 / Dashboard / 配置 / RAG / 索引重建 | ✅ |
| 知识库文件 CRUD + 导入 | ✅ |
| 病例库只读 `GET /knowledge/case-library*` | ✅（非 `/cases` CRUD） |
| 患者档案 `GET/POST/PUT/DELETE /patients*` | ✅ |
| 关键词搜索 `POST /knowledge/search` | ✅ Enter / `#knowledge-keyword-search-btn` |
| 同步索引重建 `POST /rag/rebuild-index` | ✅ `#rebuild-index-sync-btn` |
| RBAC 多角色 Key | ✅ `rbac.enabled` + `/api/admin/me` |

## 1. 项目背景

管理端面向运维/知识库管理员，主要功能包括：

- **鉴权**：Admin API Key 登录与持久化
- **概览**：知识库、向量索引、模型配置、RAG 调用统计一览
- **知识库运维**：文件列表/删除、批量导入、在线文本上传、**病例库只读浏览**（`case-library`）
- **患者管理**：患者 CRUD + 就诊记录（`/api/admin/patients*`）
- **模型 API 配置**：Embedding / LLM / Rerank 独立配置、保存、连通性测试
- **RAG 调试**：问答测试、检索 chunk 展示、调用日志与统计
- **系统运维**：CORS、RAG 默认参数、异步重建向量索引（进度条）、重新生成 Admin Key

---

## 2. 模块清单

| 模块编号 | 模块名称 | 功能描述 | 核心交互 | 依赖数据 | 备注 |
|---------|---------|---------|---------|---------|-----|
| A01 | 页面头部 AdminHeader | 标题、副标题、操作流程提示 | 纯展示 | 静态文案 | — |
| A02 | 鉴权栏 AuthBar | Admin API Key 输入、保存、测试连接 | 保存 Key → `localStorage`；测试连接 → `GET /config` | `tcm_admin_api_key` (localStorage) | 未连接时 `#main-content` 隐藏 |
| A03 | 导航提示 NavHint | 各 Tab 功能说明条 | 纯展示 | 静态 | 黄色提示条 |
| A04 | Tab 导航 TabBar | 7 个功能 Tab 切换 | 点击 Tab → `switchTab()` 显示对应 Panel | `data-tab` 属性 | 概览为默认 Tab |
| A05 | 概览控制台 DashboardOverview | 6 块状态 Tile + 刷新 | 点击「刷新概览」→ `GET /dashboard`；Tile 内按钮跳转 Tab | knowledge/index/rebuild/models/rag_stats | 连接成功后自动加载 |
| A06 | 常用操作 QuickActions | 快捷跳转到知识库/模型/系统/RAG | `data-goto` 切换 Tab | 静态 | 位于概览 Panel 底部 |
| A07 | 知识库统计 KnowledgeStats | 展示知识库 JSON 统计 | 「刷新统计」→ `GET /knowledge/stats` | stats 对象 | 同时触发文件列表刷新 |
| A08 | 文件列表 KnowledgeFileList | 列出 `tcm_knowledge/` 下文件 | 刷新后渲染；每条可删除 | `GET /knowledge/files` | 删除后提示重建索引 |
| A09 | 批量文件导入 BatchImport | 多选 .txt/.json/.md 上传 | 选文件 + 子目录 + 覆盖选项 → `POST /knowledge/import-files` (multipart) | FormData: files, subdir, overwrite | 默认子目录 `imports` |
| A10 | 在线文本上传 TextUpload | 按相对路径写入文本内容 | 路径 + 内容 + 覆盖 → `POST /knowledge/upload` | path, content, overwrite | JSON 请求 |
| A11 | 病例库 CaseLibrary | 临床案例只读列表 + 详情 modal | 搜索 → `GET /knowledge/case-library?q=` | cases[] | **非** POST/PUT `/cases` |
| A12 | ~~案例表单 CaseForm~~ | — | — | — | **已移除**；病例来自 JSON 文件 |
| A13 | Embedding 配置 EmbeddingConfig | Provider/Model/BaseURL/API Key | 独立保存 → `PUT /config` (embedding 段)；测试 → `POST /system/test-embedding` | embedding 配置对象 | api_key 留空则不修改已保存值 |
| A14 | LLM 配置 LLMConfig | Provider/Model/BaseURL/Key/Temperature | 同 A13 模式 | llm 配置对象 | — |
| A15 | Rerank 配置 RerankConfig | Provider/Model/BaseURL/Key/Top N | 同 A13 模式；provider=none 时测试返回 skipped | rerank 配置对象 | — |
| A16 | RAG 问答调试 RAGQuery | 输入问题执行完整 RAG 流水线 | 「执行 RAG」→ `POST /rag/query` | question, top_k, enable_llm | 可选覆盖 retrieval/final top_k |
| A17 | RAG 回答展示 RAGAnswer | 展示 LLM 生成回答 | 纯展示 | `result.answer` | pre-wrap 样式 |
| A18 | Rerank 结果 ChunksReranked | 展示 rerank 后 chunk 列表 | `renderChunks()` 渲染前 500 字 | `result.reranked[]` | 显示 rerank_score |
| A19 | 初检索结果 ChunksRetrieved | 展示向量初检索 chunk | 同上 | `result.retrieved[]` | 显示 score |
| A20 | RAG 调用统计 RAGStats | JSON 展示调用统计 | 「刷新统计」→ `GET /rag/logs/stats` | stats 对象 | — |
| A21 | RAG 调用日志 RAGLogs | 日志列表 + 来源/类型筛选 | 刷新/筛选 change 事件；清空 → `DELETE /rag/logs` | logs[] (limit 30) | source: admin/diagnosis；kind: query/search |
| A22 | CORS 配置 CorsConfig | 逗号分隔允许来源 | 随「保存全部配置」提交 | server.cors_origins[] | 修改后需重启服务 |
| A23 | RAG 默认参数 RAGDefaults | retrieval_top_k / final_top_k / 缺失索引自动构建 | 随「保存全部配置」提交 | rag 配置段 | — |
| A24 | 索引重建 IndexRebuild | 异步重建向量索引 + 进度条 | confirm → `POST /rag/rebuild-index/async?force=true`；轮询 `GET /rag/rebuild-index/status` (1s) | rebuild status | 运行中禁用按钮 |
| A25 | 索引状态 IndexStatus | JSON 展示索引元信息 | 「刷新索引状态」→ `GET /system/index-status` | index status | — |
| A26 | 模型批量测试 ModelBatchTest | 一次性测试 Embedding+LLM+Rerank | → `POST /system/test-models` | all_ok 等 | 结果 JSON 展示 |
| A27 | Admin Key 轮换 KeyRegenerate | 重新生成管理端密钥 | confirm → `POST /config/regenerate-key`；写回 localStorage | admin_api_key | 旧 Key 立即失效 |
| A28 | 全局状态条 SystemStatus | 操作成功/失败提示 | `setStatus('system-status', ...)` | 消息文本 | 位于系统 Panel 底部 |
| A29 | RAG 状态条 RAGStatus | RAG 操作状态提示 | `setStatus('rag-status', ...)` | 消息文本 | 位于 RAG 问答卡片内 |
| — | **关键词知识搜索** | 按关键词搜索知识库（非向量） | **已实现**：Enter / `#knowledge-keyword-search-btn` → `POST /knowledge/search` | query, top_k | 与 RAG 向量检索区分 |
| — | **同步索引重建** | 阻塞式重建 | **已实现**：`#rebuild-index-sync-btn` | — | 小库调试 |
| — | **多管理员/RBAC** | 角色权限 | **已实现**：`rbac.keys` + viewer/editor/admin | — | 配置见 README |
| — | **Sidebar 布局** | 左侧固定导航 | **当前为顶部 Pill Tab** | — | 重构时可改 IA |

---

## 3. 页面布局描述

### 3.1 整体布局

单页 + **顶部 Pill Tab 切换**（非左侧 Sidebar）；内容区 `max-width: 1100px` 居中（`.wrap`）。

**未鉴权态**：仅显示 Header + AuthBar。  
**已鉴权态**：显示 NavHint + TabBar + 当前 Panel（其余 Panel `display:none`）。

```
┌──────────────────────────────────────────┐
│  A01 Header + A02 AuthBar（始终可见）       │
├──────────────────────────────────────────┤
│  [已连接后显示 #main-content]              │
│  A03 NavHint                              │
│  A04 TabBar: 概览|知识库|Emb|LLM|Rerank|RAG|系统 │
├──────────────────────────────────────────┤
│  当前 Panel（垂直堆叠 .card 卡片）          │
│    · 概览: A05 Dashboard + A06 QuickActions│
│    · 知识库: A07–A12 多个 card             │
│    · Embedding/LLM/Rerank: 各 1 card       │
│    · RAG: A16–A21 多个 card                │
│    · 系统: A22–A28 多个 card               │
└──────────────────────────────────────────┘
```

### 3.2 各 Tab 模块位置

| Tab | Panel ID | 主要内容（自上而下） |
|-----|----------|---------------------|
| 概览 | `panel-dashboard` | 控制台 Tile Grid → 常用操作按钮行 |
| 知识库 | `panel-knowledge` | 统计 → 文件列表 → 批量导入 → 在线上传 → 案例管理 |
| Embedding | `panel-embedding` | 配置表单 + 保存/测试 + 测试结果 pre |
| LLM | `panel-llm` | 同上 |
| Rerank | `panel-rerank` | 同上 |
| RAG 检索 | `panel-rag` | 问答表单 → LLM 回答 → Rerank 结果 → 初检索 → 统计 → 日志 |
| 系统 | `panel-system` | CORS → RAG 参数/索引/密钥/进度条 → 索引状态 → 模型测试结果 |

### 3.3 响应式断点

| 断点 | 行为 |
|------|------|
| **默认（PC）** | Grid `minmax(220px)`；Tab 与 AuthBar `flex-wrap` |
| **窄屏** | Tab 换行；AuthBar 输入框 `min-width: 240px`；无独立 `@media` 规则 |

**待补充**：移动端 Sidebar 折叠、表格横向滚动、Sticky TabBar。

---

## 4. 组件层级树

```
AdminPage (admin/index.html)
├── Wrap
│   ├── AdminHeader (A01)
│   │   ├── Title (h1)
│   │   ├── Subtitle
│   │   ├── WorkflowHint
│   │   └── AuthBar (A02)
│   │       ├── ApiKeyInput #api-key-input
│   │       ├── SaveKeyButton #save-key-btn
│   │       ├── TestConnectionButton #test-key-btn
│   │       └── AuthStatus #auth-status
│   │
│   └── MainContent #main-content (鉴权后显示)
│       ├── NavHint (A03)
│       ├── TabBar (A04)
│       │   ├── Tab[data-tab=dashboard] (default active)
│       │   ├── Tab[data-tab=knowledge]
│       │   ├── Tab[data-tab=embedding]
│       │   ├── Tab[data-tab=llm]
│       │   ├── Tab[data-tab=rerank]
│       │   ├── Tab[data-tab=rag]
│       │   └── Tab[data-tab=system]
│       │
│       ├── PanelDashboard #panel-dashboard (A05–A06)
│       │   ├── Card: DashboardOverview
│       │   │   ├── RefreshButton #load-dashboard-btn
│       │   │   └── DashGrid #dashboard-content
│       │   │       └── DashTile × N (动态)
│       │   └── Card: QuickActions
│       │       └── GotoButton[data-goto] × 5
│       │
│       ├── PanelKnowledge #panel-knowledge (A07–A12)
│       │   ├── Card: KnowledgeStats
│       │   ├── Card: KnowledgeFileList #knowledge-files
│       │   ├── Card: BatchImport
│       │   ├── Card: TextUpload
│       │   └── Card: CaseManagement
│       │       ├── CaseList #knowledge-cases
│       │       └── CaseForm (id 前缀 case-*)
│       │
│       ├── PanelEmbedding #panel-embedding (A13)
│       ├── PanelLLM #panel-llm (A14)
│       ├── PanelRerank #panel-rerank (A15)
│       │
│       ├── PanelRAG #panel-rag (A16–A21)
│       │   ├── Card: RAGQuery + RAGStatus
│       │   ├── Card: RAGAnswer #rag-answer
│       │   ├── Card: ChunksReranked #rag-reranked
│       │   ├── Card: ChunksRetrieved #rag-retrieved
│       │   ├── Card: RAGStats
│       │   └── Card: RAGLogs (filters + #rag-logs)
│       │
│       └── PanelSystem #panel-system (A22–A28)
│           ├── Card: CorsConfig
│           └── Card: RAGDefaults + IndexRebuild + KeyRegenerate
│               ├── RebuildProgressPanel #rebuild-progress-panel
│               │   ├── ProgressBar #rebuild-progress-bar
│               │   └── ProgressMeta #rebuild-progress-meta
│               ├── IndexStatus #index-status
│               ├── ModelTestResult #model-test-result
│               └── SystemStatus #system-status
│
└── InlineScript
    ├── adminFetch() / adminUploadFiles()
    ├── switchTab() / loadDashboard() / loadConfig()
    ├── collectConfig() / fillConfig() / savePartialConfig()
    ├── loadKnowledgeFiles() / loadCases() / loadRagLogs()
    ├── renderChunks() / updateRebuildProgress() / pollRebuildStatus()
    └── Event listeners (各按钮)
```

---

## 5. 样式与主题信息

### 5.1 设计 Token（已用 CSS Variables）

| Token | 值 | 用途 |
|-------|-----|------|
| `--bg` | `#faf9f6` | 页面背景 |
| `--card` | `#ffffff` | 卡片背景 |
| `--primary` | `#8b4513` | 主色、Tab 激活、标题 |
| `--primary-light` | `#d2b48c` | 回答区左边框、进度条渐变 |
| `--text` | `#3a2718` | 正文 |
| `--muted` | `#6d4c41` | 次要文字、label |
| `--border` | `#e8e5de` | 边框 |
| `--danger` | `#b71c1c` | 危险按钮、错误状态 |
| `--ok` | `#2d5016` | 成功状态 |
| **字体** | `"PingFang SC", "Microsoft YaHei", sans-serif` | 全局（与 C 端 serif 不同） |
| **圆角** | 卡片 `12–14px`；Tab `999px`（pill）；按钮/输入 `8px` | — |
| **阴影** | 较少；Header 用 gradient + border | 比 C 端更扁平 |
| **状态条** | `.status.ok` 绿底；`.status.err` 红底 | — |
| **Chunk 卡片** | `.chunk` 浅灰底 `#fcfcfb` | 文件/日志/RAG 结果复用 |
| **进度条** | `.progress-wrap` + `.progress-bar` 渐变动画 | 索引重建 |

### 5.2 按钮变体

| Class | 样式 |
|-------|------|
| `.btn-primary` | 棕底白字 |
| `.btn-secondary` | 灰底 `#efebe9` |
| `.btn-danger` | 红底白字 |

### 5.3 主题支持

- **暗色模式**：不支持
- **多套主题**：无；与 C 端共享主色 `#8b4513` 品牌色，字体栈不同

**待补充**：统一 C 端/管理端 Design System；Sidebar 暗色运维主题可选。

---

## 6. 数据流与状态管理

### 6.1 状态管理方式

原生 DOM + 内联 JS，**无**框架状态库。

| 状态 | 存储位置 |
|------|----------|
| Admin API Key | `localStorage['tcm_admin_api_key']` + `#api-key-input` |
| 当前 Tab | DOM class `active` on `.tab` / `.panel` |
| 全局配置表单 | 各 `#emb-*` `#llm-*` `#rerank-*` `#rag-*` `#cors-origins` 输入框 |
| 编辑中案例 ID | JS 变量 `editingCaseId` |
| 索引重建轮询 | JS 变量 `rebuildPollTimer` |
| 鉴权门控 | `#main-content.hidden` |

### 6.2 鉴权与请求流

```
用户输入 Key
  ├─ 保存 Key → localStorage → loadConfig()
  └─ 测试连接 → loadConfig()
       └─ GET /api/admin/config (Header: X-Admin-API-Key)
            ├─ 401 → auth-status 错误
            └─ 200 → fillConfig() + 显示 main-content + loadDashboard() + startRebuildPolling()
```

**请求封装**：

- `adminFetch(path, options)` — JSON API，自动加 `X-Admin-API-Key` + `Content-Type: application/json`
- `adminUploadFiles(path, formData)` — multipart，仅加 Key 头（不设 Content-Type）

后端同时支持 `Authorization: Bearer <key>`（UI 未使用）。

### 6.3 主要 API 映射

| 模块 | 方法 | 路径 | UI 使用 |
|------|------|------|---------|
| 加载配置 | GET | `/config` | ✅ |
| 保存配置（全量/分段） | PUT | `/config` | ✅ |
| 概览 | GET | `/dashboard` | ✅ |
| 重新生成 Key | POST | `/config/regenerate-key` | ✅ |
| RAG 问答 | POST | `/rag/query` | ✅ |
| 异步重建索引 | POST | `/rag/rebuild-index/async?force=true` | ✅ |
| 重建进度 | GET | `/rag/rebuild-index/status` | ✅ 轮询 1s |
| 同步重建 | POST | `/rag/rebuild-index` | ✅ admin |
| 知识库统计 | GET | `/knowledge/stats` | ✅ |
| 文件列表 | GET | `/knowledge/files` | ✅ |
| 删除文件 | DELETE | `/knowledge/files/{path}` | ✅ |
| 批量导入 | POST | `/knowledge/import-files` | ✅ multipart |
| 文本上传 | POST | `/knowledge/upload` | ✅ |
| 关键词搜索 | POST | `/knowledge/search` | ✅ |
| 病例库 | GET | `/knowledge/case-library*` | ✅ |
| 患者 CRUD | GET/POST/PUT/DELETE | `/patients*` | ✅ |
| 索引状态 | GET | `/system/index-status` | ✅ |
| 测试全部模型 | POST | `/system/test-models` | ✅ |
| 测试 Embedding | POST | `/system/test-embedding` | ✅ |
| 测试 LLM | POST | `/system/test-llm` | ✅ |
| 测试 Rerank | POST | `/system/test-rerank` | ✅ |
| RAG 统计 | GET | `/rag/logs/stats` | ✅ |
| RAG 日志 | GET | `/rag/logs?limit&source&kind` | ✅ |
| 清空日志 | DELETE | `/rag/logs` | ✅ |

### 6.4 配置对象结构（collectConfig / fillConfig）

```json
{
  "embedding": { "provider", "model", "base_url", "api_key" },
  "llm": { "provider", "model", "base_url", "api_key", "temperature" },
  "rerank": { "provider", "model", "base_url", "api_key", "top_n" },
  "rag": { "retrieval_top_k", "final_top_k", "rebuild_on_missing_index" },
  "server": { "cors_origins": ["*"] }
}
```

持久化文件：`data/admin_config.json`（api_key 在 GET 响应中 mask）。

### 6.5 RAG Query 响应使用

| 字段 | UI 使用 |
|------|---------|
| `answer` | ✅ `#rag-answer` |
| `reranked[]` | ✅ chunk 列表 (rerank_score) |
| `retrieved[]` | ✅ chunk 列表 (score) |
| `retrieved_count` | ✅ 状态条文案 |
| `providers.embedding/rerank/llm` | ✅ 状态条文案 |
| 其他字段 | ❌ 待补充展示 |

---

## 7. 关键交互细节

| 交互 | 当前实现 | 缺失/待补充 |
|------|----------|-------------|
| **鉴权门控** | 无 Key 时主内容隐藏；localStorage 有 Key 则页面加载自动 `loadConfig()` | 无 Key 过期自动登出；无 Bearer 方式 UI |
| **Tab 切换** | Pill 按钮 + panel display 切换 | 无 URL hash 路由；刷新丢失 Tab 状态 |
| **概览 Tile** | 动态 HTML + 内嵌跳转按钮 | 无图表；重建进度 Tile 不实时刷新（需手动刷新概览） |
| **配置保存** | Embedding/LLM/Rerank 各 Tab 独立保存；系统 Tab「保存全部配置」 | 无「未保存变更」提示；api_key 空值语义依赖后端 merge |
| **Provider 测试** | 用当前表单值 POST 测试（可不保存先测） | 无 loading spinner；结果 JSON 原始展示 |
| **批量导入** | multipart 多文件；结果 JSON 展示 | 无单文件进度；无 drag-drop |
| **文件删除** | confirm 对话框 | 无批量删除 |
| **案例编辑** | 列表内编辑/删除；表单新建/更新 | 无分页（固定 limit=50）；非 clinical_cases.json 只读 |
| **RAG 调试** | 问题必填；可选 top_k；可关 LLM | 无历史问题；chunk 截断 500 字无展开 |
| **RAG 日志** | 来源/类型下拉筛选；清空 confirm | 无分页 UI；无导出 |
| **索引重建** | confirm → async；进度条 0–100%；running 时禁用按钮；完成自动刷新索引状态 | 无取消任务；无同步重建选项 |
| **Key 轮换** | confirm → 新 Key 写 localStorage + 输入框 | 无复制按钮；无 QR |
| **错误提示** | `.status.ok/.err` 条 + `alert()` + confirm | 无 Toast 组件；401 不统一跳转登录 |
| **CORS 提示** | hint 文案说明需重启 | 无重启引导 |

---

## 8. Stitch 重构建议

### 8.1 推荐拆分组件

```
admin/
├── layout/AdminLayout.tsx
├── auth/AuthGate.tsx
├── dashboard/DashboardTiles.tsx, QuickActions.tsx
├── knowledge/
│   ├── KnowledgeStats.tsx
│   ├── FileList.tsx
│   ├── BatchImport.tsx
│   ├── TextUpload.tsx
│   └── CaseManager.tsx
├── models/
│   ├── EmbeddingConfigForm.tsx
│   ├── LLMConfigForm.tsx
│   └── RerankConfigForm.tsx
├── rag/
│   ├── RAGQueryPanel.tsx
│   ├── ChunkList.tsx
│   ├── RAGStatsPanel.tsx
│   └── RAGLogPanel.tsx
└── system/
    ├── CorsSettings.tsx
    ├── IndexRebuildPanel.tsx
    └── KeyManagement.tsx
```

### 8.2 信息架构建议

- 当前 **7 Tab 平铺** 适合 MVP；数据量大时可改为 **左侧 Sidebar**（知识库 / 模型 / RAG / 系统 分组）
- 补全 **同步重建** 高级选项（`POST /rag/rebuild-index`，小库 debug）
- 概览 Tile 增加 **重建进度实时订阅**（复用已有 poll 逻辑）
- 统一 **StatusToast** 替代 alert + 分散 status div

### 8.3 与 C 端关系

| 项目 | C 端 (`frontend/`) | 管理端 (`admin/`) |
|------|-------------------|------------------|
| 用户 | 患者/使用者 | 运维/管理员 |
| 鉴权 | 无 | Admin API Key |
| 诊断 | ✅ POST /api/diagnose | ❌ |
| 知识检索 | 公开 API 未接 UI | RAG 全链路调试 |
| 视觉 | serif + 大标题 | sans-serif + Tab 控制台 |

---

## 9. 相关文件索引

| 文件 | 说明 |
|------|------|
| `admin/index.html` | 管理端 UI（本文分析对象） |
| `tcm_ai/api/routes/admin.py` | 管理端 API 路由 |
| `tcm_ai/api/routes/pages.py` | `GET /admin` 页面路由 |
| `tcm_ai/api/schemas/admin.py` | 请求/响应 Schema |
| `data/admin_config.json` | 运行时配置（gitignore） |
| `data/admin_config.example.json` | 配置示例 |
| `docs/FRONTEND_UI_REFACTOR_SPEC.md` | C 端 UI 重构说明书 |

---

*文档最后更新：2026-06-08*
