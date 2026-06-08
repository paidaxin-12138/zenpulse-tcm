# 中医 AI 诊断 · 微信小程序 Apple 风格 UI 重构说明书

> 供 **Stitch / Figma / 设计转代码** 使用。  
> 代码路径：`wechat-miniprogram/`  
> **硬性约束：只改视觉与布局，功能、页面路由、JS 逻辑、API 调用一律不变。**

**最后同步**：2026-06-08

---

## 0. Stitch 一键提示词（复制整段）

```
你是一名熟悉 Apple Human Interface Guidelines（iOS 17/18）的微信小程序 UI 工程师。请对「中医 AI 智能诊断」小程序做纯视觉重构，输出 WXML + WXSS（rpx），参照 iOS 系统 App（健康、设置、备忘录）的质感。

【硬性约束 — 功能零变更】
- 不得增删页面、不得改 TabBar 结构、不得改 API、不得改业务流程
- 必须保留下列 bindtap / bindinput / open-type 与现有 .js 方法一一对应（仅改 class 名与布局，handler 名不变）
- 不得移除：微信登录、云端历史同步、eventChannel 传参、本地 storage 备份

【页面与路由 — 保持不变】
TabBar：首页 pages/index/index · 我的 pages/profile/profile
流程页：pages/metrics → pages/upload → pages/result
子页：pages/history（从 profile 进入）

【Apple 设计系统 — Design Tokens】
色彩（Light Mode 为主，可选 Dark）：
- systemGroupedBackground: #F2F2F7
- secondarySystemGroupedBackground: #FFFFFF
- label: #000000 · secondaryLabel: #3C3C43 60% · tertiaryLabel: #3C3C43 30%
- separator: #C6C6C8 · opaqueSeparator: #E5E5EA
- systemBlue (主操作/链接): #007AFF
- systemGreen: #34C759 · systemOrange: #FF9500 · systemRed: #FF3B30
- fill: #787880 20%（输入框/占位背景）
- 禁用暖棕中医色；全面采用 iOS 中性灰 + 系统蓝 accent

字体（PingFang SC，模拟 SF Pro）：
- largeTitle: 68rpx/800 · title1: 56rpx/700 · title2: 44rpx/700
- headline: 34rpx/600 · body: 34rpx/400 · callout: 32rpx/400
- subhead: 30rpx/400 · footnote: 26rpx/400 · caption1: 24rpx/400

圆角与间距：
- groupedSection 外 margin: 32rpx 左右 · section 内 padding: 0
- cell 高度 min 88rpx · 圆角 20rpx（分组列表整体圆角，非单 cell）
- 主按钮：高度 96rpx · 圆角 24rpx · 全宽 · systemBlue 填充
- 次要按钮：透明底 + systemBlue 文字，或 gray fill
- 安全区：padding-bottom: env(safe-area-inset-bottom)

布局范式（iOS Grouped List）：
- 大标题区：页面顶部 Large Title + 可选副标题 footnote
- 内容区：白色圆角分组卡片，组间 16rpx 间距，组内 hairline 分隔
- 列表行：左 icon（24×24 线性 SVG/PNG）+ 主标题 + 可选副标题 + 右 chevron ›
- 表单：inset grouped 输入行，右侧数值/单位，placeholder 用 tertiaryLabel
- 禁止 Emoji 装饰；全部换线性 icon（heart.pulse, camera, doc.text 等 SF Symbols 风格）

阴影：默认无阴影或极轻 0 1rpx 3rpx rgba(0,0,0,0.06)；不用厚重 brown shadow
动效：按钮 active opacity 0.6；页面切换依赖微信原生；可选 200ms ease

【全局 app.wxss 重构】
- page 背景 #F2F2F7
- 统一 .ios-group / .ios-cell / .ios-large-title / .ios-btn-primary / .ios-btn-secondary
- navigationBar：背景 #F2F2F7，文字 #000（或保持 #8B4513 仅 nav 条可保留品牌，内容区必须 Apple 风）

【逐页规格 — 功能绑定不可改】

## P1 首页 index.wxml
保留 handler：
- startDiagnosis → 跳转 /pages/metrics/metrics
- goToHistory → switchTab /pages/profile/profile
- goToAbout → wx.showModal 关于（仍 Modal，可美化 copy）
布局：
- Large Title「中医智能诊断」+ footnote 副标题
- Group 1：6 项能力 grid（2×3）或 inset list，线性 icon + 单行标题（健康指标/舌象/面部/眼部/脉象/辨证）
- Group 2：主 CTA「开始诊断」ios-btn-primary
- Group 3：次要操作 list —「历史记录」「关于我们」chevron 行
- Footer：caption 版权 + 版本号
去掉所有 Emoji

## P2 健康指标 metrics.wxml
保留 handler：
- onHeartRateInput / onPulseInput / onSystolicInput / onDiastolicInput / onAgeInput
- onGenderSelect data-gender="男|女"
- getRandomMetrics · nextStep · backToHome
布局：
- 顶部 Step 指示：1 体征 · 2 拍照 · 3 结果（纯展示）
- Group「生命体征」：心率/脉搏/血压(收缩/舒张)/年龄 — 每行 label + input + unit
- Group「基本信息」：性别 — iOS Segmented Control 双段（男|女），选中 systemBlue
- 底部固定区：Primary「下一步」· Secondary「随机生成」· Tertiary「返回首页」
- Group「提示」：footnote 多行说明（原 tip-section 文案保留）

## P3 图片上传 upload.wxml
保留 handler：
- chooseTongueImage / chooseFaceImage / chooseEyeImage
- previewImage · deleteImage data-type · startDiagnosis · backToMetrics · backToHome
布局：
- Step 指示 step 2 高亮
- 三组 Image Capture Card：标题 + 说明 footnote + 占位（虚线圆角矩形 + camera icon）或预览图 + 操作行「预览|删除|重拍」
- Primary「开始诊断」· Secondary 返回
- Group 拍摄建议 footnote

## P4 诊断结果 result.wxml
保留 handler：shareResult · newDiagnosis · backToHome · onShareAppMessage
数据字段展示（wx:if 逻辑保留）：
syndrome, analysis, suggestions[], diagnosis, pulse_characteristics, source, disclaimer
布局：
- 顶部 Hero：证型 Large Title + 时间 caption
- 若有 diagnosis_mode=rule/metrics：systemOrange inset banner（文案不变）
- 多个 Group 卡片：证候分析 / 调理建议（bullet list）/ 诊断结论 / 脉象分析（key-value rows）/ 诊断依据
- 底部 Group「重要提示」红色 footnote 风格
- 固定底栏：Primary 分享 · Secondary 重新诊断 · Tertiary 返回首页

## P5 个人中心 profile.wxml
保留 handler：
- onLoginTap · onLogoutTap · onChooseAvatar · onNicknameBlur
- showDiagnosisHistory · showHelp · showAbout · showHistoryDetail · startNewDiagnosis
数据：userInfo, isLoggedIn, loginLoading, diagnosisHistory
布局：
- Group「账户」：圆形头像 120rpx（chooseAvatar button）+ 昵称 input type=nickname + 状态 caption
- 未登录：Primary「微信登录」loading 态
- 已登录：destructive text「退出登录」
- Group「功能」：诊断历史 / 帮助与反馈 / 关于我们 — chevron list（去掉设置项若 js 无独立页则合并到关于）
- Group「最近记录」：history-item 或 empty state
- Primary「开始新诊断」

## P6 历史 history.wxml
保留 handler：showHistoryDetail · clearHistory · startNewDiagnosis · formatDate
布局：
- Large Title「诊断历史」
- Grouped list：每行 日期 + 状态 badge（已完成 systemGreen pill）+ 摘要 2 行
- Empty：居中 icon + 文案 + Primary 开始新诊断
- 底部 destructive「清空历史记录」（有数据时显示）

【TabBar — 仅视觉】
- 背景 #FBFBFD 毛玻璃感（可用半透明白 + border-top #E5E5EA）
- 选中 #007AFF · 未选 #8E8E93
- 建议使用 iconPath（首页 house / 我的 person）+ 文案「首页」「我的」

【组件拆分建议】
components/ios-large-title/
components/ios-group/
components/ios-cell/
components/ios-segment/
components/ios-step-bar/
components/ios-primary-button/
components/image-capture-card/
components/report-section/

【禁止事项】
- 不要新增百科 Tab 或任何 Web 独有功能
- 不要改 utils/api.js、utils/auth.js 接口签名
- 不要改 eventChannel 事件名 passMetrics / passDiagnosisResult
- 不要用暖棕 #8B4513 作为主色（仅 navigationBar 可保留）

【交付物】
1. 每页完整 WXML + WXSS
2. styles/tokens.wxss + app.wxss 全局样式
3. app.json window/tabBar 颜色更新建议
4. icon 资源清单（PNG 48×48 @2x 线性风格）
5. 变更对照表：旧 class → 新 class，bind 事件零变更确认清单

【参考路径】
wechat-miniprogram/pages/*/*
wechat-miniprogram/utils/auth.js（登录逻辑）
docs/MINIPROGRAM_UI_REFACTOR_SPEC.md（API 对照）
```

