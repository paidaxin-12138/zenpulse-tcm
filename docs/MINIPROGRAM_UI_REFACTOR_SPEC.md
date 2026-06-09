<!-- Copyright (c) 2026 paidaxin-12138 — CC BY-NC 4.0 — see LICENSE -->

# 中医 AI 诊断系统 · 微信小程序 UI 模块重构说明书（Stitch 用）

> 供 **Stitch** / Figma / 设计转代码工具使用。  
> 代码路径：`wechat-miniprogram/`  
> 视觉对齐参考：Web C 端 `frontend/index.html`（ZenPulse 侧栏 + 中药百科库暖棕 Bento 风）  
> 后端 API 与 Web 共用同一 FastAPI 服务（默认 `http://localhost:8000`）

**最后同步**：2026-06-08

---

## 0. Stitch 一键提示词（复制整段）

```
你是一名资深微信小程序 UI/UX 设计师 + 前端工程师。请重构「中医 AI 智能诊断」微信小程序界面，输出 WXML + WXSS + 页面结构说明（可附 JS 事件清单），风格必须与已有 Web 版 ZenPulse 中医智库对齐。

【产品定位】
移动端多步诊断向导 + 个人中心；面向普通用户，强调望闻问切多模态采集与 AI 辨证，结果仅供参考。

【设计系统 — 必须与 Web 一致】
- 主色 primary: #8B4513（鞍褐）
- 背景 bg: #FAF9F6（米白纸感）
- 卡片 surface: #FFFFFF
- 次要文字: #6D4C41 / #5D4037
- 正文: #3A2718
- 边框: #E8E5DE / #D2B48C
- 成功: #2d5016 · 错误: #8B0000 / #ba1a1a
- 圆角：卡片 16–24rpx，主按钮 12–16rpx，Pill 标签全圆角
- 字体：PingFang SC / Microsoft YaHei，标题 serif 感可保留
- 阴影：0 2rpx 10rpx rgba(139,69,19,0.08)
- 减少 Emoji 图标，改用线性 icon 或简约几何装饰（与 Web Material Symbols 气质一致）
- 支持深色模式可选（第二主题，非必须）

【信息架构 — 建议重构为 TabBar 四栏】
1. 首页 Home — 品牌介绍 + 「开始问诊」主 CTA + 系统状态条
2. 诊断 Diagnosis — 合并 metrics + upload 为分步向导（Step 1 体征 / Step 2 望诊拍照 / Step 3 确认提交）
3. 百科 Library — 新增：搜索框 + 分类 Pill（解表药/清热药/补益药等）+ 结果卡片（对齐 Web #view-library）
4. 我的 Profile — 诊断历史 + 设置 + 关于 + 法律链接

保留独立页面：pages/result/result（诊断报告全屏）、pages/history/history（历史列表，可从 Profile 进入）。

【现有页面映射（重构前）】
- pages/index — 首页入口
- pages/metrics — 健康指标表单
- pages/upload — 舌/面/眼三图（wx.chooseMedia + 相机）
- pages/result — 诊断报告
- pages/profile — 个人中心 + 历史摘要
- pages/history — 完整历史列表（当前较少直达）

【核心用户流程】
首页 → 体征（心率/脉搏/血压/年龄/性别，支持「随机采样」）→ 望诊三图（相册/相机，可删可预览）→ POST 诊断 → 结果页 → 保存历史

【必须接线的 API（baseUrl: /api）】
- GET  /health-metrics — 随机体征
- POST /diagnose/json — 小程序专用 JSON+base64 图片
- GET  /system/status — 页脚/首页提示 RAG/LLM 是否就绪
- POST /knowledge/search — 百科 { query, top_k }
- GET  /diagnosis/history — 服务端历史列表
- POST /diagnosis/history — 保存一条
- DELETE /diagnosis/history — 清空
- DELETE /diagnosis/history/{id} — 删除单条

【DiagnoseResponse 必须展示的字段】
syndrome, analysis, suggestions[], prescriptions[],
face_analysis[], tongue_analysis[], eye_analysis[],
fusion_summary, diagnosis_mode (llm|rule|metrics), llm_fallback_reason,
pulse_characteristics{pulse_type, description, characteristics},
diagnosis, source, disclaimer

【诊断模式 UI】
- diagnosis_mode=rule：顶部 amber 提示条「LLM 不可用，已降级规则引擎」
- diagnosis_mode=metrics：提示「仅基于体征的简要评估」

【各页模块清单】
P01 HomeHeader — Logo/标题/副标题
P02 FeatureGrid — 六项能力（指标/舌/面/眼/脉/辨证）
P03 SystemStatusBar — 绑定 /api/system/status
P04 PrimaryCTA — 开始问诊
P05 MetricsForm — 六项输入 + 随机采样按钮
P06 GenderSelector — 男/女 Pill
P07 ImageCaptureCard ×3 — 舌/面/眼，占位/预览/删除/重拍/全屏预览
P08 StepIndicator — 诊断向导步骤条
P09 DiagnoseSubmit — 加载态「AI 正在深度辨证…」
P10 ReportHeader — 时间 + 证型 Badge
P11 ReportBlocks — 证候/融合摘要/面舌目/建议/方剂/脉象/完整报告
P12 HistoryListItem — 证型 + 时间 + 摘要 + 删除
P13 LibrarySearch — 搜索 + 分类 Pill
P14 LibraryResultCard — 标题/来源/内容摘要
P15 ProfileMenu — 历史/设置/帮助/关于
P16 LegalLinks — 隐私/条款/算法说明（WebView 或内置页）

【交互细节】
- 体征：metrics 页必填校验（现有逻辑保留）
- 图片：至少一张才可提交；compressImage quality≈50
- 加载：wx.showLoading mask；失败解析 detail 数组
- 历史：优先服务端，wx.storage 备份；进入 Profile 时 pull 同步
- 分享：onShareAppMessage 带证型摘要
- 重新诊断：清空 globalData + 表单项

【不要破坏】
- utils/api.js 中 wxDiagnose() 的 base64 映射：tongueImage→tongue, faceImage→face, eyeImage→eye
- eventChannel 传 metrics / result（或改为 globalData 单一数据源）
- app.json 需配置 request 合法域名（生产环境）

【交付物】
1. 每页 WXML 结构树 + WXSS（rpx）
2. 组件拆分建议（components/metrics-form, image-capture-card, report-block…）
3. app.json tabBar 与页面路由表
4. 与 Web 对照的差异说明（仅小程序有的：原生相机、分享；Web 已有但小程序待补：百科 Tab）

【参考代码路径】
wechat-miniprogram/pages/*/*.wxml
frontend/index.html（视觉与百科布局）
docs/FRONTEND_UI_REFACTOR_SPEC.md
```

