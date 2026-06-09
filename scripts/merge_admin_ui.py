# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

#!/usr/bin/env python3
"""Merge Stitch admin shell with existing admin panel logic."""
from pathlib import Path
import re

project = Path(__file__).resolve().parents[1]
old = (project / "admin/index.html").read_text(encoding="utf-8")
stitch_head = Path("/Users/macmini/Downloads/stitch_ai/_1/code.html").read_text(encoding="utf-8")

head_match = re.search(r"(<!DOCTYPE html>.*?</head>)", stitch_head, re.S)
head = head_match.group(1)
head = head.replace("<title>ZenPulse AI - 系统概览</title>", "<title>中医知识库 · 管理端</title>")

body_match = re.search(r"(<div id=\"main-content\".*?</div>\s*</div>)\s*<script>", old, re.S)
panels_block = body_match.group(1)
script_match = re.search(r"(<script>.*?</script>)", old, re.S)
script = script_match.group(1)

compat_css = """
    .panel { display: none; }
    .panel.active { display: block; }
    .status { padding: 10px 12px; border-radius: 8px; font-size: 0.9rem; margin-top: 10px; }
    .status.ok { background: #e8f5e9; color: #2d5016; }
    .status.err { background: #ffebee; color: #b71c1c; }
    .chunk { border: 1px solid #dac2b6; border-radius: 8px; padding: 12px; margin-bottom: 10px; background: #fcfcfb; }
    .chunk-meta { font-size: 0.8rem; color: #54433a; margin-bottom: 6px; }
    .answer { white-space: pre-wrap; background: #fff8e1; border-left: 4px solid #d2b48c; padding: 14px; border-radius: 8px; }
    .hint { font-size: 0.82rem; color: #54433a; margin-top: 6px; }
    .btn-primary, .btn-secondary, .btn-danger { border: none; border-radius: 8px; padding: 10px 16px; cursor: pointer; font-size: 0.95rem; }
    .btn-primary { background: #8b4513; color: #fff; }
    .btn-secondary { background: #efebe9; color: #3a2718; }
    .btn-danger { background: #b71c1c; color: #fff; }
    .card { background: #fff; border: 1px solid #dac2b6; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
    .card h2 { font-size: 1.1rem; color: #8b4513; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid #dac2b6; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
    .row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    label { display: block; font-size: 0.85rem; color: #54433a; margin-bottom: 4px; }
    input, select, textarea { width: 100%; padding: 10px 12px; border: 1px solid #dac2b6; border-radius: 8px; font-size: 0.95rem; background: #fff; }
    textarea { min-height: 120px; resize: vertical; }
    .dash-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
    .dash-tile { border: 1px solid #dac2b6; border-radius: 10px; padding: 14px; background: #fcfcfb; }
    .dash-tile h3 { font-size: 0.9rem; color: #8b4513; margin-bottom: 6px; }
    .dash-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
    .progress-wrap { margin-top: 12px; background: #efebe9; border-radius: 8px; height: 22px; overflow: hidden; border: 1px solid #dac2b6; }
    .progress-bar { height: 100%; background: linear-gradient(90deg, #d2b48c, #8b4513); width: 0%; transition: width 0.35s ease; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 0.75rem; font-weight: 600; }
    .nav-hint { font-size: 0.88rem; color: #54433a; margin-bottom: 12px; padding: 10px 14px; background: #fff8e1; border-radius: 8px; border: 1px solid #dac2b6; }
    .tab.active { background: #8b4513 !important; color: #fff !important; }
    #sidebar-nav .tab.active { background: #8b4513 !important; color: #fff !important; font-weight: 700; }
"""

head = head.replace("</style>", compat_css + "\n  </style>", 1)

panels_clean = panels_block
panels_clean = panels_clean.replace('<div id="main-content" class="hidden">', '<div id="main-content" class="hidden">', 1)
panels_clean = re.sub(r'<header>.*?</header>\s*', '', panels_clean, count=1, flags=re.S)
panels_clean = panels_clean.replace('<div class="tabs">', '<div class="tabs hidden">', 1)

