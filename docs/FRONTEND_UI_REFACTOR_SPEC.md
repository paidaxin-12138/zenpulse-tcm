# 中医 AI 诊断系统 · Web 前端 UI 模块重构说明书

> 供 **Stitch** 等前端重构工具使用。  
> 分析范围：Web C 端主前端 `frontend/index.html`（Stitch 侧栏布局，单文件 ~1012 行）。  
> 对照参考：微信小程序 `wechat-miniprogram/`（多页流程；Web 已用 localStorage 实现历史）。

**代码路径**：`/Users/macmini/Downloads/中医/frontend/index.html`  
**最后同步代码**：2026-06-08

---

## 0. 实现状态速查（2026-06-08）

| 功能 | 状态 |
|------|------|
| 侧栏三视图（智能诊断 / 中药百科 / 诊断历史） | ✅ |
| `POST /api/diagnose` | ✅ |
| `GET /api/health-metrics` + 随机采样按钮 | ✅ |
| `POST /api/knowledge/search` 百科检索 | ✅ |
| 诊断历史 localStorage | ✅ |
| 多模态结果 `face/tongue/eye/fusion_summary` | ✅ |
| `#new-consultation-btn` 完整重置 | ✅ |
| 摄像头 `getUserMedia` | ✅ 拍照按钮 + 模态框 |
| 服务端历史持久化 | ✅ `/api/diagnosis/history` |

## 1. 项目背景

这是一个中医 AI 辅助诊断系统的前端界面，主要功能包括：

- 舌象/面部/眼部图像采集与预览（**文件上传**，非摄像头）
- 生理参数输入（心率、脉搏、血压；年龄、性别）+ **随机采样**（`/api/health-metrics`）
- 启动诊断并展示诊断结果（证型、治则、方剂、调理建议、**面/舌/目诊、融合摘要**）
- 中医知识检索（**已实现**：百科页 `searchLibrary()` → `POST /api/knowledge/search`）
- 历史记录（**已实现**：`localStorage`，`#view-history`）

---

## 2. 模块清单

| 模块编号 | 模块名称 | 功能描述 | 核心交互 | 依赖数据 | 备注 |
|---------|---------|---------|---------|---------|-----|
| M01 | 页面头部 Header | 展示系统标题与副标题，中医风格装饰（阴阳符号、顶部渐变条） | 纯展示，无交互 | 静态文案 | 无 Logo 图、无用户菜单 |
| M02 | 健康指标区 MetricsSection | 展示/编辑心率、脉搏、收缩压/舒张压；年龄、性别 | 页面加载调用 `/api/health-metrics`；**「随机采样」**按钮可刷新；用户可手动编辑全部字段 | 同上 | **无体温** |
| M03 | 舌苔图片上传 TongueUpload | 选择本地舌苔图片并预览 | 点击预览区 → 触发 `<input type="file">` → FileReader 显示缩略图 | `tongue-upload` File 对象 | **非摄像头**，无 Tab，与面/眼并列卡片 |
| M04 | 面部图片上传 FaceUpload | 选择本地面部图片并预览 | 同 M03 | `face-upload` File | 同上 |
| M05 | 眼部图片上传 EyeUpload | 选择本地眼部图片并预览 | 同 M03 | `eye-upload` File | 产品描述未提眼部，但代码已实现 |
| M06 | 操作指引 OperationHint | 提示需上传三类照片后再诊断 | 纯文案 | 静态 | 位于诊断按钮上方 |
| M07 | 诊断触发 DiagnoseButton | 提交多模态数据并请求后端 | 点击「开始诊断」→ 按钮禁用 + 内联 spinner → POST 表单 | FormData 聚合 M02–M05 数据 | 无前置校验（图片可选上传） |
| M08 | 诊断结果区 ResultPanel | 展示结构化诊断报告 | 请求成功后 `.result-section.show` 淡入显示；失败显示错误块 | `DiagnoseResponse` JSON | 初始 `display:none` |
| M09 | 报告头 ReportHeader | 标题「中医诊断报告」+ 当前时间 | 纯展示 | `new Date()` | — |
| M10 | 证型 SyndromeBlock | 展示 `syndrome` | 纯展示 | `result.syndrome` | 空则隐藏 |
| M11 | 证候分析 AnalysisBlock | 展示 `analysis` | 纯展示 | `result.analysis` | — |
| M12 | 调理建议 SuggestionsBlock | 展示 `suggestions[]` 列表 | 纯展示 | `result.suggestions` | — |
| M13 | 方剂建议 PrescriptionsBlock | 展示 `prescriptions[]` 列表 | 纯展示 | `result.prescriptions` | — |
| M14 | 完整报告 FullReportBlock | 将 `diagnosis` 按 `\n\n` 分段渲染 | 纯展示 | `result.diagnosis` | 与结构化块重复展示 |
| M15 | 脉象分析 PulseBlock | 展示 `pulse_characteristics` | 纯展示 | `result.pulse_characteristics` | 仅 API 返回时展示，**无前端假数据** |
| M16 | 多模态分析 MultimodalBlocks | 面/舌/目诊 + 融合摘要 | 纯展示 | `face_analysis`, `tongue_analysis`, `eye_analysis`, `fusion_summary` | ✅ 已实现 |
| M17 | 报告脚注 ReportFooter | 参考来源 + 免责声明 + 上传状态 | 纯展示 | `result.source`, `result.disclaimer` | — |
| M18 | 错误提示 ErrorPanel | 网络/接口失败提示 | catch 后展示；**解析 API `detail`** | `error.message` | — |
| M19 | **百科检索 LibraryView** | 分类 pill、搜索框、结果卡片 | `searchLibrary()` → `POST /api/knowledge/search` | query, top_k | ✅ `#view-library` |
| M20 | **历史记录 HistoryView** | 保存/清空/回看 | `localStorage` `tcm_diagnosis_history` | 最近 50 条 | ✅ `#view-history` |
| M21 | **新建问诊** | 重置表单并回到诊断页 | `#new-consultation-btn` → `resetConsultationForm()` | — | ✅ |
| — | **摄像头采集 CameraCapture** | 实时预览/拍照 | **已实现**：`.camera-photo` + `#camera-modal` | `getUserMedia` | — |

