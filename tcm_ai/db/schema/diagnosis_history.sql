-- 诊断历史（预留 — 生产环境建议使用微信小程序云开发存储桶）
--
-- 小程序端：config/cloud.js 开启后，历史写入云存储
--   diagnosis-history/{userId}/index.json
--   diagnosis-history/{userId}/{entryId}.json
--
-- 自建后端（开发/回退）：TCM_HISTORY_BACKEND=json（默认）
-- 若未来要在服务端落库，可使用下方 SQLite 表结构：

CREATE TABLE IF NOT EXISTS diagnosis_history (
    id              TEXT PRIMARY KEY,
    user_id         TEXT,
    time            TEXT NOT NULL,
    syndrome        TEXT NOT NULL DEFAULT '',
    diagnosis       TEXT NOT NULL DEFAULT '',
    summary         TEXT NOT NULL DEFAULT '',
    diagnosis_mode  TEXT NOT NULL DEFAULT '',
    detail_json     TEXT,
    cloud_file_id   TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_diagnosis_history_user_time
    ON diagnosis_history (user_id, time DESC);