---

## 1. 重构原则

| 原则 | 说明 |
|------|------|
| **功能冻结** | 6 个页面、2 Tab、诊断三步流、微信登录、历史上云 — 全部保留 |
| **只改 UI** | WXML 结构、WXSS、静态资源；`.js` 除 `data` 绑定路径外不改动 |
| **Apple HIG** | Grouped List、Large Title、系统色、线性图标、大留白 |
| **去 Emoji** | 全部替换为 SF Symbols 风格 PNG/SVG icon |

---

## 2. 设计 Token（`styles/tokens.wxss`）

```css
/* Apple Light */
--ios-bg-grouped: #F2F2F7;
--ios-bg-cell: #FFFFFF;
--ios-label: #000000;
--ios-label-secondary: rgba(60, 60, 67, 0.6);
--ios-label-tertiary: rgba(60, 60, 67, 0.3);
--ios-separator: rgba(60, 60, 67, 0.12);
--ios-blue: #007AFF;
--ios-green: #34C759;
--ios-orange: #FF9500;
--ios-red: #FF3B30;
--ios-fill: rgba(120, 120, 128, 0.2);
--ios-radius-group: 20rpx;
--ios-radius-button: 24rpx;
--ios-spacing-page: 32rpx;
--ios-cell-min-height: 88rpx;
```

