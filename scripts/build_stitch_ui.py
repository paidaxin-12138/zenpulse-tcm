# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

#!/usr/bin/env python3
"""Build admin/index.html from Stitch source pages + admin/app.js."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STITCH = Path("/Users/macmini/Downloads/stitch_ai")
STITCH_PATIENTS = STITCH / "ai_2"
OUT = ROOT / "admin" / "index.html"


def read(name: str) -> str:
    return (STITCH / name / "code.html").read_text(encoding="utf-8")


def read_patients() -> str:
    return (STITCH_PATIENTS / "code.html").read_text(encoding="utf-8")


def extract_head(html: str) -> str:
    m = re.search(r"(<!DOCTYPE html>.*?</head>)", html, re.S | re.I)
    head = m.group(1)
    return head.replace("<title>ZenPulse AI - 系统概览</title>", "<title>中医知识库 · 管理端</title>")


def extract_main_inner(html: str) -> str:
    m = re.search(r"<main[^>]*>(.*)</main>", html, re.S | re.I)
    if not m:
        return ""
    inner = m.group(1)
    # drop outer max-w wrapper if present — keep full inner for fidelity
    return inner.strip()


def patch_dashboard(html: str) -> str:
    html = re.sub(
        r"<!-- Top Level Metrics \(Tiles\) -->.*?<!-- Grid Layout for Detailed Info -->",
        '<!-- Top Level Metrics (Tiles) -->\n<section id="dashboard-content" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-gutter"></section>\n<!-- Grid Layout for Detailed Info -->',
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r"<tbody class=\"divide-y divide-outline-variant\">.*?</tbody>",
        '<tbody id="provider-status-body" class="divide-y divide-outline-variant"></tbody>',
        html,
        count=1,
        flags=re.S,
    )
    # remove duplicate inline api key form — use top bar
    html = re.sub(
        r"<form class=\"space-y-4\">.*?</form>",
        '<p class="text-secondary font-body-sm">请在页面右上角输入 Admin Key 并点击「连接」。</p>',
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'最后更新: [\d:]+',
        '最后更新: <span id="dashboard-updated">--</span>',
        html,
        count=1,
    )
    return html


def patch_knowledge(html: str) -> str:
    html = re.sub(
        r"<span class=\"font-display-lg text-display-lg text-primary\">12,840</span>",
        '<span id="kn-metric-docs" class="font-display-lg text-display-lg text-primary">—</span>',
        html,
        count=1,
    )
    html = re.sub(
        r"<span class=\"font-display-lg text-display-lg text-on-surface\">342</span>\s*<div class=\"mt-auto pt-4 flex items-center text-secondary\">\s*<span class=\"text-xs font-label-caps\">实时同步中</span>",
        '<span id="kn-metric-cases" class="font-display-lg text-display-lg text-on-surface">—</span>\n<div class="mt-auto pt-4 flex items-center text-secondary">\n<span id="kn-metric-cases-sub" class="text-xs font-label-caps">加载中…</span>',
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r"<span class=\"font-display-lg text-display-lg text-on-surface\">4\.2 GB</span>",
        '<span id="kn-metric-storage" class="font-display-lg text-display-lg text-on-surface">—</span>',
        html,
        count=1,
    )
    html = re.sub(
        r"<span class=\"font-display-lg text-display-lg text-on-surface\">128</span>\s*<div class=\"mt-auto pt-4 flex items-center text-tertiary\">",
        '<span id="kn-metric-index" class="font-display-lg text-display-lg text-on-surface">—</span>\n<div class="mt-auto pt-4 flex items-center text-tertiary">',
        html,
        count=1,
        flags=re.S,
    )
    html = html.replace(
        '<button class="border border-outline-variant text-primary px-stack-md py-2 rounded-lg font-label-caps text-label-caps flex items-center gap-2 hover:bg-surface-container transition-colors">\n<span class="material-symbols-outlined text-[18px]">sync</span> 同步索引\n                    </button>',
        '<button type="button" id="knowledge-sync-index-btn" class="border border-outline-variant text-primary px-stack-md py-2 rounded-lg font-label-caps text-label-caps flex items-center gap-2 hover:bg-surface-container transition-colors"><span class="material-symbols-outlined text-[18px]">sync</span> 同步索引</button>',
        1,
    )
    html = html.replace(
        '<button class="bg-primary text-on-primary px-stack-lg py-2 rounded-lg font-label-caps text-label-caps flex items-center gap-2 hover:opacity-90 transition-opacity">\n<span class="material-symbols-outlined text-[18px]">upload_file</span> 批量导入\n                    </button>',
        '<button type="button" id="knowledge-goto-import-btn" class="bg-primary text-on-primary px-stack-lg py-2 rounded-lg font-label-caps text-label-caps flex items-center gap-2 hover:opacity-90 transition-opacity"><span class="material-symbols-outlined text-[18px]">upload_file</span> 批量导入</button>',
        1,
    )
    html = re.sub(
        r"<!-- Tabs Section -->.*?<!-- Management Section Lower Grid -->",
        '''<!-- Tabs Section -->
<div id="knowledge-tabs" class="flex items-center gap-2 bg-secondary-container p-1 rounded-lg w-fit mb-stack-md">
<button type="button" data-knowledge-tab="docs" class="knowledge-tab active bg-primary text-on-primary px-stack-lg py-2 rounded-lg font-label-caps text-label-caps">知识文档列表</button>
<button type="button" data-knowledge-tab="cases" class="knowledge-tab text-secondary px-stack-lg py-2 rounded-lg font-label-caps text-label-caps hover:bg-surface-variant transition-colors">临床案例管理</button>
<button type="button" data-knowledge-tab="index" class="knowledge-tab text-secondary px-stack-lg py-2 rounded-lg font-label-caps text-label-caps hover:bg-surface-variant transition-colors">索引状态分析</button>
</div>
<!-- Tab: 知识文档 -->
<div id="knowledge-tab-docs" class="knowledge-tab-panel active">
<div class="bg-surface border border-outline-variant rounded-lg overflow-hidden">
<div class="p-stack-md border-b border-outline-variant bg-surface-container-low flex justify-between items-center flex-wrap gap-3">
<div class="relative w-72">
<span class="material-symbols-outlined absolute left-3 top-2.5 text-secondary text-lg">search</span>
<input id="knowledge-doc-search" class="w-full bg-surface border border-outline-variant rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-primary" placeholder="搜索文件名、类型或来源..." type="text"/>
</div>
<div class="flex items-center gap-base">
<span class="text-sm text-secondary">分类:</span>
<select id="knowledge-doc-filter" class="bg-surface border border-outline-variant rounded-lg px-2 py-1 text-xs font-label-caps text-secondary">
<option value="">全部分类</option>
</select>
</div>
</div>
<table class="w-full text-left border-collapse">
<thead class="bg-surface-container-low">
<tr>
<th class="px-stack-md py-4 font-label-caps text-label-caps text-secondary border-b border-outline-variant">文件名</th>
<th class="px-stack-md py-4 font-label-caps text-label-caps text-secondary border-b border-outline-variant">大小</th>
<th class="px-stack-md py-4 font-label-caps text-label-caps text-secondary border-b border-outline-variant">分类</th>
<th class="px-stack-md py-4 font-label-caps text-label-caps text-secondary border-b border-outline-variant">状态</th>
<th class="px-stack-md py-4 font-label-caps text-label-caps text-secondary border-b border-outline-variant text-right">操作</th>
</tr>
</thead>
<tbody id="knowledge-files-table" class="divide-y divide-outline-variant"></tbody>
</table>
<div class="px-stack-md py-4 bg-surface-container-low border-t border-outline-variant">
<span id="knowledge-doc-count" class="text-sm text-secondary">共 0 个文件</span>
</div>
</div>
</div>
<!-- Tab: 临床案例 -->
<div id="knowledge-tab-cases" class="knowledge-tab-panel hidden">
<div class="bg-surface border border-outline-variant rounded-lg overflow-hidden mb-stack-md">
<div class="p-stack-md border-b border-outline-variant bg-surface-container-low flex flex-wrap justify-between items-center gap-3">
<div class="relative flex-1 min-w-[240px] max-w-md">
<span class="material-symbols-outlined absolute left-3 top-2.5 text-secondary text-lg">search</span>
<input id="case-library-search" class="w-full bg-surface border border-outline-variant rounded-lg pl-10 pr-4 py-2 text-sm" placeholder="搜索证型、症状、诊断、病例 ID…" type="text"/>
</div>
<button type="button" id="search-case-library-btn" class="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm">搜索病例</button>
</div>
<p id="case-library-stats" class="px-stack-md py-2 text-xs text-secondary border-b border-outline-variant">加载中…</p>
<table class="w-full text-left border-collapse">
<thead class="bg-surface-container-low">
<tr>
<th class="px-stack-md py-3 text-xs text-secondary">病例 ID</th>
<th class="px-stack-md py-3 text-xs text-secondary">证型 / 诊断</th>
<th class="px-stack-md py-3 text-xs text-secondary">性别·年龄</th>
<th class="px-stack-md py-3 text-xs text-secondary">来源文件</th>
<th class="px-stack-md py-3 text-xs text-secondary">症状摘要</th>
</tr>
</thead>
<tbody id="case-library-table" class="divide-y divide-outline-variant text-sm"></tbody>
</table>
<div class="px-stack-md py-3 bg-surface-container-low border-t border-outline-variant flex justify-between items-center">
<span id="case-library-count" class="text-sm text-secondary">—</span>
<button type="button" id="load-more-cases-btn" class="text-primary text-sm hidden">加载更多</button>
</div>
</div>
<div class="bg-surface border border-outline-variant rounded-lg overflow-hidden">
<div class="p-stack-md border-b border-outline-variant"><h3 class="font-title-sm text-primary">病例库文件（cases/）</h3></div>
<table class="w-full text-left border-collapse">
<thead class="bg-surface-container-low"><tr>
<th class="px-stack-md py-3 text-xs text-secondary">文件</th>
<th class="px-stack-md py-3 text-xs text-secondary">大小</th>
<th class="px-stack-md py-3 text-xs text-secondary text-right">操作</th>
</tr></thead>
<tbody id="case-files-table" class="divide-y divide-outline-variant text-sm"></tbody>
</table>
</div>
</div>
<!-- Tab: 索引状态 -->
<div id="knowledge-tab-index" class="knowledge-tab-panel hidden">
<div class="grid grid-cols-1 md:grid-cols-2 gap-gutter">
<section class="bg-surface border border-outline-variant p-stack-md rounded-lg">
<h3 class="font-title-sm text-primary mb-3">向量索引</h3>
<div id="knowledge-index-summary" class="space-y-2 text-sm text-secondary">加载中…</div>
<div class="flex flex-wrap gap-2 mt-4">
<button type="button" id="knowledge-refresh-index-btn" class="border border-outline-variant px-4 py-2 rounded text-sm">刷新状态</button>
<button type="button" id="knowledge-rebuild-index-btn" class="bg-primary text-on-primary px-4 py-2 rounded text-sm">重建索引</button>
</div>
<pre id="knowledge-index-detail" class="mt-4 text-xs bg-surface-container p-3 rounded max-h-64 overflow-auto"></pre>
</section>
<section class="bg-surface border border-outline-variant p-stack-md rounded-lg">
<h3 class="font-title-sm text-primary mb-3">知识库健康</h3>
<div id="knowledge-health-summary" class="space-y-2 text-sm"></div>
</section>
</div>
</div>
<!-- Management Section Lower Grid -->''',
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r"<!-- Management Section Lower Grid -->.*?<div class=\"mt-stack-lg grid",
        '<div class="mt-stack-lg grid',
        html,
        count=1,
        flags=re.S,
    )
    functional = '''
<div id="knowledge-import-section" class="mt-stack-lg grid grid-cols-1 lg:grid-cols-2 gap-gutter border-t border-outline-variant pt-stack-lg">
  <section class="bg-surface border border-outline-variant p-stack-md rounded-lg">
    <h3 class="font-title-sm text-primary mb-3">批量导入</h3>
    <p class="text-xs text-secondary mb-2">病例 JSON 请导入到 <code>cases/</code> 子目录，与理论资料一样纳入知识库索引。</p>
    <label class="font-label-caps text-label-caps text-secondary">子目录</label>
    <input id="import-subdir" value="cases" class="w-full border border-outline-variant rounded px-3 py-2 mb-2"/>
    <input id="import-files" type="file" multiple accept=".txt,.json,.md,.markdown" class="w-full mb-2"/>
    <label class="flex items-center gap-2 text-sm mb-2"><input id="import-overwrite" type="checkbox"> 覆盖同名</label>
    <button id="import-files-btn" class="bg-primary text-on-primary px-4 py-2 rounded font-label-caps">导入所选文件</button>
    <pre id="import-result" class="hidden mt-2 text-xs bg-surface-container p-2 rounded overflow-auto max-h-32"></pre>
  </section>
  <section class="bg-surface border border-outline-variant p-stack-md rounded-lg">
    <h3 class="font-title-sm text-primary mb-3">在线上传</h3>
    <input id="upload-path" placeholder="cases/my_cases.json" class="w-full border border-outline-variant rounded px-3 py-2 mb-2"/>
    <textarea id="upload-content" placeholder="文本 / JSON 内容…" class="w-full border border-outline-variant rounded px-3 py-2 mb-2 min-h-[80px]"></textarea>
    <label class="flex items-center gap-2 text-sm mb-2"><input id="upload-overwrite" type="checkbox"> 覆盖</label>
    <button id="upload-knowledge-btn" class="bg-primary text-on-primary px-4 py-2 rounded font-label-caps mb-3">上传文本</button>
  </section>
</div>
'''
    return html + functional


def patch_models(html: str) -> str:
    html = html.replace(
        '<input class="w-full bg-white border border-outline-variant rounded px-4 py-2 focus:ring-1 focus:ring-primary focus:border-primary outline-none" placeholder="例如: gpt-4-turbo" type="text" value="gpt-4o"/>',
        '<input id="llm-model" class="w-full bg-white border border-outline-variant rounded px-4 py-2 focus:ring-1 focus:ring-primary focus:border-primary outline-none" placeholder="deepseek-r1:1.5b" type="text"/>',
        1,
    )
    html = html.replace(
        '<input class="w-full bg-white border border-outline-variant rounded px-4 py-2 focus:ring-1 focus:ring-primary focus:border-primary outline-none" placeholder="输入您的 API Key" type="password" value="sk-proj-**********************"/>',
        '<input id="llm-api-key" class="w-full bg-white border border-outline-variant rounded px-4 py-2 focus:ring-1 focus:ring-primary focus:border-primary outline-none" placeholder="API Key（留空不修改）" type="password"/>',
        1,
    )
    html = html.replace(
        '<select class="w-full bg-white border border-outline-variant rounded px-4 py-2 focus:ring-1 focus:ring-primary focus:border-primary outline-none appearance-none">',
        '<select id="llm-provider" class="w-full bg-white border border-outline-variant rounded px-4 py-2 focus:ring-1 focus:ring-primary focus:border-primary outline-none appearance-none">',
        1,
    )
    html = html.replace(
        '<section class="col-span-12 lg:col-span-8 bg-surface-container-lowest border border-outline-variant rounded-lg p-stack-lg shadow-sm hover:shadow-md transition-shadow">',
        '<section id="llm-section" class="col-span-12 lg:col-span-8 bg-surface-container-lowest border border-outline-variant rounded-lg p-stack-lg shadow-sm hover:shadow-md transition-shadow">',
        1,
    )
    html = re.sub(
        r'<select id="llm-provider" class="[^"]*">.*?</select>',
        '''<select id="llm-provider" class="w-full bg-white border border-outline-variant rounded px-4 py-2 focus:ring-1 focus:ring-primary focus:border-primary outline-none appearance-none">
<option value="ollama">Local (Ollama)</option><option value="openai">OpenAI</option><option value="local">Local</option></select>''',
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'(<input id="llm-model"[^>]*/>)\s*</div>\s*</div>\s*<div class="flex flex-col gap-base">\s*<label class="font-label-caps text-label-caps text-on-surface-variant">API 密钥',
        r'''\1
</div>
<div class="flex flex-col gap-base">
<label class="font-label-caps text-label-caps text-on-surface-variant">Base URL</label>
<input id="llm-base-url" class="w-full bg-white border border-outline-variant rounded px-4 py-2 focus:ring-1 focus:ring-primary focus:border-primary outline-none" placeholder="http://127.0.0.1:11434" type="text"/>
</div>
<div class="flex flex-col gap-base">
<label class="font-label-caps text-label-caps text-on-surface-variant">Temperature</label>
<input id="llm-temperature" type="number" step="0.1" class="w-full bg-white border border-outline-variant rounded px-4 py-2 focus:ring-1 focus:ring-primary focus:border-primary outline-none" placeholder="0.3"/>
</div>
</div>
<div class="flex flex-col gap-base">
<label class="font-label-caps text-label-caps text-on-surface-variant">API 密钥''',
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'<button class="border border-outline-variant text-primary px-6 py-2.*?连通性测试\s*</button>',
        '<button type="button" id="test-llm-btn" class="border border-outline-variant text-primary px-6 py-2 rounded font-title-sm hover:bg-secondary-container transition-colors">连通性测试</button>',
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'<button class="bg-primary text-on-primary px-10 py-2 rounded font-title-sm text-title-sm hover:opacity-90 transition-opacity" type="button">\s*保存 LLM 配置\s*</button>',
        '<button type="button" id="save-llm-btn" class="bg-primary text-on-primary px-10 py-2 rounded font-title-sm hover:opacity-90">保存 LLM 配置</button>',
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'<!-- Embedding & Rerank \(Row 2\) -->.*?<!-- Advanced Settings Section',
        '''<!-- Embedding & Rerank (Row 2) -->
<section id="emb-section" class="col-span-12 md:col-span-6 bg-surface-container-lowest border border-outline-variant rounded-lg p-stack-lg shadow-sm">
<div class="flex items-center gap-3 mb-stack-md border-b border-outline-variant pb-base">
<span class="material-symbols-outlined text-tertiary p-2 bg-tertiary-fixed rounded-full">view_in_ar</span>
<h2 class="font-title-sm text-title-sm text-on-surface">Embedding 嵌入模型</h2>
</div>
<div class="space-y-4">
<div class="flex flex-col gap-1"><label class="font-label-caps text-label-caps text-secondary">Provider</label>
<select id="emb-provider" class="w-full bg-white border border-outline-variant rounded px-4 py-2"><option value="local">local</option><option value="ollama">ollama</option><option value="openai">openai</option></select></div>
<div class="flex flex-col gap-1"><label class="font-label-caps text-label-caps text-secondary">Model</label>
<input id="emb-model" class="w-full bg-white border border-outline-variant rounded px-4 py-2" placeholder="model / 路径"/></div>
<div class="flex flex-col gap-1"><label class="font-label-caps text-label-caps text-secondary">Base URL</label>
<input id="emb-base-url" class="w-full bg-white border border-outline-variant rounded px-4 py-2" placeholder="http://127.0.0.1:11434"/></div>
<div class="flex flex-col gap-1"><label class="font-label-caps text-label-caps text-secondary">API Key</label>
<input id="emb-api-key" type="password" class="w-full bg-white border border-outline-variant rounded px-4 py-2" placeholder="留空不修改"/></div>
<div class="flex gap-2 pt-2"><button type="button" id="save-emb-btn" class="flex-1 bg-primary text-on-primary py-2 rounded-lg font-label-caps">保存</button><button type="button" id="test-emb-btn" class="flex-1 border border-outline-variant text-primary py-2 rounded-lg font-label-caps">测试</button></div>
<pre id="emb-test-result" class="hidden text-xs bg-surface-container p-2 rounded mt-2"></pre>
</div>
</section>
<section id="rerank-section" class="col-span-12 md:col-span-6 bg-surface-container-lowest border border-outline-variant rounded-lg p-stack-lg shadow-sm">
<div class="flex items-center gap-3 mb-stack-md border-b border-outline-variant pb-base">
<span class="material-symbols-outlined text-primary p-2 bg-primary-fixed rounded-full">sort</span>
<h2 class="font-title-sm text-title-sm text-on-surface">Rerank 重排序模型</h2>
</div>
<div class="space-y-4">
<div class="flex flex-col gap-1"><label class="font-label-caps text-label-caps text-secondary">Provider</label>
<select id="rerank-provider" class="w-full bg-white border border-outline-variant rounded px-4 py-2"><option value="none">none</option><option value="local">local</option><option value="api">api</option></select></div>
<div class="flex flex-col gap-1"><label class="font-label-caps text-label-caps text-secondary">Model</label>
<input id="rerank-model" class="w-full bg-white border border-outline-variant rounded px-4 py-2"/></div>
<div class="flex flex-col gap-1"><label class="font-label-caps text-label-caps text-secondary">Base URL</label>
<input id="rerank-base-url" class="w-full bg-white border border-outline-variant rounded px-4 py-2"/></div>
<div class="flex flex-col gap-1"><label class="font-label-caps text-label-caps text-secondary">API Key</label>
<input id="rerank-api-key" type="password" class="w-full bg-white border border-outline-variant rounded px-4 py-2" placeholder="留空不修改"/></div>
<div class="flex flex-col gap-1"><label class="font-label-caps text-label-caps text-secondary">Top N</label>
<input id="rerank-top-n" type="number" class="w-full bg-white border border-outline-variant rounded px-4 py-2"/></div>
<div class="flex gap-2 pt-2"><button type="button" id="save-rerank-btn" class="flex-1 bg-primary text-on-primary py-2 rounded-lg font-label-caps">保存</button><button type="button" id="test-rerank-btn" class="flex-1 border border-outline-variant text-primary py-2 rounded-lg font-label-caps">测试</button></div>
<pre id="rerank-test-result" class="hidden text-xs bg-surface-container p-2 rounded mt-2"></pre>
<pre id="llm-test-result" class="hidden text-xs bg-surface-container p-2 rounded mt-2"></pre>
</div>
</section>
<!-- Advanced Settings Section''',
        html,
        count=1,
        flags=re.S,
    )
    return html


def patch_system(html: str) -> str:
    html = re.sub(
        r'<div class="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-primary transition-all duration-500" style="width:68\.4%"></div>',
        '<div id="rebuild-progress-bar" class="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-primary transition-all duration-500" style="width:0%">0%</div>',
        html,
        count=1,
    )
    html = html.replace(
        "立即生成新密钥",
        "立即生成新密钥",
    )
    html = re.sub(
        r'<button class="w-full bg-primary text-on-primary py-3 rounded font-label-caps.*?>[\s\S]*?立即生成新密钥[\s\S]*?</button>',
        '<button type="button" id="regen-key-btn" class="w-full bg-primary text-on-primary py-3 rounded font-label-caps">立即生成新密钥</button>',
        html,
        count=1,
    )
    html = re.sub(
        r'<button class="bg-primary text-on-primary px-6 py-2 rounded font-label-caps.*?暂停重建</button>',
        '<button type="button" id="rebuild-index-btn" class="bg-primary text-on-primary px-6 py-2 rounded font-label-caps">重建向量索引</button>',
        html,
        count=1,
        flags=re.S,
    )
    functional = '''
<div id="rebuild-progress-panel" class="hidden mt-4">
  <p id="rebuild-progress-meta" class="font-body-sm text-secondary mb-2"></p>
</div>
<div class="mt-stack-lg grid grid-cols-1 lg:grid-cols-2 gap-gutter">
  <section class="bg-surface border border-outline-variant p-stack-md rounded-lg">
    <h3 class="font-title-sm text-primary mb-3">RAG 默认参数</h3>
    <label>retrieval_top_k</label><input id="rag-retrieval-k" type="number" class="w-full border rounded px-3 py-2 mb-2"/>
    <label>final_top_k</label><input id="rag-final-k" type="number" class="w-full border rounded px-3 py-2 mb-2"/>
    <label class="flex items-center gap-2"><input id="rag-rebuild-missing" type="checkbox"> 索引缺失时自动构建</label>
    <div class="flex flex-wrap gap-2 mt-3">
      <button id="save-config-btn" class="bg-primary text-white px-4 py-2 rounded">保存全部配置</button>
      <button id="test-models-btn" class="border px-4 py-2 rounded">测试全部模型</button>
      <button id="load-index-status-btn" class="border px-4 py-2 rounded">刷新索引状态</button>
    </div>
    <pre id="index-status" class="mt-2 text-xs bg-surface-container p-2 rounded max-h-40 overflow-auto"></pre>
    <pre id="model-test-result" class="hidden mt-2 text-xs bg-surface-container p-2 rounded max-h-40 overflow-auto"></pre>
  </section>
  <section class="bg-surface border border-outline-variant p-stack-md rounded-lg">
    <h3 class="font-title-sm text-primary mb-3">CORS</h3>
    <input id="cors-origins" placeholder="*, http://localhost:8000" class="w-full border rounded px-3 py-2"/>
    <p class="text-xs text-secondary mt-2">修改 CORS 后需重启服务</p>
  </section>
</div>
<div id="system-status" class="mt-3"></div>
'''
    return html + functional


def patch_rag(html: str) -> str:
    html = html.replace(
        '<textarea class="w-full bg-surface border border-outline-variant rounded-lg p-3 font-body-md text-body-md focus:border-primary outline-none transition-colors" placeholder="输入您想测试的问题..." rows="4"></textarea>',
        '<textarea id="question" class="w-full bg-surface border border-outline-variant rounded-lg p-3 font-body-md focus:border-primary outline-none" placeholder="输入您想测试的问题..." rows="4"></textarea>',
    )
    html = re.sub(
        r'<button class="flex-1 bg-primary text-on-primary font-label-caps.*?运行测试\s*</button>',
        '<button type="button" id="run-rag-btn" class="flex-1 bg-primary text-on-primary font-label-caps py-3 rounded flex items-center justify-center gap-2"><span class="material-symbols-outlined text-[20px]">send</span> 运行测试</button>',
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'<div class="bg-surface p-stack-md rounded-lg border border-outline-variant/30 italic font-body-md.*?</div>',
        '<div id="rag-answer" class="bg-surface p-stack-md rounded-lg border border-outline-variant/30 font-body-md text-on-surface">等待查询…</div>',
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'<div class="p-stack-md max-h-\[600px\] overflow-y-auto">.*?</div>\s*</section>\s*<!-- Debug Logs Table -->',
        '<div id="rag-retrieved" class="p-stack-md max-h-[600px] overflow-y-auto"></div></section><section class="bg-surface-container-lowest border border-outline-variant rounded-lg overflow-hidden mt-gutter"><h3 class="font-label-caps p-stack-md border-b border-outline-variant text-secondary">Rerank 结果</h3><div id="rag-reranked" class="p-stack-md max-h-[400px] overflow-y-auto"></div></section><!-- Debug Logs Table -->',
        html,
        count=1,
        flags=re.S,
    )
    functional = '''
<div class="mt-gutter grid grid-cols-1 lg:grid-cols-2 gap-gutter">
  <section class="bg-surface border border-outline-variant p-stack-md rounded-lg">
    <h3 class="font-label-caps text-secondary mb-2">RAG 参数</h3>
    <label>初检索 Top K</label><input id="retrieval-top-k" type="number" class="w-full border rounded px-3 py-2 mb-2"/>
    <label>最终 Top K</label><input id="final-top-k" type="number" class="w-full border rounded px-3 py-2 mb-2"/>
    <label class="flex items-center gap-2"><input id="enable-llm" type="checkbox" checked> 启用 LLM</label>
    <div id="rag-status" class="mt-2 text-sm"></div>
  </section>
  <section class="bg-surface border border-outline-variant p-stack-md rounded-lg">
    <button id="load-rag-stats-btn" class="border px-3 py-1 rounded text-sm mb-2">刷新统计</button>
    <pre id="rag-stats" class="text-xs bg-surface-container p-2 rounded max-h-32 overflow-auto">点击刷新…</pre>
    <div class="flex gap-2 mt-2 flex-wrap items-center">
      <button id="load-rag-logs-btn" class="border px-3 py-1 rounded text-sm">刷新日志</button>
      <button id="clear-rag-logs-btn" class="border px-3 py-1 rounded text-sm text-error">清空</button>
      <select id="rag-log-source" class="border rounded px-2 py-1 text-sm"><option value="">全部来源</option><option value="admin">admin</option><option value="diagnosis">diagnosis</option></select>
      <select id="rag-log-kind" class="border rounded px-2 py-1 text-sm"><option value="">全部类型</option><option value="query">query</option><option value="search">search</option></select>
    </div>
    <div id="rag-logs" class="mt-2 max-h-48 overflow-auto text-sm"></div>
  </section>
</div>
'''
    return html + functional


def patch_patients(html: str) -> str:
    html = re.sub(
        r'placeholder="搜索患者姓名、ID或症状\.\.\." type="text"',
        'id="patient-search" placeholder="搜索患者姓名、手机号或 ID..." type="text"',
        html,
        count=1,
    )
    html = html.replace(
        '<h2 class="font-headline-md text-headline-md text-primary">患者管理</h2>',
        '<div class="flex items-center gap-3 flex-wrap">'
        '<h2 class="font-headline-md text-headline-md text-primary">患者管理</h2>'
        '<button type="button" id="refresh-patients-btn" class="border border-outline-variant px-4 py-1.5 rounded-full text-sm">刷新</button>'
        '<button type="button" id="new-patient-btn" class="bg-primary text-on-primary px-4 py-1.5 rounded-full text-sm">新建患者</button>'
        '</div>',
        1,
    )
    html = re.sub(
        r"<!-- Bento-style Patient List -->.*?<!-- Right Column: Patient Details",
        """<!-- Bento-style Patient List -->
