<!-- Copyright (c) 2026 paidaxin-12138 — CC BY-NC 4.0 — see LICENSE -->

# 生产部署指南

本文档介绍如何使用 **Docker** 或 **systemd** 部署中医 AI 诊断系统。

## 前置要求

| 组件 | 说明 |
|------|------|
| Python | 3.10+（Docker 镜像使用 3.11） |
| 内存 | 建议 ≥ 8GB（本地 Embedding + 可选 CrossEncoder） |
| 磁盘 | 模型 `models/` + 向量索引 `vector_store/` + 知识库 |
| Ollama（可选） | 若 LLM/Embedding 走 Ollama，需单独部署并开放 11434 |

## 首次部署 checklist

1. 复制配置：`cp data/admin_config.production.example.json data/admin_config.json`
2. 编辑 `data/admin_config.json`：
   - 生成并填入 `admin_api_key`、`wechat_miniprogram.token_secret`（各 ≥32 字符随机值）
   - 设置 `server.cors_origins` 为实际域名
   - 确认 `allow_public_diagnose` / `allow_public_knowledge_search` / **`allow_public_vitals`** / **`allow_public_pulse`** 为 **false**
   - 确认 `wechat_miniprogram.dev_mode` 为 **false**
3. 设置环境：`export TCM_ENV=production`
4. 构建向量索引：`python scripts/build_index.py --force`
5. 启动服务并访问 `/admin` 登录（HttpOnly Cookie 会话）
6. 测试模型连通性与 `/api/ready`

> 本地开发仍可用 `data/admin_config.example.json`；**切勿**将 example 中的占位符直接用于生产。

---

## 方式一：Docker Compose（推荐）

### 1. 构建并启动

```bash
docker compose up -d --build
```

### 2. 首次构建索引（容器内）

```bash
docker compose exec tcm-ai python scripts/build_index.py --force
```

### 3. 访问

| 服务 | 地址 |
|------|------|
| 用户 Web | http://localhost:8000/ |
| 管理端 | http://localhost:8000/admin |
| API 文档 | http://localhost:8000/docs |

### 4. 持久化卷

`docker-compose.yml` 已挂载（容器内以 **uid 10001** 用户运行，宿主机目录需可写）：

- `./data` — 配置与 RAG 日志
- `./tcm_knowledge` — 知识库
- `./vector_store` — 向量索引
- `./models` — 本地 Embedding 模型

### 5. 与 Ollama 联调

若 LLM 使用宿主机 Ollama，在 `data/admin_config.json` 中将 `base_url` 设为：

```json
"base_url": "http://host.docker.internal:11434"
```

Linux 需在 `docker-compose.yml` 添加 `extra_hosts: ["host.docker.internal:host-gateway"]`（已配置）。

### 6. 生产 CORS

```json
"server": {
  "cors_origins": ["https://your-domain.com"]
}
```

修改后重启容器：`docker compose restart tcm-ai`

---

## 方式二：systemd（裸机 / VM）

### 1. 安装依赖

```bash
cd /opt/tcm-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_index.py --force
```

### 2. 安装 unit 文件

```bash
sudo cp deploy/tcm-ai.service /etc/systemd/system/
# 编辑 WorkingDirectory、User、ExecStart 路径
sudo nano /etc/systemd/system/tcm-ai.service
sudo systemctl daemon-reload
sudo systemctl enable tcm-ai
sudo systemctl start tcm-ai
```

### 3. 常用命令

```bash
sudo systemctl status tcm-ai
sudo journalctl -u tcm-ai -f
sudo systemctl restart tcm-ai
```

### 4. 反向代理（Nginx 示例）

完整示例（HTTPS、限流、`X-Forwarded-For`）见 **[deploy/nginx.example.conf](../deploy/nginx.example.conf)**。

最小配置：

```nginx
server {
    listen 80;
    server_name tcm.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 20M;
    }
}
```

HTTPS 建议使用 certbot 或云厂商负载均衡终止 TLS。

---

## 环境变量

| 变量 | 用途 | 默认 |
|------|------|------|
| `TCM_HOST` | 监听地址 | `0.0.0.0` |
| `TCM_PORT` | 端口 | `8000` |
| `TCM_ENV` | 运行环境（`development` / `production`） | 本地 `python web_server.py` 为 `development`；**Docker / systemd 镜像默认为 `production`** |

---

## 运维

### 重建向量索引

**管理端（推荐）**：系统 →「重建向量索引」，后台异步执行并显示进度条。

**命令行**：

```bash
python scripts/build_index.py --force
# Docker:
docker compose exec tcm-ai python scripts/build_index.py --force
```

**Admin API（异步）**：

```bash
curl -X POST -H "X-Admin-API-Key: <key>" \
  "http://localhost:8000/api/admin/rag/rebuild-index/async?force=true"
curl -H "X-Admin-API-Key: <key>" \
  "http://localhost:8000/api/admin/rag/rebuild-index/status"
```