---

## 3. 页面布局描述

### 3.1 整体布局

单页应用，**左侧 Sidebar + 主内容区三视图切换**（`showSection`：`diagnosis` | `library` | `history`）。

```
┌──────────┬────────────────────────────────────┐
│ Sidebar  │  Header（标题随视图变化）            │
│ 智能诊断  │  ─────────────────────────────────  │
│ 中药百科  │  #view-diagnosis | library | history│
│ 诊断历史  │                                     │
│ 新建问诊  │                                     │
└──────────┴────────────────────────────────────┘
```

- **Header**：顶部全宽
- **Metrics / Photos**：中部主内容，左右随 Grid 自适应
- **DiagnoseButton**：中下部居中
- **ResultPanel**：最底部，诊断成功后展开
- **Footer**：无独立 Footer 组件

### 3.2 响应式断点

| 断点 | 行为 |
|------|------|
| **PC**（>768px） | 指标 Grid `auto-fit minmax(220px)`；图片 Grid `minmax(320px)`，通常 2–3 列 |
| **平板**（≤768px） | 标题缩小；指标 2 列；图片 1 列；按钮 padding 缩小 |
| **手机**（≤480px） | 标题更小；指标 1 列；按钮进一步缩小 |

**待补充**：无独立平板横屏布局；无 sticky 诊断按钮。

---

## 4. 组件层级树