<div id="patient-list" class="space-y-4 custom-scrollbar max-h-[70vh] overflow-y-auto"></div>
<p id="patient-list-meta" class="text-xs text-secondary mt-2"></p>
</div>
<!-- Right Column: Patient Details""",
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r"<!-- Right Column: Patient Details & History -->.*?<!-- Footer Component -->",
        """<!-- Right Column: Patient Details & History -->
<div class="col-span-12 lg:col-span-8 space-y-stack-md" id="patient-detail-panel">
<div id="patient-detail-empty" class="bg-surface rounded-[15px] card-shadow p-12 text-center text-secondary">
<span class="material-symbols-outlined text-5xl mb-4 opacity-40">person_search</span>
<p>从左侧选择患者，或点击「新建患者」</p>
</div>
<div id="patient-detail-content" class="hidden space-y-stack-md">
<div class="bg-surface rounded-[15px] card-shadow overflow-hidden">
<div class="bg-surface-container px-gutter py-6 border-b border-outline-variant flex flex-wrap justify-between items-end gap-4">
<div>
<h4 id="patient-detail-title" class="font-display-lg text-headline-lg text-on-surface"></h4>
<div id="patient-detail-meta" class="flex flex-wrap gap-4 mt-2 text-on-surface-variant text-sm"></div>
</div>
<div class="flex gap-2 flex-wrap" id="patient-detail-actions"></div>
</div>
<div class="p-gutter grid grid-cols-1 md:grid-cols-2 gap-6">
<div><h5 class="font-label-md text-outline uppercase mb-3">主诉 / 症状</h5><p id="patient-detail-symptoms" class="text-on-surface leading-relaxed"></p></div>
<div><h5 class="font-label-md text-outline uppercase mb-3">诊断与治疗</h5><p id="patient-detail-treatment" class="text-on-surface leading-relaxed"></p></div>
</div>
</div>
<div class="space-y-stack-sm">
<h3 class="font-label-md uppercase text-outline px-2">诊疗记录</h3>
<div class="bg-surface rounded-[15px] card-shadow overflow-hidden">
<table class="w-full text-left border-collapse">
<thead class="bg-surface-container-low text-on-surface-variant text-[13px] uppercase">
<tr><th class="px-6 py-4">日期</th><th class="px-6 py-4">主诉</th><th class="px-6 py-4">证型</th><th class="px-6 py-4">疗效</th><th class="px-6 py-4 text-right">操作</th></tr>
</thead>
<tbody id="patient-history-body" class="divide-y divide-outline-variant"></tbody>
</table>
</div>
</div>
</div>
</div>
</div>
</section>
<!-- Footer Component -->""",
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(r"<!-- Footer Component -->.*?</footer>", "", html, count=1, flags=re.S)
    html = re.sub(
        r"<!-- Floating Action Button.*?</div>\s*<script>.*?</script>",
        "",
        html,
        count=1,
        flags=re.S,
    )
    html += """