sidebar = """
<aside class="hidden lg:flex flex-col h-screen fixed left-0 top-0 p-stack-md w-64 bg-surface-container-low border-r border-outline-variant pt-24 z-40">
  <div class="mb-8 px-4">
    <h2 class="font-title-sm text-title-sm text-primary">中医知识库管理端</h2>
    <p class="font-label-caps text-label-caps text-secondary">Admin Dashboard</p>
  </div>
  <nav class="flex-1 flex flex-col gap-1 overflow-y-auto custom-scrollbar" id="sidebar-nav">
    <button type="button" class="tab flex items-center gap-3 rounded-full px-4 py-2 font-label-caps text-label-caps text-secondary hover:bg-secondary-container transition-all active" data-tab="dashboard"><span class="material-symbols-outlined">dashboard</span>概览</button>
    <button type="button" class="tab flex items-center gap-3 rounded-full px-4 py-2 font-label-caps text-label-caps text-secondary hover:bg-secondary-container transition-all" data-tab="knowledge"><span class="material-symbols-outlined">database</span>知识库</button>
    <button type="button" class="tab flex items-center gap-3 rounded-full px-4 py-2 font-label-caps text-label-caps text-secondary hover:bg-secondary-container transition-all" data-tab="embedding"><span class="material-symbols-outlined">view_in_ar</span>Embedding</button>
    <button type="button" class="tab flex items-center gap-3 rounded-full px-4 py-2 font-label-caps text-label-caps text-secondary hover:bg-secondary-container transition-all" data-tab="llm"><span class="material-symbols-outlined">psychology</span>LLM</button>
    <button type="button" class="tab flex items-center gap-3 rounded-full px-4 py-2 font-label-caps text-label-caps text-secondary hover:bg-secondary-container transition-all" data-tab="rerank"><span class="material-symbols-outlined">sort</span>Rerank</button>
    <button type="button" class="tab flex items-center gap-3 rounded-full px-4 py-2 font-label-caps text-label-caps text-secondary hover:bg-secondary-container transition-all" data-tab="rag"><span class="material-symbols-outlined">bug_report</span>RAG 检索</button>
    <button type="button" class="tab flex items-center gap-3 rounded-full px-4 py-2 font-label-caps text-label-caps text-secondary hover:bg-secondary-container transition-all" data-tab="system"><span class="material-symbols-outlined">settings_suggest</span>系统</button>
  </nav>
</aside>
"""

topnav = """
<nav class="fixed top-0 w-full z-50 flex justify-between items-center px-margin-page py-base bg-surface/95 backdrop-blur border-b border-outline-variant">
  <div class="flex items-center gap-8 lg:pl-64">
    <span class="font-headline-md text-headline-md font-bold text-primary">ZenPulse AI · 管理端</span>
  </div>
  <div class="flex items-center gap-3 flex-wrap justify-end max-w-2xl">
    <input id="api-key-input" type="password" placeholder="Admin API Key" class="!w-auto flex-1 min-w-[180px] text-sm py-2 px-3 border border-outline-variant rounded-lg">
    <button class="btn-primary text-sm py-2 px-4" id="save-key-btn">保存</button>
    <button class="btn-secondary text-sm py-2 px-4" id="test-key-btn">连接</button>
    <span id="auth-status" class="hint text-xs"></span>
  </div>
</nav>
"""

mobile_tabs = """
<div class="lg:hidden flex flex-wrap gap-2 mb-4">
  <button type="button" class="tab btn-secondary text-xs py-2 px-3 active" data-tab="dashboard">概览</button>
  <button type="button" class="tab btn-secondary text-xs py-2 px-3" data-tab="knowledge">知识库</button>
  <button type="button" class="tab btn-secondary text-xs py-2 px-3" data-tab="embedding">Emb</button>
  <button type="button" class="tab btn-secondary text-xs py-2 px-3" data-tab="llm">LLM</button>
  <button type="button" class="tab btn-secondary text-xs py-2 px-3" data-tab="rerank">Rerank</button>
  <button type="button" class="tab btn-secondary text-xs py-2 px-3" data-tab="rag">RAG</button>
  <button type="button" class="tab btn-secondary text-xs py-2 px-3" data-tab="system">系统</button>
</div>
"""

switch_tab_fn = """
    function switchTab(tabName) {
      document.querySelectorAll('.tab').forEach(t => {
        const on = t.dataset.tab === tabName;
        t.classList.toggle('active', on);
      });
      document.querySelectorAll('.panel').forEach(p => {
        p.classList.toggle('active', p.id === 'panel-' + tabName);
      });
    }
"""

script = re.sub(
    r"function switchTab\(tabName\) \{.*?\n    \}",
    switch_tab_fn.strip(),
    script,
    count=1,
    flags=re.S,
)

html_body = (
    '<body class="font-body-md text-body-md selection:bg-primary-fixed bg-surface">\n'
    + topnav
    + sidebar
    + '<main class="lg:ml-64 pt-24 pb-16 px-margin-page min-h-screen">\n'
    + '<div class="max-w-container-max mx-auto">\n'
    + mobile_tabs
    + '<p class="nav-hint">数据导入 · 模型 API 配置 · RAG 调试 · 索引运维 · 案例管理</p>\n'
    + panels_clean
    + "\n</div>\n</main>\n"
    + script
    + "\n</body></html>"
)

out = head + "\n" + html_body
(project / "admin/index.html").write_text(out, encoding="utf-8")
print(f"Wrote admin/index.html ({len(out)} bytes)")