```
DiagnosisPage (frontend/index.html)
├── Container
│   ├── Header (M01)
│   │   ├── Title (h1)
│   │   └── Subtitle (p)
│   │
│   ├── MetricsSection (M02)
│   │   ├── SectionTitle
│   │   └── MetricsGrid
│   │       ├── MetricCard (心率)
│   │       │   ├── MetricValue #heart-rate
│   │       │   ├── MetricUnit
│   │       │   ├── MetricRange
│   │       │   └── MetricStatus #heart-rate-status
│   │       ├── MetricCard (脉搏) … #pulse
│   │       ├── MetricCard (收缩压) … #systolic
│   │       ├── MetricCard (舒张压) … #diastolic
│   │       ├── MetricCard (年龄)
│   │       │   └── NumberInput #age
│   │       └── MetricCard (性别)
│   │           └── Select #gender
│   │
│   ├── PhotoSection (M03–M05)
│   │   ├── SectionTitle
│   │   └── PhotosGrid
│   │       ├── PhotoCard (舌苔)
│   │       │   ├── PhotoPreview #tongue-preview
│   │       │   │   ├── UploadPlaceholder | ImagePreview | LoadingOverlay
│   │       │   └── FileInput #tongue-upload (hidden trigger)
│   │       ├── PhotoCard (面部) … #face-*
│   │       └── PhotoCard (眼部) … #eye-*
│   │
│   ├── DiagnoseSection (M06–M07)
│   │   ├── OperationHint
│   │   └── DiagnoseButton #diagnose-btn
│   │       ├── DiagnoseText #diagnose-text
│   │       └── LoadingSpinner #diagnose-loading
│   │
│   └── ResultSection #result-section (M08, 条件显示)
│       ├── SectionTitle
│       └── DiagnosisResult #diagnosis-result
│           └── DiagnosisReport
│               ├── ReportHeader (M09)
│               ├── SyndromeBlock (M10)
│               ├── AnalysisBlock (M11)
│               ├── SuggestionsBlock (M12)
│               ├── PrescriptionsBlock (M13)
│               ├── FullReportBlock (M14)
│               ├── PulseBlock (M15)
│               ├── EvidenceBlock (M16)
│               └── ReportFooter (M17)
│                   ├── SourceInfo
│                   └── ReportNote (disclaimer)
│
└── InlineScript (无独立组件文件)
    ├── generateMetrics()
    ├── getMetricStatus()
    ├── setupPhotoPreview()
    └── setupDiagnoseButton()
```

### 小程序对照结构（多页，供扩展参考）

```
MiniProgram
├── pages/index      → 首页入口 + 历史入口
├── pages/metrics    → 可编辑指标 + 随机生成
├── pages/upload     → 三图上传 + 删除/重传 + 拍摄建议
├── pages/result     → 诊断结果
└── pages/history    → 本地历史列表
```

---

## 5. 样式与主题信息

### 5.1 设计 Token（从 CSS 提取，当前未用 CSS Variables）

| Token | 值 | 用途 |
|-------|-----|------|
| `--bg`（隐含） | `#FAF9F6` | 页面背景 + 渐变纹理 SVG |
| `--card` | `#FFFFFF` | 卡片背景 |
| `--primary` | `#8B4513` | 主色：标题、按钮、强调边框 |
| `--primary-hover` | `#6B340B` | 按钮 hover |
| `--primary-light` | `#D2B48C` | 边框、分隔线 |
| `--header-bg` | `#F5F5DC` | Header 背景 |
| `--success` | `#2d5016` | 正常状态文字 |
| `--warning` | `#8B4513` | 警告状态 |
| `--danger` | `#8B0000` | 异常/错误 |
| `--text` | `#3A2718` | 正文 |
| `--text-muted` | `#5D4037` / `#6D4C41` | 次要文字 |
| `--border` | `#E8E5DE` | 卡片边框 |
| **字体** | `'Microsoft YaHei', 'SimSun', serif` | 全局 |
| **圆角** | 卡片 `15px`；按钮 `8–12px`；小元素 `4–10px` | — |
| **阴影** | `0 4px 20px rgba(139,69,19,0.08)` 等 | 卡片 elevation |
| **动画** | `fadeIn 0.5s`（结果区）；`spin 1s`（loading） | — |
| **Hover** | 卡片 `translateY(-2px)`；按钮 ripple 伪元素 | — |

### 5.2 主题支持

- **暗色模式**：不支持，无 `prefers-color-scheme`、无主题切换
- **多套主题**：无；全局 inline `<style>` 单主题

**待补充**：Design Token 应重构为 CSS Variables 或 Design System 以便 Stitch 生成组件库。

---

## 6. 数据流与状态管理

### 6.1 状态管理方式

原生 DOM + 内联 `<script>`，**无** Vuex/Pinia/Redux/useState。状态分散在：

- DOM 文本节点（指标数值）
- `<input>` / `<select>` 值（年龄、性别）
- `<input type="file">`.files（三张图）
- `#result-section` 的 class / `#result-panel` 可见性
- `localStorage['tcm_diagnosis_history']`（诊断历史，最多 50 条）
- `lastDiagnosisResult`（内存，供保存历史）

### 6.2 共享数据流