<div id="patient-form-panel" class="hidden mt-stack-lg bg-surface border border-outline-variant rounded-lg p-stack-md">
  <h3 id="patient-form-title" class="font-title-sm text-primary mb-4">新建患者</h3>
  <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
    <input id="pf-name" placeholder="姓名 *" class="border border-outline-variant rounded px-3 py-2 text-sm"/>
    <input id="pf-gender" placeholder="性别" class="border border-outline-variant rounded px-3 py-2 text-sm"/>
    <input id="pf-age" type="number" placeholder="年龄" class="border border-outline-variant rounded px-3 py-2 text-sm"/>
    <input id="pf-phone" placeholder="手机号" class="border border-outline-variant rounded px-3 py-2 text-sm"/>
    <input id="pf-id-number" placeholder="证件号" class="border border-outline-variant rounded px-3 py-2 text-sm col-span-2"/>
    <input id="pf-address" placeholder="地址" class="border border-outline-variant rounded px-3 py-2 text-sm col-span-2"/>
    <input id="pf-constitution" placeholder="体质" class="border border-outline-variant rounded px-3 py-2 text-sm col-span-2"/>
    <input id="pf-allergies" placeholder="过敏史" class="border border-outline-variant rounded px-3 py-2 text-sm col-span-2"/>
  </div>
  <textarea id="pf-notes" placeholder="备注" class="w-full border border-outline-variant rounded px-3 py-2 mb-3 min-h-[50px]"></textarea>
  <div class="flex gap-2">
    <button type="button" id="pf-save-btn" class="bg-primary text-on-primary px-4 py-2 rounded">保存</button>
    <button type="button" id="pf-cancel-btn" class="border border-outline-variant px-4 py-2 rounded">取消</button>
  </div>
  <div id="patient-status" class="mt-2"></div>