### Dark Mode（可选第二主题）

```css
--ios-bg-grouped: #000000;
--ios-bg-cell: #1C1C1E;
--ios-label: #FFFFFF;
--ios-separator: rgba(84, 84, 88, 0.65);
```

---

## 3. 功能绑定清单（不可改）

### 3.1 首页 `index.js`

| 事件 | 方法 | 行为 |
|------|------|------|
| bindtap | `startDiagnosis` | navigateTo `/pages/metrics/metrics` |
| bindtap | `goToHistory` | switchTab `/pages/profile/profile` |
| bindtap | `goToAbout` | showModal 关于我们 |
| 生命周期 | `onPullDownRefresh` | 刷新 toast |

### 3.2 指标页 `metrics.js`

| 事件 | 方法 |
|------|------|
| bindinput | `onHeartRateInput` / `onPulseInput` / `onSystolicInput` / `onDiastolicInput` / `onAgeInput` |
| bindtap data-gender | `onGenderSelect` |
| bindtap | `getRandomMetrics` → GET `/health-metrics` |
| bindtap | `nextStep` → validate + navigateTo upload + eventChannel `passMetrics` |
| bindtap | `backToHome` |

### 3.3 上传页 `upload.js`

| 事件 | 方法 |
|------|------|
| bindtap | `chooseTongueImage` / `chooseFaceImage` / `chooseEyeImage` |
| bindtap | `previewImage` / `deleteImage` |
| bindtap | `startDiagnosis` → POST `/diagnose/json` |
| bindtap | `backToMetrics` / `backToHome` |

### 3.4 结果页 `result.js`

| 事件 | 方法 |
|------|------|
| eventChannel | `passDiagnosisResult` |
| 自动 | `saveDiagnosisHistory` → local + POST `/diagnosis/history` |
| bindtap | `shareResult` / `newDiagnosis` / `backToHome` |

### 3.5 个人中心 `profile.js`

| 事件 | 方法 |
|------|------|
| bindtap | `onLoginTap` / `onLogoutTap` |
| open-type chooseAvatar | `onChooseAvatar` |
| bindblur nickname | `onNicknameBlur` → PUT `/wx/profile` |
| bindtap | `showDiagnosisHistory` / `showHelp` / `showAbout` |
| bindtap | `showHistoryDetail` / `startNewDiagnosis` |
| onShow | `loadDiagnosisHistory` → GET `/diagnosis/history` |

### 3.6 历史页 `history.js`

| 事件 | 方法 |
|------|------|
| bindtap | `showHistoryDetail` / `clearHistory` / `startNewDiagnosis` |
| onShow | `loadDiagnosisHistory` |

### 3.7 全局 `app.js`

