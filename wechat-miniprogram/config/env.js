// Copyright (c) 2026 paidaxin-12138
// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
// https://creativecommons.org/licenses/by-nc/4.0/

/**
 * 小程序 API 环境
 *
 * 开发者工具：127.0.0.1 通常比 localhost 更稳定
 * 真机预览：我的 → 服务器设置，或在此填写 customBaseUrl
 * 勾选：开发者工具 → 详情 → 本地设置 → 不校验合法域名
 *
 * 毕设局域网部署：无需 HTTPS 与正式上架；生产环境需 HTTPS + Token 鉴权
 */
export const API_ENV = {
  /** 真机预览默认地址（与 /api/public/dev-hints 一致；模拟器也会优先使用） */
  customBaseUrl: 'http://192.168.1.7:8000/api',
  /** 自动探测候选（按顺序尝试） */
  baseUrlCandidates: [
    'http://127.0.0.1:8000/api',
    'http://localhost:8000/api'
  ],
  /** 普通接口（登录、体征、历史） */
  defaultTimeoutMs: 12000,
  /** 诊断（含图片；需与 app.json networkTimeout.request 一致） */
  diagnoseTimeoutMs: 60000,
  /** 脉象波形分析 */
  pulseTimeoutMs: 30000,
  /** 启动探测超时 */
  probeTimeoutMs: 4000
};