</div>
<div id="visit-form-panel" class="hidden mt-stack-md bg-surface-container-low border border-outline-variant rounded-lg p-stack-md">
  <h3 class="font-title-sm text-primary mb-3">新增就诊记录</h3>
  <div class="grid grid-cols-2 gap-2 mb-2">
    <input id="vf-date" placeholder="日期 YYYY-MM-DD" class="border rounded px-2 py-1 text-sm"/>
    <input id="vf-complaint" placeholder="主诉" class="border rounded px-2 py-1 text-sm"/>
    <input id="vf-diagnosis" placeholder="诊断" class="border rounded px-2 py-1 text-sm"/>
    <input id="vf-syndrome" placeholder="证型" class="border rounded px-2 py-1 text-sm"/>
  </div>
  <textarea id="vf-symptoms" placeholder="症状" class="w-full border rounded px-2 py-1 text-sm mb-1 min-h-[40px]"></textarea>
  <textarea id="vf-treatment" placeholder="治疗方案" class="w-full border rounded px-2 py-1 text-sm mb-1 min-h-[40px]"></textarea>
  <textarea id="vf-efficacy" placeholder="疗效" class="w-full border rounded px-2 py-1 text-sm mb-2 min-h-[30px]"></textarea>
  <div class="flex gap-2">
    <button type="button" id="vf-save-btn" class="bg-primary text-white px-3 py-1 rounded text-sm">保存就诊</button>
    <button type="button" id="vf-cancel-btn" class="border px-3 py-1 rounded text-sm">取消</button>
  </div>