```
页面加载
  └─ generateMetrics() → 写入 DOM（心率/脉搏/血压）

用户操作
  ├─ 编辑 age / gender
  ├─ 选择 tongue/face/eye 文件 → FileReader → preview innerHTML
  └─ 点击诊断
       └─ 从 DOM + files 组装 FormData
            └─ POST /api/diagnose
                 └─ JSON → 拼接 HTML 字符串 → #diagnosis-result.innerHTML
```

### 6.3 主要 API

| 接口 | 方法 | 用途 | Web 前端 |
|------|------|------|----------|
| `/api/diagnose` | POST multipart | 多模态诊断 | ✅ 已用 |
| `/api/diagnose/json` | POST JSON+base64 | 小程序诊断 | ❌ Web 未用 |
| `/api/knowledge/search` | POST `{query, top_k}` | 公开知识检索 | ✅ `#view-library` |
| `/api/admin/*` | — | 管理端 | ❌ 非 C 端 |

### 6.4 请求体字段（FormData）

```
heart_rate, pulse, systolic, diastolic, age, gender
tongue_image?, face_image?, eye_image?  (File)
```

### 6.5 响应字段（DiagnoseResponse）使用矩阵

| 字段 | UI 使用 |
|------|---------|
| `syndrome`, `analysis`, `suggestions`, `prescriptions` | ✅ 结构化块 |
| `diagnosis`, `source`, `disclaimer` | ✅ 完整报告/脚注 |
| `pulse_characteristics` | ✅（有则展示） |
| `face_analysis`, `tongue_analysis`, `eye_analysis`, `fusion_summary` | ✅ 独立块展示 |

**待补充**：全局 State 对象（如 `appState = { metrics, images, result, loading, error }`）供 Stitch 重构为 React/Vue 组件。

---

## 7. 关键交互细节

| 交互 | 当前实现 | 缺失/待补充 |
|------|----------|-------------|
| **图片采集** | 点击预览区 → 系统文件选择器；支持 JPG/PNG | 无摄像头 `getUserMedia`；无拍照倒计时；无 Tab 切换舌/面 |
| **图片加载** | FileReader 期间显示 `.loading-overlay` + spinner | 无上传进度条；无图片尺寸/格式校验提示 |
| **图片管理** | 仅覆盖重选 | 无删除、无放大预览（小程序有 delete/reupload/preview） |
| **指标输入** | 可编辑；页面加载 + 「随机采样」调 `/api/health-metrics` | 无体温 |
| **结果展示** | 成功后 `scrollIntoView`；含多模态分析块 | 无复制报告、无折叠 |
| **错误提示** | 诊断/检索均解析 API `detail` | 无 Toast |
| **脉象兜底** | 仅展示 API 返回的 `pulse_characteristics` | — |
| **历史记录** | localStorage + `#view-history` | 无服务端同步 |
| **知识检索** | `#view-library` 完整 UI | — |
| **新建问诊** | 重置指标/图片/结果 | — |

---

## 8. Stitch 重构建议

1. **拆分目标**：当前为 **1 个 monolithic 文件**（~1012 行），建议拆分为：
   - `Layout` / `Sidebar`
   - `MetricsGrid` / `ImageUploader` × 3
   - `DiagnoseCTA` / `DiagnosisReport`
   - `HerbalLibrary`（百科，**已有**）
   - `HistoryPanel`（**已有**）

2. **仍待实现**：摄像头、服务端历史、Toast、复制报告、Design Token 变量化。

3. **后端已就绪、前端未接**：无（C 端公开 API 均已接线）。

*文档最后更新：2026-06-08*

---

## 9. 相关文件索引

| 文件 | 说明 |
|------|------|
| `frontend/index.html` | Web C 端主前端（本文分析对象） |
| `wechat-miniprogram/` | 小程序前端（多页流程参考） |
| `tcm_ai/api/routes/diagnose.py` | 诊断 API |
| `tcm_ai/api/schemas/diagnose.py` | `DiagnoseResponse` 结构 |
| `tcm_ai/api/routes/knowledge.py` | 公开知识检索 API |
| `admin/index.html` | 管理端 UI（非 C 端） |

管理端 UI 重构说明书见 **[docs/ADMIN_UI_REFACTOR_SPEC.md](docs/ADMIN_UI_REFACTOR_SPEC.md)**。

---

*文档生成日期：2026-06-08*