知识库更新后执行上述任一方式。

### 日志

- 应用：stdout（journal / `docker compose logs -f`）
- RAG：管理端 **RAG 检索 → 调用日志**，可按 `diagnosis` / `admin` 筛选

### 健康检查

| 端点 | 用途 |
|------|------|
| `GET /api/health` | **存活**探针（进程已启动） |
| `GET /api/ready` | **就绪**探针（向量索引 / RAG 依赖可用） |

```bash
curl -s http://localhost:8000/api/health
curl -s http://localhost:8000/api/ready
```

Docker Compose 已对 `/api/ready` 做 `healthcheck`。Nginx 反代时请设置 `X-Forwarded-For` / `X-Real-IP`，以便限流与 Admin 鉴权失败计数使用真实客户端 IP。

### 备份

```bash
bash scripts/backup.sh              # 默认写入 backups/tcm-backup-<时间戳>/
bash scripts/backup.sh /path/to/dir # 自定义目录
```

手动备份亦可包含：

- `data/admin_config.json`
- `data/diagnosis_history.sqlite3`（若 `TCM_HISTORY_BACKEND=sql`）
- `tcm_knowledge/`
- `vector_store/`

### 诊断历史 SQLite

默认 `TCM_HISTORY_BACKEND=json`。多实例或希望历史落库时：

```bash
export TCM_HISTORY_BACKEND=sql
export TCM_HISTORY_DATABASE_URL=sqlite:///data/diagnosis_history.sqlite3
python scripts/migrate_history_to_sql.py   # 自 JSON 迁移（可 --dry-run）
```

### 多 worker 限流（Redis）

单进程使用内存滑动窗口；`uvicorn --workers N` 或多副本部署请设置：

```bash
export TCM_REDIS_URL=redis://127.0.0.1:6379/0
pip install redis
```

管理端 `GET /api/admin/metrics` 可查看 `redis_rate_limit` 与运行指标。

### Prometheus

```bash
curl -s http://127.0.0.1:8000/metrics
# 含 tcm_http_requests_total{method,route,status} 请求计数
# 生产建议 Nginx 内网限制 /metrics，或设置 TCM_METRICS_TOKEN
export TCM_METRICS_TOKEN=your-scrape-token
curl -H "Authorization: Bearer $TCM_METRICS_TOKEN" https://your-domain/metrics
```

### 管理端 Cookie 会话

浏览器登录 `POST /api/admin/session/login` 后，API Key 写入 **HttpOnly Cookie**（默认 8 小时，`server.admin_session_ttl_hours`）。登出会将 `jti` 写入 Redis 黑名单（需 `TCM_REDIS_URL`；无 Redis 时进程内黑名单）。脚本/自动化仍可使用 `X-Admin-API-Key` 头。

### 小程序 Token 刷新

- 登录/刷新响应含 `expires_in`（秒）
- `POST /api/wx/refresh`：Token 未过期或处于 `token_refresh_grace_hours`（默认 168h）宽限内可换新 Token
- 小程序 `utils/auth.js` 在到期前 24h 自动刷新

---

## 安全建议

1. 设置 **`TCM_ENV=production`**（Docker：`environment: TCM_ENV: production`）
2. 配置 **`wechat_miniprogram.token_secret`**（随机 32+ 字节）；**禁止** `dev_mode: true`
3. **`server.cors_origins`** 填写实际前端域名，勿用 `["*"]`
4. 生产建议关闭 **`allow_public_diagnose`** / **`allow_public_knowledge_search`** / **`allow_public_vitals`** / **`allow_public_pulse`**（实验性脉象 API）
5. 小程序生产环境需配置 **`wechat_miniprogram.token_secret`** 且 **`dev_mode: false`**；体征与诊断接口走 Bearer Token，勿依赖公开接口
6. Admin Key 生产环境重新生成，仅 HTTPS + 内网使用；管理端通过 `/api/admin/session/login` 建立 HttpOnly Cookie 会话
7. Prometheus：`GET /metrics`（可选 `TCM_METRICS_TOKEN`）；Nginx 建议内网限制 `/metrics`
8. 8000 不对公网裸奔，走 Nginx/内网
9. 展示 API 返回的 `disclaimer`

`data/admin_config.json` 生产示例片段：

```json
{
  "server": {
    "cors_origins": ["https://your-domain.com"],
    "allow_public_diagnose": false,
    "allow_public_knowledge_search": false,
    "allow_public_vitals": false,
    "allow_public_pulse": false,
    "rate_limit_per_minute": 60
  },
  "wechat_miniprogram": {
    "dev_mode": false,
    "token_secret": "your-random-secret"
  }
}
```

---

## 故障排查

| 现象 | 处理 |
|------|------|
| RAG 无结果 | 重建索引；测试 Embedding |
| LLM 超时 | 检查 Ollama / API Key |
| Docker 连不上 Ollama | `host.docker.internal:11434` |
| CORS 错误 | 改 `server.cors_origins` 并重启 |