---

## 1. 项目背景

微信小程序是 Web C 端的**多页向导版**：分步采集体征与望诊图片，调用 `POST /api/diagnose/json` 获取辨证结果。历史记录目前主要存 `wx.storage`，**尚未**对接服务端 `/api/diagnosis/history`，**无**中药百科页。

---

## 2. 当前页面与路由

| 路径 | 导航栏标题 | TabBar | 功能 |
|------|-----------|--------|------|
| pages/index/index | 中医智能诊断系统 | ✅ 首页 | 功能介绍、开始诊断、历史入口（跳 profile） |
| pages/metrics/metrics | 健康指标 | — | 六项指标 + 随机生成 + 下一步 |
| pages/upload/upload | 图片上传 | — | 舌/面/眼 + 开始诊断 |
| pages/result/result | 诊断结果 | — | 报告展示 + 分享 + 重新诊断 |
| pages/profile/profile | 个人中心 | ✅ 我的 | 菜单 + 最近历史 |
| pages/history/history | 诊断历史 | — | 完整历史列表（入口少） |

**TabBar 现状**：仅「首页」「我的」两项，emoji 未配置 iconPath。

---

## 3. 组件层级（现状）

```
App (app.js — globalData.baseUrl, diagnosisHistory)
├── Tab: index
│   └── 功能网格 + CTA
├── Tab: profile
│   ├── UserSection
│   ├── MenuList
│   └── HistoryPreview
├── metrics (wizard step 1)
│   └── MetricsForm + RandomBtn
├── upload (wizard step 2)
│   └── ImageCapture ×3
├── result
│   └── ReportBlocks（缺 face/tongue/eye/fusion/prescriptions/mode）
└── history
    └── HistoryList
```

---

## 4. 样式 Token（自 app.wxss）