</div>"""
    return html


def sidebar() -> str:
    tabs = [
        ("dashboard", "dashboard", "概览"),
        ("patients", "group", "患者管理"),
        ("knowledge", "database", "知识库"),
        ("embedding", "view_in_ar", "Embedding"),
        ("llm", "psychology", "LLM"),
        ("rerank", "sort", "Rerank"),
        ("rag", "bug_report", "RAG 检索"),
        ("system", "settings_suggest", "系统"),
    ]
    items = []
    for i, (tab, icon, label) in enumerate(tabs):
        active = "active bg-primary-container text-on-primary-container font-bold" if i == 0 else "text-secondary hover:bg-secondary-container"
        items.append(
            f'<button type="button" class="tab flex items-center gap-3 rounded-full px-4 py-2 font-label-caps transition-all {active}" data-tab="{tab}" data-scroll="{label.lower()}"><span class="material-symbols-outlined">{icon}</span>{label}</button>'
        )
    return f'''
<aside class="hidden lg:flex flex-col h-screen fixed left-0 top-0 p-stack-md w-64 bg-surface-container-low border-r border-outline-variant pt-24 z-40">
  <div class="mb-8 px-4"><h2 class="font-title-sm text-primary">中医知识库管理端</h2><p class="font-label-caps text-secondary">Stitch UI</p></div>
  <nav class="flex-1 flex flex-col gap-1 overflow-y-auto custom-scrollbar" id="sidebar-nav">{"".join(items)}</nav>
</aside>'''


def topnav() -> str:
    return '''
<nav class="fixed top-0 w-full z-50 flex justify-between items-center px-margin-page py-base bg-surface/95 backdrop-blur border-b border-outline-variant">
  <div class="flex items-center gap-8 lg:pl-64"><span class="font-headline-md font-bold text-primary">ZenPulse AI · 管理端</span></div>
  <div class="flex items-center gap-3 flex-wrap justify-end max-w-2xl">
    <input id="api-key-input" type="password" placeholder="Admin API Key" class="min-w-[180px] text-sm py-2 px-3 border border-outline-variant rounded-lg"/>
    <button id="save-key-btn" class="bg-primary text-on-primary text-sm px-4 py-2 rounded-lg">保存</button>
    <button id="test-key-btn" class="border border-outline-variant text-sm px-4 py-2 rounded-lg">连接</button>
    <span id="auth-status" class="text-xs text-secondary max-w-[200px]"></span>
  </div>
</nav>'''


def panel_wrap(panel_id: str, content: str, active: bool = False) -> str:
    cls = "admin-panel"
    if active:
        cls += " active"
    return f'<section id="panel-{panel_id}" class="{cls} lg:ml-64 pt-24 pb-16 px-margin-page min-h-screen"><div class="max-w-container-max mx-auto">{content}</div></section>'


def build() -> None:
    head = extract_head(read("_1"))
    extra_css = """
    .admin-panel { display: none; }
    .admin-panel.active { display: block; }
    .status { padding: 8px 12px; border-radius: 8px; font-size: 0.875rem; margin-top: 8px; }
    .status.ok { background: #e8f5e9; color: #2d5016; }
    .status.err { background: #ffebee; color: #b71c1c; }
    .card-shadow { box-shadow: 0 4px 20px rgba(139, 69, 19, 0.08); }
    .knowledge-tab-panel { display: none; }
    .knowledge-tab-panel.active { display: block; }
    .knowledge-tab.active { background-color: #6c2f00; color: #fff; }
    """
    head = head.replace("</style>", extra_css + "\n  </style>", 1)

    panels = [
        ("dashboard", patch_dashboard(extract_main_inner(read("_1"))), True),
        ("patients", patch_patients(extract_main_inner(read_patients())), False),
        ("knowledge", patch_knowledge(extract_main_inner(read("_2"))), False),
        ("models", patch_models(extract_main_inner(read("_3"))), False),
        ("rag", patch_rag(extract_main_inner(read("rag"))), False),
        ("system", patch_system(extract_main_inner(read("_4"))), False),
    ]

    auth_gate = '''
<div id="auth-gate" class="lg:ml-64 pt-28 px-margin-page">
  <div class="max-w-lg mx-auto bg-surface-container-lowest border border-outline-variant rounded-lg p-8 text-center">
    <span class="material-symbols-outlined text-5xl text-primary">vpn_key</span>
    <h2 class="font-headline-md text-primary mt-4">请先连接管理端</h2>
    <p class="text-secondary mt-2 text-sm">右上角输入 Key（见 data/admin_config.json）后点击「连接」</p>
    <div id="auth-gate-status" class="status err hidden mt-4"></div>
  </div>
</div>'''

    body_parts = [
        "<body class=\"font-body-md bg-surface text-on-surface\">",
        topnav(),
        sidebar(),
        auth_gate,
        '<div id="admin-panels" class="hidden">',
    ]
    for pid, content, active in panels:
        body_parts.append(panel_wrap(pid, content, active))
    body_parts.append("</div>")
    body_parts.append('<footer class="lg:ml-64 py-6 px-margin-page border-t border-outline-variant text-center text-secondary text-sm">© ZenPulse AI · 中医知识库管理端</footer>')
    body_parts.append('<script src="/admin-static/app.js"></script>')
    body_parts.append("</body></html>")

    OUT.write_text(head + "\n" + "\n".join(body_parts), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