| 行为 | 说明 |
|------|------|
| `ensureLogin()` | 启动静默微信登录 |
| `baseUrl` | `http://localhost:8000/api` |
| `addDiagnosisHistory` | 本地 storage |

---

## 4. 逐页线框（Apple Grouped）

### P1 首页

```
┌─────────────────────────────┐
│  Large Title                │
│  中医智能诊断                │
│  footnote: AI 中医助手       │
├─────────────────────────────┤
│ ┌─ 系统能力 ─────────────┐  │
│ │ [icon] 健康指标  [icon] │  │
│ │ 舌象    面部    眼部    │  │
│ │ 脉象    辨证            │  │
│ └─────────────────────────┘  │
│ ┌─────────────────────────┐  │
│ │    开始诊断 (Blue)       │  │
│ └─────────────────────────┘  │
│ ┌─────────────────────────┐  │
│ │ 历史记录            ›   │  │
│ │ 关于我们            ›   │  │
│ └─────────────────────────┘  │
│ caption © 2026 · v1.1.0     │
└─────────────────────────────┘
```

### P2 指标页

```
Large Title: 健康指标
Step: ● 体征  ○ 拍照  ○ 结果

┌ 生命体征 ─────────────┐
│ 心率          [___] 次/分│
│ 脉搏          [___] 次/分│
│ 收缩压/舒张压  [__]/[__] │
│ 年龄          [___] 岁   │
└────────────────────────┘
┌ 性别 ─────────────────┐
│  [  男  |  女  ] segment │
└────────────────────────┘
[ 随机生成 ]  [ 下一步 → ]
footnote 提示组
```

### P5 个人中心

```
Large Title: 我的

┌ 账户 ─────────────────┐
│ (avatar)  昵称         │
│           已登录/未登录 │
│ [ 微信登录 ]           │
└────────────────────────┘
┌ ──────────────────────┐
│ 诊断历史            › │
│ 帮助与反馈          › │
│ 关于我们            › │
└────────────────────────┘
┌ 最近记录 ─────────────┐
│ 2026-06-08  已完成    │
│ 气虚血弱…             │
└────────────────────────┘
```

---

## 5. TabBar & NavigationBar

```json
{
  "window": {
    "navigationBarBackgroundColor": "#F2F2F7",
    "navigationBarTitleText": "",
    "navigationBarTextStyle": "black",
    "backgroundColor": "#F2F2F7"
  },
  "tabBar": {
    "color": "#8E8E93",
    "selectedColor": "#007AFF",
    "backgroundColor": "#F9F9F9",
    "borderStyle": "white",
    "list": [
      { "pagePath": "pages/index/index", "text": "首页", "iconPath": "...", "selectedIconPath": "..." },
      { "pagePath": "pages/profile/profile", "text": "我的", "iconPath": "...", "selectedIconPath": "..." }
    ]
  }
}
```

各页 `navigationStyle` 建议：`default`；Large Title 在页面内自绘（微信不支持原生 large title，用 WXML 模拟）。

---

## 6. Icon 清单（线性 48×48）

| 用途 | 建议 SF Symbol 名 |
|------|------------------|
| 健康指标 | heart.text.square |
| 舌象 | mouth |
| 面部 | face.smiling |
| 眼部 | eye |
| 脉象 | waveform.path.ecg |
| 辨证 | doc.text.magnifyingglass |
| 相机 | camera |
| 历史 | clock.arrow.circlepath |
| 关于 | info.circle |
| 分享 | square.and.arrow.up |
| Chevron | chevron.right |

---

## 7. Stitch 分步生成顺序

1. **全局**：`tokens.wxss` + `app.wxss` + `app.json` 颜色
2. **首页 + TabBar icon**
3. **metrics + upload**（步骤条组件）
4. **result**（报告分组卡片）
5. **profile + history**（账户 + grouped list）

每步交付后对照 **§3 功能绑定清单** 逐项勾选。

---

## 8. 验收标准

- [ ] 全部 bind 事件名与现网 `.js` 一致
- [ ] 诊断全流程可走通：首页 → 指标 → 上传 → 结果 → 历史
- [ ] 微信登录 / 退出 / 头像昵称 / 云端历史同步正常
- [ ] 无 Emoji；主色 systemBlue；背景 grouped gray
- [ ] 视觉接近 iOS 设置/健康 App（分组圆角列表 + 大标题）

---

*文档路径：`docs/MINIPROGRAM_APPLE_UI_SPEC.md`*