| Token | 值 | 用途 |
|-------|-----|------|
| page bg | #FAF9F6 | 页面背景 |
| primary | #8B4513 | 导航栏、按钮、标题 |
| primary hover | #6B340B | 按钮按下 |
| border | #D2B48C / #E8E5DE | 输入框、分割 |
| card | #FFFFFF | 卡片 |
| error | #8B0000 | 错误提示 |
| success | #2d5016 | 成功提示 |
| 圆角 btn | 12rpx | 按钮 |
| 圆角 card | 16rpx | 卡片 |

**重构目标**：抽离 `styles/tokens.wxss`，与 Web CSS Variables 命名对齐。

---

## 5. API 与数据流

### 5.1 baseUrl

`app.globalData.baseUrl = 'http://localhost:8000/api'`（开发）；生产改为 HTTPS 域名并在小程序后台配置。

### 5.2 接口矩阵

| 接口 | 方法 | 小程序现状 | 重构目标 |
|------|------|-----------|---------|
| /health-metrics | GET | ✅ metrics 随机 | ✅ |
| /diagnose/json | POST | ✅ wxDiagnose | ✅ |
| /system/status | GET | ❌ | ✅ 首页/诊断页状态条 |
| /knowledge/search | POST | ❌ | ✅ 百科 Tab |
| /diagnosis/history | GET/POST/DELETE | ❌ 仅 storage | ✅ 双写 |

### 5.3 wxDiagnose 请求体

```json
{
  "heart_rate": 72, "pulse": 72, "systolic": 120, "diastolic": 80,
  "age": 30, "gender": "男",
  "images": {
    "tongue": "data:image/jpeg;base64,...",
    "face": "...",
    "eye": "..."
  }
}
```

### 5.4 页面间传参

- metrics → upload：`eventChannel.emit('passMetrics', { metrics })`
- upload → result：`eventChannel.emit('passDiagnosisResult', { result })`
- 备份：`wx.setStorageSync('lastDiagnosisResult', result)`

**重构建议**：统一 `app.globalData.consultation = { metrics, images, result }` 减少 eventChannel 丢失。

---

## 6. 与 Web 版差异（Stitch 应对齐 Web）

| 能力 | Web (`frontend/index.html`) | 小程序现状 |
|------|---------------------------|-----------|
| 布局 | 侧栏三视图 | 多页 + 双 Tab |
| 百科检索 | ✅ | ❌ 待新增 Tab |
| 摄像头 | getUserMedia 模态 | ✅ 原生 chooseMedia |
| 历史 | 服务端 + localStorage | 仅 storage |
| 多模态结果块 | 全面 | 缺 face/tongue/eye/fusion/prescriptions |
| 诊断模式提示 | ✅ | ❌ |
| 法律页 | /legal/* | Modal 占位 |

---

## 7. 重构建议 IA（推荐）

```
TabBar: [首页] [诊断] [百科] [我的]

诊断 Tab 内嵌 Stepper：
  Step1 MetricsForm
  Step2 ImageCapture×3
  → navigateTo result

百科 Tab：
  SearchBar + CategoryPills + ResultCards

我的 Tab：
  HistoryList (server-first) + Settings + About
```

---

## 8. 关键交互清单

| 交互 | 现状 | Stitch 应设计 |
|------|------|--------------|
| 随机体征 | API + 本地 fallback | 保留，按钮次要样式 |
| 图片 | 压缩/预览/删除 | Bento 大卡铺满预览（对齐 Web scan-preview） |
| 诊断加载 | wx.showLoading | 全屏遮罩 + 阶段文案 |
| 结果分享 | ActionSheet | 保留，补「保存报告」占位 |
| 历史清空 | profile/history | 确认 Modal + DELETE API |
| 错误 | Toast 泛化 | 展示 API detail 首句 |

---

## 9. 文件索引

| 文件 | 说明 |
|------|------|
| wechat-miniprogram/app.json | 路由与 TabBar |
| wechat-miniprogram/app.wxss | 全局样式 |
| wechat-miniprogram/utils/api.js | API 封装 |
| wechat-miniprogram/pages/* | 各页面 |
| frontend/index.html | Web 视觉参考 |
| docs/FRONTEND_UI_REFACTOR_SPEC.md | Web 规格 |

---

*文档生成日期：2026-06-08*
