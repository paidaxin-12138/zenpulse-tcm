const STORAGE_KEY = 'tcm_admin_api_key'; // 遗留：不再持久化 API Key
const DISPLAY_NAME_KEY = 'tcm_admin_display_name';

const TAB_PANEL = {
  dashboard: 'dashboard',
  patients: 'patients',
  knowledge: 'knowledge',
  embedding: 'models',
  llm: 'models',
  rerank: 'models',
  rag: 'rag',
  system: 'system',
};

const SCROLL_TARGET = {
  embedding: 'emb-section',
  llm: 'llm-section',
  rerank: 'rerank-section',
};

function getStoredApiKey() {
  return '';
}

function setStoredApiKey(_key) {
  sessionStorage.removeItem(STORAGE_KEY);
}

function getStoredDisplayName() {
  return sessionStorage.getItem(DISPLAY_NAME_KEY) || '';
}

function setStoredDisplayName(name) {
  sessionStorage.removeItem(DISPLAY_NAME_KEY);
  if (name) sessionStorage.setItem(DISPLAY_NAME_KEY, name);
}

function syncHiddenApiKeyInput(key) {
  const input = document.getElementById('api-key-input');
  if (input) input.value = key || '';
}

function getLoginApiKey() {
  return document.getElementById('login-api-key')?.value.trim() || '';
}

function getApiKey() {
  return document.getElementById('api-key-input')?.value.trim() || '';
}

function updateAdminUserLabel(role) {
  const el = document.getElementById('admin-user-label');
  if (!el) return;
  const name = getStoredDisplayName();
  const parts = [name, role].filter(Boolean);
  if (!parts.length) {
    el.classList.add('hidden');
    el.textContent = '';
    return;
  }
  el.textContent = parts.join(' · ');
  el.classList.remove('hidden');
}

function setStatus(elId, message, ok) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.className = 'status ' + (ok ? 'ok' : 'err');
  el.textContent = message;
}

function setAuthGate(message, ok) {
  const gate = document.getElementById('auth-gate');
  const gateStatus = document.getElementById('auth-gate-status');
  const shell = document.getElementById('admin-shell');
  if (ok) {
    gate?.classList.add('hidden');
    shell?.classList.remove('hidden');
    return;
  }
  gate?.classList.remove('hidden');
  shell?.classList.add('hidden');
  if (message && gateStatus) {
    gateStatus.classList.remove('hidden');
    gateStatus.className = 'status err mt-2';
    gateStatus.textContent = message;
  } else if (gateStatus) {
    gateStatus.classList.add('hidden');
    gateStatus.textContent = '';
  }
}

function setLoginBusy(busy) {
  const btn = document.getElementById('login-submit-btn');
  if (!btn) return;
  btn.disabled = busy;
  btn.classList.toggle('opacity-70', busy);
  btn.classList.toggle('pointer-events-none', busy);
}

async function attemptLogin(options = {}) {
  const key = (options.key ?? getLoginApiKey()).trim();
  if (!key) {
    setAuthGate('请输入 Admin API Key', false);
    return false;
  }
  const displayName = document.getElementById('login-account')?.value.trim() || '';
  syncHiddenApiKeyInput('');
  setStoredApiKey('');
  setLoginBusy(true);
  try {
    const res = await fetch('/api/admin/session/login', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: key, display_name: displayName }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      let detail = data.detail || res.statusText;
      if (Array.isArray(detail)) detail = detail.map((d) => d.msg || JSON.stringify(d)).join('；');
      throw new Error(detail || '登录失败');
    }
    setStoredDisplayName(displayName || data.display_name || '');
    const loginKey = document.getElementById('login-api-key');
    if (loginKey) loginKey.value = '';
    await loadConfig();
    return true;
  } catch (err) {
    setStoredDisplayName('');
    syncHiddenApiKeyInput('');
    setAuthGate('登录失败：' + err.message, false);
    return false;
  } finally {
    setLoginBusy(false);
  }
}

function logoutAdmin() {
  fetch('/api/admin/session/logout', { method: 'POST', credentials: 'include' }).catch(() => {});
  setStoredApiKey('');
  setStoredDisplayName('');
  syncHiddenApiKeyInput('');
  const loginKey = document.getElementById('login-api-key');
  const loginAccount = document.getElementById('login-account');
  if (loginKey) loginKey.value = '';
  if (loginAccount) loginAccount.value = '';
  setStatus('auth-status', '', false);
  updateAdminUserLabel('');
  setAuthGate('', false);
}

async function adminFetch(path, options = {}) {
  const headers = Object.assign({}, options.headers || {}, {
    'Content-Type': 'application/json',
  });
  const manualKey = getApiKey();
  if (manualKey) headers['X-Admin-API-Key'] = manualKey;
  const res = await fetch('/api/admin' + path, { ...options, credentials: 'include', headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    let detail = data.detail || res.statusText;
    if (Array.isArray(detail)) detail = detail.map((d) => d.msg || JSON.stringify(d)).join('；');
    if (res.status === 403) detail = `权限不足：${detail}`;
    if (res.status === 401) detail = `鉴权失败：${detail}`;
    throw new Error(detail);
  }
  return data;
}

async function adminUploadFiles(path, formData) {
  const headers = {};
  const manualKey = getApiKey();
  if (manualKey) headers['X-Admin-API-Key'] = manualKey;
  const res = await fetch('/api/admin' + path, {
    method: 'POST',
    credentials: 'include',
    headers,
    body: formData,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

function switchTab(tabName) {
  const panelId = TAB_PANEL[tabName] || tabName;
  document.querySelectorAll('.tab').forEach((t) => {
    t.classList.toggle('active', t.dataset.tab === tabName);
    if (t.closest('#sidebar-nav')) {
      const on = t.dataset.tab === tabName;
      t.classList.toggle('bg-primary-container', on);
      t.classList.toggle('text-on-primary-container', on);
      t.classList.toggle('font-bold', on);
      t.classList.toggle('text-secondary', !on);
    }
  });
  document.querySelectorAll('.admin-panel').forEach((p) => {
    p.classList.toggle('active', p.id === 'panel-' + panelId);
  });
  const scrollId = SCROLL_TARGET[tabName];
  if (scrollId) {
    setTimeout(() => document.getElementById(scrollId)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
  }
  if (tabName === 'patients') loadPatients().catch(() => {});
  if (tabName === 'knowledge') initKnowledgePanel().catch(() => {});
}

document.querySelectorAll('[data-goto]').forEach((btn) => {
  btn.addEventListener('click', () => switchTab(btn.dataset.goto));
});

async function savePartialConfig(section) {
  const full = collectConfig();
  await adminFetch('/config', { method: 'PUT', body: JSON.stringify({ [section]: full[section] }) });
}

function formatTileValue(value) {
  const full = String(value ?? '-');
  if (full === '-') return { display: full, full, long: false };
  const isLong = full.length > 24 || /[/\\]/.test(full);
  if (!isLong) return { display: full, full, long: false };
  const parts = full.split(/[/\\]/).filter(Boolean);
  const base = parts[parts.length - 1] || full;
  const parent = parts.length > 1 ? parts[parts.length - 2] : '';
  const display = parent ? `${parent}/${base}` : base;
  return { display, full, long: true };
}

function formatModelShort(model) {
  const full = String(model || '-');
  if (full === '-') return full;
  if (full.length <= 40 && !/[/\\]/.test(full)) return full;
  const parts = full.split(/[/\\]/).filter(Boolean);
  return parts[parts.length - 1] || full;
}

function stitchTile(label, value, sub, goto) {
  const v = formatTileValue(value);
  const valueClass = v.long
    ? 'font-data-mono text-data-mono text-primary text-sm leading-snug break-all line-clamp-3'
    : 'font-display-lg text-display-lg text-primary break-words';
  return `<div class="dashboard-tile bg-surface-container-lowest border border-outline-variant p-stack-md rounded-xl flex flex-col justify-between min-w-0 overflow-hidden">
    <span class="font-label-caps text-label-caps text-secondary">${label}</span>
    <div class="mt-2 min-w-0"><span class="${valueClass}" title="${escapeHtml(v.full)}">${escapeHtml(v.display)}</span>
    ${sub ? `<span class="text-secondary font-label-caps text-label-caps block mt-1 truncate" title="${escapeHtml(sub)}">${escapeHtml(sub)}</span>` : ''}</div>
    ${goto ? `<button class="mt-3 border border-outline-variant text-primary px-3 py-1 rounded text-sm shrink-0" data-goto="${goto}">查看</button>` : ''}
  </div>`;
}

async function loadDashboard() {
  const data = await adminFetch('/dashboard');
  const box = document.getElementById('dashboard-content');
  if (!box) return;
  const idx = data.index || {};
  const kn = data.knowledge || {};
  const rb = data.rebuild || {};
  const models = data.models || {};
  box.innerHTML = [
    stitchTile('知识库文件', kn.total_files ?? 0, '个文件', 'knowledge'),
    stitchTile('向量索引', idx.exists ? (idx.document_count ?? '?') + ' 分块' : '未构建', idx.exists ? '已就绪' : '请重建', 'system'),
    stitchTile('索引重建', (rb.progress ?? 0) + '%', rb.status || 'idle', 'system'),
    stitchTile('RAG 调用', data.rag_stats?.total ?? 0, '累计次数', 'rag'),
    stitchTile('Embedding', models.embedding?.model || '-', models.embedding?.provider || '', 'embedding'),
    stitchTile('LLM', models.llm?.model || '-', models.llm?.provider || '', 'llm'),
  ].join('');
  box.querySelectorAll('[data-goto]').forEach((btn) => btn.addEventListener('click', () => switchTab(btn.dataset.goto)));

  const tbody = document.getElementById('provider-status-body');
  if (tbody) {
    const rows = [
      { name: 'Embedding', type: '向量嵌入', p: models.embedding?.provider, m: models.embedding?.model },
      { name: 'LLM', type: '大语言模型', p: models.llm?.provider, m: models.llm?.model },
      { name: 'Rerank', type: '重排序', p: models.rerank?.provider, m: models.rerank?.model },
    ];
    tbody.innerHTML = rows.map((r) => `<tr>
      <td class="px-stack-md py-4 font-title-sm max-w-[240px]"><span class="block truncate" title="${escapeHtml(r.m || '-')}">${r.name} · ${escapeHtml(formatModelShort(r.m))}</span></td>
      <td class="px-stack-md py-4 font-body-sm text-secondary">${r.type}</td>
      <td class="px-stack-md py-4"><span class="bg-[#e7f5e9] text-[#2E7D32] px-2 py-1 rounded-full text-xs font-bold">${r.p || '未配置'}</span></td>
      <td class="px-stack-md py-4"><button class="text-primary text-sm" data-goto="${r.name === 'Embedding' ? 'embedding' : r.name === 'LLM' ? 'llm' : 'rerank'}">配置</button></td>
    </tr>`).join('');
    tbody.querySelectorAll('[data-goto]').forEach((b) => b.addEventListener('click', () => switchTab(b.dataset.goto)));
  }

  const updated = document.getElementById('dashboard-updated');
  if (updated) updated.textContent = new Date().toLocaleTimeString('zh-CN');
}

function fillConfig(cfg) {
  const set = (id, val) => { const el = document.getElementById(id); if (el && val != null) el.value = val; };
  set('emb-provider', cfg.embedding.provider);
  set('emb-model', cfg.embedding.model || '');
  set('emb-base-url', cfg.embedding.base_url || '');
  set('llm-provider', cfg.llm.provider);
  set('llm-model', cfg.llm.model || '');
  set('llm-base-url', cfg.llm.base_url || '');
  set('llm-temperature', cfg.llm.temperature ?? 0.3);
  set('rerank-provider', cfg.rerank.provider);
  set('rerank-model', cfg.rerank.model || '');
  set('rerank-base-url', cfg.rerank.base_url || '');
  set('rerank-top-n', cfg.rerank.top_n ?? 5);
  set('rag-retrieval-k', cfg.rag.retrieval_top_k ?? 20);
  set('rag-final-k', cfg.rag.final_top_k ?? 5);
  const missing = document.getElementById('rag-rebuild-missing');
  if (missing) missing.checked = !!cfg.rag.rebuild_on_missing_index;
  const rbacOn = document.getElementById('rbac-enabled');
  if (rbacOn) rbacOn.checked = !!cfg.rbac?.enabled;
  const origins = cfg.server?.cors_origins || ['http://127.0.0.1:8000', 'http://localhost:8000'];
  set('cors-origins', origins.join(', '));
  set('allow-public-diagnose', cfg.server?.allow_public_diagnose !== false ? 'true' : 'false');
  set('allow-public-knowledge', cfg.server?.allow_public_knowledge_search !== false ? 'true' : 'false');
  set('rate-limit-per-minute', cfg.server?.rate_limit_per_minute ?? 60);
  const wx = cfg.wechat_miniprogram || {};
  set('wx-app-id', wx.app_id || '');
  set('wx-app-secret', '');
  set('wx-token-secret', '');
  set('wx-token-ttl', wx.token_ttl_hours ?? 72);
  const wxDev = document.getElementById('wx-dev-mode');
  if (wxDev) wxDev.value = wx.dev_mode ? 'true' : 'false';
  const wxHint = document.getElementById('wx-config-status');
  if (wxHint) {
    const parts = [];
    if (wx.app_secret_set) parts.push('AppSecret 已配置');
    if (wx.token_secret_set) parts.push('Token 密钥已配置');
    wxHint.textContent = parts.length ? parts.join(' · ') : '密钥类字段留空表示不修改';
  }
  const badge = document.getElementById('rag-llm-model-badge');
  if (badge) badge.textContent = cfg.llm?.model || 'LLM';
}

function collectConfig() {
  const v = (id) => document.getElementById(id)?.value ?? '';
  return {
    embedding: { provider: v('emb-provider'), model: v('emb-model').trim(), base_url: v('emb-base-url').trim(), api_key: v('emb-api-key') },
    llm: { provider: v('llm-provider'), model: v('llm-model').trim(), base_url: v('llm-base-url').trim(), api_key: v('llm-api-key'), temperature: parseFloat(v('llm-temperature') || '0.3') },
    rerank: { provider: v('rerank-provider'), model: v('rerank-model').trim(), base_url: v('rerank-base-url').trim(), api_key: v('rerank-api-key'), top_n: parseInt(v('rerank-top-n') || '5', 10) },
    rag: { retrieval_top_k: parseInt(v('rag-retrieval-k') || '20', 10), final_top_k: parseInt(v('rag-final-k') || '5', 10), rebuild_on_missing_index: document.getElementById('rag-rebuild-missing')?.checked },
    rbac: { enabled: document.getElementById('rbac-enabled')?.checked ?? false },
    server: {
      cors_origins: v('cors-origins').split(',').map((s) => s.trim()).filter(Boolean),
      allow_public_diagnose: v('allow-public-diagnose') === 'true',
      allow_public_knowledge_search: v('allow-public-knowledge') === 'true',
      rate_limit_per_minute: parseInt(v('rate-limit-per-minute') || '60', 10),
    },
    wechat_miniprogram: collectWxConfig(),
  };
}

function collectWxConfig() {
  const v = (id) => document.getElementById(id)?.value ?? '';
  const wx = {
    app_id: v('wx-app-id').trim(),
    dev_mode: v('wx-dev-mode') === 'true',
    token_ttl_hours: parseInt(v('wx-token-ttl') || '72', 10),
  };
  const secret = v('wx-app-secret').trim();
  const tokenSecret = v('wx-token-secret').trim();
  if (secret) wx.app_secret = secret;
  if (tokenSecret) wx.token_secret = tokenSecret;
  return wx;
}

async function loadLlmSetupPanel() {
  const box = document.getElementById('llm-setup-report');
  if (!box) return;
  try {
    const report = await adminFetch('/system/llm-setup');
    box.textContent = [
      `就绪: ${report.ready ? '是' : '否'}`,
      report.model_error ? `问题: ${report.model_error}` : '',
      report.installed_models?.length ? `已安装: ${report.installed_models.join(', ')}` : '',
      '',
      '步骤:',
      ...(report.setup_steps || []).map((s, i) => `${i + 1}. ${s}`),
    ].filter(Boolean).join('\n');
  } catch (err) {
    box.textContent = '加载失败: ' + err.message;
  }
}

async function loadDevHintsPanel() {
  const box = document.getElementById('dev-hints-panel');
  if (!box) return;
  try {
    const hints = await adminFetch('/system/dev-hints');
    box.textContent = [
      `局域网 IP: ${hints.lan_ip}`,
      `小程序 API: ${hints.suggested_api_base}`,
      `Web: ${hints.suggested_web_url}`,
      '',
      ...(hints.checklist || []),
    ].join('\n');
  } catch (err) {
    box.textContent = '加载失败: ' + err.message;
  }
}

async function loadConfig() {
  const cfg = await adminFetch('/config');
  fillConfig(cfg);
  setAuthGate('', true);
  let roleLabel = '';
  let role = '';
  try {
    const me = await adminFetch('/me');
    role = me.role || '';
    roleLabel = role ? ` · ${role}` : '';
  } catch (_) {}
  updateAdminUserLabel(role);
  setStatus('auth-status', `已连接${roleLabel}`, true);
  try {
    await loadDashboard();
    startRebuildPolling();
    loadKnowledgeFiles().catch(() => {});
    loadLlmSetupPanel().catch(() => {});
    loadDevHintsPanel().catch(() => {});
  } catch (err) {
    setStatus('auth-status', '已连接（部分数据加载失败）', true);
    console.error(err);
  }
}

function renderChunks(containerId, items, scoreKey) {
  const box = document.getElementById(containerId);
  if (!box) return;
  if (!items?.length) { box.innerHTML = '<p class="text-secondary text-sm p-4">无结果</p>'; return; }
  box.innerHTML = items.map((item, idx) => {
    const raw = item[scoreKey] ?? item.score;
    const score = raw != null ? Number(raw).toFixed(4) : '-';
    return `<div class="mb-stack-md p-stack-md border border-outline-variant rounded-xl hover:bg-surface-container">
      <div class="flex justify-between mb-2"><span class="font-data-mono text-sm">#${idx + 1} · ${score}</span><span class="text-xs text-secondary">${escapeHtml(item.category || '')}</span></div>
      <p class="font-body-sm line-clamp-4">${escapeHtml((item.content || '').slice(0, 500))}</p>
    </div>`;
  }).join('');
}

let allKnowledgeFiles = [];
let knowledgeTab = 'docs';
let caseLibraryItems = [];
let caseLibraryTotal = 0;
const CASE_LIBRARY_PAGE = 30;

function switchKnowledgeTab(tab) {
  knowledgeTab = tab;
  document.querySelectorAll('.knowledge-tab').forEach((btn) => {
    const on = btn.dataset.knowledgeTab === tab;
    btn.classList.toggle('active', on);
    btn.classList.toggle('bg-primary', on);
    btn.classList.toggle('text-on-primary', on);
    btn.classList.toggle('text-secondary', !on);
  });
  document.querySelectorAll('.knowledge-tab-panel').forEach((panel) => {
    panel.classList.toggle('active', panel.id === 'knowledge-tab-' + tab);
    panel.classList.toggle('hidden', panel.id !== 'knowledge-tab-' + tab);
  });
  if (tab === 'docs') renderKnowledgeDocs();
  if (tab === 'cases') {
    loadCaseLibraryStats().catch(() => {});
    searchCaseLibrary(false).catch(() => {});
    renderCaseFiles();
  }
  if (tab === 'index') loadKnowledgeIndexPanel().catch(() => {});
}

function escapeHtml(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeAttr(s) {
  return escapeHtml(s).replace(/'/g, '&#39;');
}

function showCaseDetailModal(detail) {
  let modal = document.getElementById('case-detail-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'case-detail-modal';
    modal.className = 'fixed inset-0 z-[100] hidden items-center justify-center bg-black/40 p-4';
    modal.innerHTML = `<div class="bg-surface max-w-lg w-full rounded-xl border border-outline-variant shadow-xl max-h-[85vh] overflow-y-auto">
      <div class="flex justify-between items-center p-4 border-b border-outline-variant">
        <h3 class="font-headline-md text-primary" id="case-modal-title">病例详情</h3>
        <button type="button" id="case-modal-close" class="text-secondary hover:text-primary text-xl">&times;</button>
      </div>
      <div id="case-modal-body" class="p-4 space-y-3 text-sm"></div>
    </div>`;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => { if (e.target === modal) closeCaseDetailModal(); });
    modal.querySelector('#case-modal-close')?.addEventListener('click', closeCaseDetailModal);
  }
  const fields = [
    ['case_id', '病例 ID'],
    ['syndrome', '证型'],
    ['diagnosis', '诊断'],
    ['symptoms', '症状'],
    ['treatment', '治法'],
    ['efficacy', '疗效'],
    ['source_file', '来源文件'],
  ];
  document.getElementById('case-modal-title').textContent = detail.case_id || detail.patient_id || '病例详情';
  document.getElementById('case-modal-body').innerHTML = fields
    .filter(([k]) => detail[k])
    .map(([k, label]) => `<div><span class="text-secondary">${label}：</span><p class="mt-1 whitespace-pre-wrap">${escapeHtml(detail[k])}</p></div>`)
    .join('') || '<p class="text-secondary">无详情</p>';
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeCaseDetailModal() {
  const modal = document.getElementById('case-detail-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

function wireAdminPlaceholderControls() {
  document.getElementById('dashboard-manage-keys-btn')?.addEventListener('click', () => switchTab('system'));
  document.querySelectorAll('[data-quick-action]').forEach((el) => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const action = el.dataset.quickAction;
      if (action === 'upload') {
        switchTab('knowledge');
        setTimeout(() => {
          switchKnowledgeTab('docs');
          document.getElementById('knowledge-import-section')?.scrollIntoView({ behavior: 'smooth' });
        }, 150);
      } else if (action === 'rag') switchTab('rag');
      else if (action === 'stats') {
        switchTab('rag');
        loadRagLogs().catch(() => {});
        document.getElementById('load-rag-stats-btn')?.click();
      } else if (action === 'audit') {
        switchTab('rag');
        loadRagLogs().catch(() => {});
      }
    });
  });
  document.getElementById('cases-view-all-btn')?.addEventListener('click', () => {
    switchTab('knowledge');
    setTimeout(() => switchKnowledgeTab('cases'), 150);
  });
  document.getElementById('rag-logs-view-all-btn')?.addEventListener('click', () => {
    switchTab('rag');
    loadRagLogs().catch(() => {});
    document.getElementById('load-rag-logs-btn')?.click();
  });
  document.getElementById('expert-mode-btn')?.addEventListener('click', () => switchTab('system'));
  document.querySelectorAll('.ui-stub-hidden').forEach((el) => el.classList.add('hidden'));
}

async function initKnowledgePanel() {
  switchKnowledgeTab(knowledgeTab || 'docs');
  const files = await adminFetch('/knowledge/files');
  allKnowledgeFiles = files.files || [];
  populateDocFilter();
  await loadKnowledgeMetrics();
  renderKnowledgeDocs();
  renderCaseFiles();
}

async function loadKnowledgeMetrics() {
  const [stats, caseStats, index] = await Promise.all([
    adminFetch('/knowledge/stats'),
    adminFetch('/knowledge/case-library/stats').catch(() => ({ file_count: 0, case_count: 0 })),
    adminFetch('/system/index-status').catch(() => ({})),
  ]);
  const docFiles = allKnowledgeFiles.filter((f) => !f.path.startsWith('cases/'));
  const totalBytes = allKnowledgeFiles.reduce((s, f) => s + (f.size_bytes || 0), 0);
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  set('kn-metric-docs', String(docFiles.length || stats.total_files || 0));
  set('kn-metric-cases', String(caseStats.case_count || 0));
  set('kn-metric-cases-sub', `${caseStats.file_count || 0} 个病例文件 · 只读参考库`);
  set('kn-metric-storage', totalBytes > 1024 * 1024 ? (totalBytes / 1024 / 1024).toFixed(1) + ' MB' : totalBytes + ' B');
  set('kn-metric-index', index.exists ? String(index.document_count ?? '已就绪') : '未构建');
}

function populateDocFilter() {
  const sel = document.getElementById('knowledge-doc-filter');
  if (!sel) return;
  const cats = [...new Set(allKnowledgeFiles.filter((f) => !f.path.startsWith('cases/')).map((f) => f.category))].sort();
  sel.innerHTML = '<option value="">全部分类</option>' + cats.map((c) => `<option value="${escapeAttr(c)}">${escapeHtml(c)}</option>`).join('');
}

function renderFileRows(files, tbodyId, onDelete) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  tbody.innerHTML = files.map((f) => `<tr class="hover:bg-surface-container-lowest">
    <td class="px-stack-md py-3"><span class="material-symbols-outlined text-primary align-middle mr-1 text-sm">description</span>${escapeHtml(f.path)}</td>
    <td class="px-stack-md py-3 font-data-mono text-secondary">${escapeHtml(String(f.size_bytes))} B</td>
    <td class="px-stack-md py-3 text-secondary">${escapeHtml(f.category || '-')}</td>
    <td class="px-stack-md py-3"><span class="bg-tertiary/10 text-tertiary px-2 py-0.5 rounded text-[10px]">已纳入索引</span></td>
    <td class="px-stack-md py-3 text-right"><button class="text-error text-sm" data-delete-path="${escapeAttr(f.path)}">删除</button></td>
  </tr>`).join('') || '<tr><td colspan="5" class="p-4 text-secondary text-sm">暂无文件</td></tr>';
  tbody.querySelectorAll('[data-delete-path]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (!confirm(`确定删除 ${btn.dataset.deletePath}？`)) return;
      await adminFetch('/knowledge/files/' + encodeURIComponent(btn.dataset.deletePath), { method: 'DELETE' });
      await initKnowledgePanel();
      if (onDelete) onDelete();
    });
  });
}

function renderKnowledgeKeywordResults(items, query) {
  const panel = document.getElementById('knowledge-keyword-results');
  if (!panel) return;
  if (!items.length) {
    panel.classList.add('hidden');
    panel.innerHTML = '';
    return;
  }
  panel.classList.remove('hidden');
  panel.innerHTML = `<p class="text-sm text-secondary mb-2">关键词「${escapeHtml(query)}」匹配 ${items.length} 条（非向量检索）</p>`
    + items.map((r, i) => `<div class="chunk bg-white border border-outline-variant rounded-xl p-3">
      <div class="text-xs text-secondary mb-1">#${i + 1} · ${escapeHtml(r.title || r.category || '片段')} · ${escapeHtml(r.file_path || r.source || '')}</div>
      <div class="text-sm whitespace-pre-wrap">${escapeHtml((r.content || '').slice(0, 400))}${(r.content || '').length > 400 ? '…' : ''}</div>
    </div>`).join('');
}

async function searchKnowledgeKeywords() {
  const q = (document.getElementById('knowledge-doc-search')?.value || '').trim();
  const panel = document.getElementById('knowledge-keyword-results');
  if (!q) {
    panel?.classList.add('hidden');
    return;
  }
  try {
    const data = await adminFetch('/knowledge/search', {
      method: 'POST',
      body: JSON.stringify({ query: q, top_k: 10 }),
    });
    renderKnowledgeKeywordResults(data.results || [], q);
    const count = document.getElementById('knowledge-doc-count');
    if (count) count.textContent = `文件名筛选 ${allKnowledgeFiles.filter((f) => !f.path.startsWith('cases/')).length} 个 · 关键词 ${(data.results || []).length} 条`;
  } catch (err) {
    if (panel) {
      panel.classList.remove('hidden');
      panel.innerHTML = `<p class="text-error text-sm">关键词搜索失败：${escapeHtml(err.message)}</p>`;
    }
  }
}

function renderKnowledgeDocs() {
  const q = (document.getElementById('knowledge-doc-search')?.value || '').trim().toLowerCase();
  const cat = document.getElementById('knowledge-doc-filter')?.value || '';
  let files = allKnowledgeFiles.filter((f) => !f.path.startsWith('cases/'));
  if (cat) files = files.filter((f) => f.category === cat);
  if (q) files = files.filter((f) => f.path.toLowerCase().includes(q) || (f.category || '').toLowerCase().includes(q));
  renderFileRows(files, 'knowledge-files-table');
  const count = document.getElementById('knowledge-doc-count');
  if (count) count.textContent = `共 ${files.length} 个文档${q || cat ? '（已筛选）' : ''}`;
  document.getElementById('knowledge-keyword-results')?.classList.add('hidden');
}

function renderCaseFiles() {
  const files = allKnowledgeFiles.filter((f) => f.path.startsWith('cases/'));
  const tbody = document.getElementById('case-files-table');
  if (!tbody) return;
  tbody.innerHTML = files.map((f) => `<tr class="hover:bg-surface-container-lowest">
    <td class="px-stack-md py-3">${f.path}</td>
    <td class="px-stack-md py-3 font-data-mono text-secondary">${f.size_bytes} B</td>
    <td class="px-stack-md py-3 text-right"><button class="text-error text-sm" data-delete-path="${f.path}">删除</button></td>
  </tr>`).join('') || '<tr><td colspan="3" class="p-4 text-secondary text-sm">暂无病例文件，请导入 JSON 到 cases/</td></tr>';
  tbody.querySelectorAll('[data-delete-path]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (!confirm(`删除病例文件 ${btn.dataset.deletePath}？`)) return;
      await adminFetch('/knowledge/files/' + encodeURIComponent(btn.dataset.deletePath), { method: 'DELETE' });
      await initKnowledgePanel();
      switchKnowledgeTab('cases');
    });
  });
}

async function loadCaseLibraryStats() {
  const el = document.getElementById('case-library-stats');
  if (!el) return;
  try {
    const stats = await adminFetch('/knowledge/case-library/stats');
    el.textContent = `病例库：${stats.file_count} 个 JSON 文件，共 ${stats.case_count} 条临床案例（RAG 参考资料，非患者档案）`;
  } catch (err) {
    el.textContent = `病例库统计加载失败：${err.message}（请重启服务：python3 web_server.py）`;
  }
}

async function searchCaseLibrary(append) {
  const q = document.getElementById('case-library-search')?.value.trim() || '';
  const tbody = document.getElementById('case-library-table');
  const count = document.getElementById('case-library-count');
  try {
    if (!append) caseLibraryItems = [];
    const offset = caseLibraryItems.length;
    const data = await adminFetch(`/knowledge/case-library?limit=${CASE_LIBRARY_PAGE}&offset=${offset}&q=${encodeURIComponent(q)}`);
    caseLibraryTotal = data.total || 0;
    caseLibraryItems = append ? caseLibraryItems.concat(data.cases || []) : (data.cases || []);
    if (!tbody) return;
    tbody.innerHTML = caseLibraryItems.map((c) => `<tr class="hover:bg-surface-container-lowest cursor-pointer" data-case-id="${escapeAttr(c.case_id || c.patient_id)}">
      <td class="px-stack-md py-3 font-data-mono">${escapeHtml(c.case_id || c.patient_id)}</td>
      <td class="px-stack-md py-3">${escapeHtml(c.syndrome || c.diagnosis || '—')}</td>
      <td class="px-stack-md py-3">${escapeHtml(c.gender || '-')} · ${escapeHtml(String(c.age ?? '-'))}岁</td>
      <td class="px-stack-md py-3 text-secondary text-xs">${escapeHtml(c.source_file)}</td>
      <td class="px-stack-md py-3 text-secondary">${escapeHtml((c.symptoms || '').slice(0, 40))}</td>
    </tr>`).join('') || `<tr><td colspan="5" class="p-4 text-secondary text-sm">无匹配病例${q ? '，可尝试「头痛」等同义词' : ''}</td></tr>`;
    tbody.querySelectorAll('[data-case-id]').forEach((row) => {
      row.addEventListener('click', async () => {
        const detail = await adminFetch('/knowledge/case-library/' + encodeURIComponent(row.dataset.caseId));
        showCaseDetailModal(detail);
      });
    });
    if (count) count.textContent = `显示 ${caseLibraryItems.length} / ${caseLibraryTotal} 条`;
    const more = document.getElementById('load-more-cases-btn');
    if (more) {
      more.classList.toggle('hidden', caseLibraryItems.length >= caseLibraryTotal);
      more.onclick = () => searchCaseLibrary(true).catch(() => {});
    }
  } catch (err) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-error text-sm">搜索失败：${escapeHtml(err.message)}（若提示 Not Found 请重启 python3 web_server.py）</td></tr>`;
    if (count) count.textContent = '—';
  }
}

async function loadKnowledgeIndexPanel() {
  const index = await adminFetch('/system/index-status');
  const stats = await adminFetch('/knowledge/stats');
  const summary = document.getElementById('knowledge-index-summary');
  if (summary) {
    summary.innerHTML = [
      `<p>索引路径：<code class="text-xs">${index.index_path || '—'}</code></p>`,
      `<p>状态：<strong>${index.exists ? '已构建' : '未构建'}</strong></p>`,
      index.document_count != null ? `<p>向量分块数：${index.document_count}</p>` : '',
      index.last_modified ? `<p>最后更新：${index.last_modified}</p>` : '',
      `<p>Embedding：${index.embedding_provider} / ${index.embedding_model}</p>`,
    ].filter(Boolean).join('');
  }
  const detail = document.getElementById('knowledge-index-detail');
  if (detail) detail.textContent = JSON.stringify(index, null, 2);
  const health = document.getElementById('knowledge-health-summary');
  if (health) {
    const cats = Object.entries(stats.by_category || {}).map(([k, v]) => `${k}: ${v}`).join(' · ');
    health.innerHTML = `<p>知识库目录文件：${stats.total_files}</p><p>分类分布：${cats || '—'}</p><p class="text-xs text-secondary mt-2">修改 cases/ 或文档后请重建索引以同步 RAG。</p>`;
  }
}

async function loadKnowledgeFiles() {
  await initKnowledgePanel();
}

let allPatients = [];
let selectedPatientId = null;
let editingPatientId = null;
let patientTotal = 0;
const PATIENT_PAGE = 100;

function patientDisplayTitle(p) {
  return p.name || p.patient_id;
}

function renderPatientCard(p, active) {
  const title = escapeHtml(patientDisplayTitle(p));
  const initial = escapeHtml((p.name || p.gender || '?').slice(0, 1));
  return `<div class="patient-card bg-surface rounded-[15px] p-4 card-shadow border-l-4 ${active ? 'border-primary active' : 'border-outline-variant opacity-80'} transition-all cursor-pointer hover:bg-surface-container-low" data-patient-id="${escapeAttr(p.patient_id)}">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-full bg-primary-container/20 text-primary flex items-center justify-center font-bold">${initial}</div>
      <div class="flex-1 min-w-0">
        <div class="flex justify-between items-start gap-2">
          <p class="font-bold text-on-surface truncate">${title}</p>
          <span class="text-outline text-[10px] shrink-0">${escapeHtml(p.status || 'active')}</span>
        </div>
        <p class="text-on-surface-variant text-[13px] truncate">${escapeHtml(p.patient_id)} · ${escapeHtml(p.gender || '-')} · ${escapeHtml(String(p.age ?? '-'))}岁 · ${escapeHtml(p.phone || '无电话')}</p>
      </div>
    </div>
  </div>`;
}

async function loadPatients(query, append) {
  const q = query ?? document.getElementById('patient-search')?.value.trim() ?? '';
  if (!append) allPatients = [];
  const offset = append ? allPatients.length : 0;
  let path = `/patients?limit=${PATIENT_PAGE}&offset=${offset}`;
  if (q) path += '&q=' + encodeURIComponent(q);
  const data = await adminFetch(path);
  patientTotal = data.total || 0;
  allPatients = append ? allPatients.concat(data.patients || []) : (data.patients || []);
  const list = document.getElementById('patient-list');
  const meta = document.getElementById('patient-list-meta');
  if (!list) return;
  if (!allPatients.length) {
    list.innerHTML = '<p class="text-secondary text-sm p-4">暂无患者，点击「新建患者」添加</p>';
    if (meta) meta.textContent = '共 0 人';
    return;
  }
  list.innerHTML = allPatients.map((p) => renderPatientCard(p, p.patient_id === selectedPatientId)).join('');
  if (meta) {
    meta.textContent = `显示 ${allPatients.length} / ${patientTotal} 人${q ? '（已筛选）' : ''}`;
    if (patientTotal > allPatients.length) {
      meta.innerHTML = `${meta.textContent} · <button type="button" id="load-more-patients" class="text-primary underline">加载更多</button>`;
      document.getElementById('load-more-patients')?.addEventListener('click', () => loadPatients(q, true));
    }
  }
  list.querySelectorAll('[data-patient-id]').forEach((el) => {
    el.addEventListener('click', () => selectPatient(el.dataset.patientId));
  });
  if (selectedPatientId && allPatients.some((p) => p.patient_id === selectedPatientId)) {
    selectPatient(selectedPatientId, false);
  }
}

async function selectPatient(patientId, scroll) {
  selectedPatientId = patientId;
  document.querySelectorAll('.patient-card').forEach((el) => {
    const on = el.dataset.patientId === patientId;
    el.classList.toggle('border-primary', on);
    el.classList.toggle('active', on);
    el.classList.toggle('border-outline-variant', !on);
    el.classList.toggle('opacity-80', !on);
  });
  const p = await adminFetch('/patients/' + encodeURIComponent(patientId));
  const visits = await adminFetch('/patients/' + encodeURIComponent(patientId) + '/visits');
  document.getElementById('patient-detail-empty')?.classList.add('hidden');
  document.getElementById('patient-detail-content')?.classList.remove('hidden');
  const title = document.getElementById('patient-detail-title');
  if (title) title.textContent = patientDisplayTitle(p);
  const meta = document.getElementById('patient-detail-meta');
  if (meta) {
    meta.innerHTML = [
      `<span>ID: ${escapeHtml(p.patient_id)}</span>`,
      p.gender ? `<span>${escapeHtml(p.gender)}</span>` : '',
      p.age != null ? `<span>${escapeHtml(String(p.age))}岁</span>` : '',
      p.phone ? `<span>${escapeHtml(p.phone)}</span>` : '',
      p.address ? `<span>${escapeHtml(p.address)}</span>` : '',
    ].filter(Boolean).join('');
  }
  const symptoms = document.getElementById('patient-detail-symptoms');
  if (symptoms) {
    symptoms.textContent = [
      p.constitution ? `体质：${p.constitution}` : '',
      p.allergies ? `过敏：${p.allergies}` : '',
      p.notes ? `备注：${p.notes}` : '',
    ].filter(Boolean).join('\n') || '—';
  }
  const treatment = document.getElementById('patient-detail-treatment');
  if (treatment) treatment.textContent = p.id_number ? `证件：${p.id_number}` : '—';
  const actions = document.getElementById('patient-detail-actions');
  if (actions) {
    actions.innerHTML = `<button type="button" id="edit-patient-btn" class="border border-outline-variant px-4 py-2 rounded-full text-sm">编辑档案</button>
      <button type="button" id="add-visit-btn" class="bg-primary text-on-primary px-4 py-2 rounded-full text-sm">新增就诊</button>
      <button type="button" id="delete-patient-btn" class="text-error border border-error/30 px-4 py-2 rounded-full text-sm">删除</button>`;
    document.getElementById('edit-patient-btn')?.addEventListener('click', () => openPatientForm(p));
    document.getElementById('add-visit-btn')?.addEventListener('click', () => openVisitForm(patientId));
    document.getElementById('delete-patient-btn')?.addEventListener('click', () => deletePatient(p.patient_id));
  }
  const tbody = document.getElementById('patient-history-body');
  if (tbody) {
    tbody.innerHTML = (visits.visits || []).map((v) => `<tr class="hover:bg-surface-container-lowest">
      <td class="px-6 py-4 whitespace-nowrap">${escapeHtml(v.visit_date || '—')}</td>
      <td class="px-6 py-4 text-on-surface-variant">${escapeHtml((v.chief_complaint || v.symptoms || '').slice(0, 40))}</td>
      <td class="px-6 py-4"><span class="bg-surface-container px-3 py-1 rounded-full text-[12px] text-primary">${escapeHtml(v.syndrome || '—')}</span></td>
      <td class="px-6 py-4 text-[13px]">${escapeHtml((v.efficacy || '—').slice(0, 30))}</td>
      <td class="px-6 py-4 text-right text-xs text-secondary">${escapeHtml(v.source || 'manual')}</td>
    </tr>`).join('') || '<tr><td colspan="5" class="px-6 py-8 text-center text-secondary">暂无就诊记录</td></tr>';
  }
  if (scroll !== false) document.getElementById('patient-detail-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function clearPatientForm() {
  editingPatientId = null;
  document.getElementById('patient-form-panel')?.classList.add('hidden');
  ['pf-name', 'pf-gender', 'pf-age', 'pf-phone', 'pf-id-number', 'pf-address', 'pf-constitution', 'pf-allergies', 'pf-notes'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  const title = document.getElementById('patient-form-title');
  if (title) title.textContent = '新建患者';
}

function openPatientForm(p) {
  const panel = document.getElementById('patient-form-panel');
  panel?.classList.remove('hidden');
  panel?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  if (p) {
    editingPatientId = p.patient_id;
    document.getElementById('patient-form-title').textContent = '编辑患者 · ' + p.name;
    document.getElementById('pf-name').value = p.name || '';
    document.getElementById('pf-gender').value = p.gender || '';
    document.getElementById('pf-age').value = p.age ?? '';
    document.getElementById('pf-phone').value = p.phone || '';
    document.getElementById('pf-id-number').value = p.id_number || '';
    document.getElementById('pf-address').value = p.address || '';
    document.getElementById('pf-constitution').value = p.constitution || '';
    document.getElementById('pf-allergies').value = p.allergies || '';
    document.getElementById('pf-notes').value = p.notes || '';
  } else {
    clearPatientForm();
    panel?.classList.remove('hidden');
  }
}

async function savePatientForm() {
  const payload = {
    name: document.getElementById('pf-name').value.trim(),
    gender: document.getElementById('pf-gender').value.trim(),
    phone: document.getElementById('pf-phone').value.trim(),
    id_number: document.getElementById('pf-id-number').value.trim(),
    address: document.getElementById('pf-address').value.trim(),
    constitution: document.getElementById('pf-constitution').value.trim(),
    allergies: document.getElementById('pf-allergies').value.trim(),
    notes: document.getElementById('pf-notes').value.trim(),
  };
  const age = document.getElementById('pf-age').value;
  if (age) payload.age = parseInt(age, 10);
  if (!payload.name) return alert('请填写姓名');
  try {
    if (editingPatientId) {
      await adminFetch('/patients/' + encodeURIComponent(editingPatientId), { method: 'PUT', body: JSON.stringify(payload) });
      setStatus('patient-status', '已更新', true);
      selectedPatientId = editingPatientId;
    } else {
      const created = await adminFetch('/patients', { method: 'POST', body: JSON.stringify(payload) });
      setStatus('patient-status', '已创建', true);
      selectedPatientId = created.patient_id;
    }
    clearPatientForm();
    await loadPatients();
    if (selectedPatientId) await selectPatient(selectedPatientId, false);
  } catch (err) {
    setStatus('patient-status', err.message, false);
  }
}

async function deletePatient(patientId) {
  if (!confirm(`确定删除患者 ${patientId}？就诊记录将一并删除。`)) return;
  await adminFetch('/patients/' + encodeURIComponent(patientId), { method: 'DELETE' });
  selectedPatientId = null;
  document.getElementById('patient-detail-content')?.classList.add('hidden');
  document.getElementById('patient-detail-empty')?.classList.remove('hidden');
  await loadPatients();
}

function openVisitForm(patientId) {
  selectedPatientId = patientId;
  document.getElementById('visit-form-panel')?.classList.remove('hidden');
  ['vf-date', 'vf-complaint', 'vf-diagnosis', 'vf-syndrome', 'vf-symptoms', 'vf-treatment', 'vf-efficacy'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  document.getElementById('vf-date').value = new Date().toISOString().slice(0, 10);
}

async function saveVisitForm() {
  if (!selectedPatientId) return;
  const payload = {
    visit_date: document.getElementById('vf-date').value.trim(),
    chief_complaint: document.getElementById('vf-complaint').value.trim(),
    diagnosis: document.getElementById('vf-diagnosis').value.trim(),
    syndrome: document.getElementById('vf-syndrome').value.trim(),
    symptoms: document.getElementById('vf-symptoms').value.trim(),
    treatment: document.getElementById('vf-treatment').value.trim(),
    efficacy: document.getElementById('vf-efficacy').value.trim(),
  };
  await adminFetch('/patients/' + encodeURIComponent(selectedPatientId) + '/visits', { method: 'POST', body: JSON.stringify(payload) });
  document.getElementById('visit-form-panel')?.classList.add('hidden');
  await selectPatient(selectedPatientId, false);
}

let rebuildPollTimer = null;

function updateRebuildProgress(status) {
  const panel = document.getElementById('rebuild-progress-panel');
  const bar = document.getElementById('rebuild-progress-bar');
  const meta = document.getElementById('rebuild-progress-meta');
  const btn = document.getElementById('rebuild-index-btn');
  const progress = status.progress || 0;
  if (status.status === 'idle' && !status.job_id) {
    panel?.classList.add('hidden');
    if (btn) btn.disabled = false;
    return;
  }
  panel?.classList.remove('hidden');
  if (bar) { bar.style.width = progress + '%'; bar.textContent = progress + '%'; }
  if (meta) meta.textContent = `[${status.phase || status.status}] ${status.message || ''}`;
  if (btn) btn.disabled = status.status === 'running';
  if (status.status === 'completed') setStatus('system-status', status.message || '完成', true);
  if (status.status === 'failed') setStatus('system-status', status.error || '失败', false);
}

async function pollRebuildStatus() {
  const status = await adminFetch('/rag/rebuild-index/status');
  updateRebuildProgress(status);
  if (status.status === 'running') rebuildPollTimer = setTimeout(pollRebuildStatus, 1000);
}

function startRebuildPolling() {
  if (rebuildPollTimer) clearTimeout(rebuildPollTimer);
  pollRebuildStatus().catch(() => {});
}

function providerPayload(prefix) {
  const payload = {
    provider: document.getElementById(prefix + '-provider')?.value,
    model: document.getElementById(prefix + '-model')?.value.trim(),
    base_url: document.getElementById(prefix + '-base-url')?.value.trim(),
  };
  const key = document.getElementById(prefix + '-api-key')?.value;
  if (key) payload.api_key = key;
  if (prefix === 'llm') payload.temperature = parseFloat(document.getElementById('llm-temperature')?.value || '0.3');
  if (prefix === 'rerank') payload.top_n = parseInt(document.getElementById('rerank-top-n')?.value || '5', 10);
  return payload;
}

async function runProviderTest(endpoint, prefix, resultId) {
  const result = await adminFetch(endpoint, { method: 'POST', body: JSON.stringify(providerPayload(prefix)) });
  const el = document.getElementById(resultId);
  if (el) { el.classList.remove('hidden'); el.textContent = JSON.stringify(result, null, 2); }
  return result;
}

async function loadRagLogs() {
  const source = document.getElementById('rag-log-source')?.value || '';
  const kind = document.getElementById('rag-log-kind')?.value || '';
  let path = '/rag/logs?limit=30';
  if (source) path += '&source=' + encodeURIComponent(source);
  if (kind) path += '&kind=' + encodeURIComponent(kind);
  const data = await adminFetch(path);
  const box = document.getElementById('rag-logs');
  if (!box) return;
  box.innerHTML = data.logs.map((log) => `<div class="border-b border-outline-variant/30 py-2 text-xs">
    <div class="font-data-mono">${escapeHtml(log.timestamp)} · ${escapeHtml(log.kind)} · ${escapeHtml(String(log.duration_ms))}ms</div>
    <div>${escapeHtml((log.question || '').slice(0, 80))}</div>
  </div>`).join('') || '<p class="text-secondary">暂无日志</p>';
}

function bind(id, event, fn) {
  const el = document.getElementById(id);
  if (el) el.addEventListener(event, fn);
}

document.querySelectorAll('.tab').forEach((btn) => btn.addEventListener('click', () => switchTab(btn.dataset.tab)));

bind('login-form', 'submit', (e) => {
  e.preventDefault();
  attemptLogin().catch(() => {});
});

bind('login-key-toggle', 'click', () => {
  const input = document.getElementById('login-api-key');
  const toggle = document.getElementById('login-key-toggle');
  if (!input || !toggle) return;
  const show = input.type === 'password';
  input.type = show ? 'text' : 'password';
  toggle.textContent = show ? 'visibility_off' : 'visibility';
});

bind('login-help-btn', 'click', () => {
  alert(
    'Admin API Key 配置位置：\n\n' +
      '1. 打开项目 data/admin_config.json\n' +
      '2. 复制 admin_api_key 字段的值\n' +
      '3. 若启用 RBAC，也可使用 rbac.keys 中的附加 Key\n\n' +
      '开发环境首次运行会自动从 admin_config.example.json 生成配置。'
  );
});

bind('logout-btn', 'click', () => {
  if (confirm('确定退出管理端？')) logoutAdmin();
});

bind('save-key-btn', 'click', () => {
  const key = document.getElementById('api-key-input')?.value.trim();
  if (!key) return alert('请输入 API Key');
  attemptLogin({ key }).catch((err) => setAuthGate('连接失败：' + err.message, false));
});

bind('test-key-btn', 'click', () => {
  loadConfig().catch((err) => setAuthGate('连接失败：' + err.message, false));
});

bind('save-emb-btn', 'click', async () => { await savePartialConfig('embedding'); setStatus('system-status', 'Embedding 已保存', true); loadDashboard().catch(() => {}); });
bind('save-llm-btn', 'click', async () => { await savePartialConfig('llm'); setStatus('system-status', 'LLM 已保存', true); loadDashboard().catch(() => {}); });
bind('save-rerank-btn', 'click', async () => { await savePartialConfig('rerank'); setStatus('system-status', 'Rerank 已保存', true); loadDashboard().catch(() => {}); });
bind('save-config-btn', 'click', async () => { await adminFetch('/config', { method: 'PUT', body: JSON.stringify(collectConfig()) }); setStatus('system-status', '配置已保存', true); });

bind('save-wx-config-btn', 'click', async () => {
  try {
    await adminFetch('/config', { method: 'PUT', body: JSON.stringify({ wechat_miniprogram: collectWxConfig() }) });
    setStatus('wx-config-status', '微信配置已保存（重启后 dev_mode/token 变更完全生效）', true);
    const cfg = await adminFetch('/config');
    fillConfig(cfg);
  } catch (err) {
    setStatus('wx-config-status', err.message, false);
  }
});

bind('refresh-llm-setup-btn', 'click', () => loadLlmSetupPanel().catch((e) => setStatus('system-status', e.message, false)));
bind('refresh-dev-hints-btn', 'click', () => loadDevHintsPanel().catch((e) => setStatus('system-status', e.message, false)));
bind('pull-llm-model-btn', 'click', async () => {
  try {
    const r = await adminFetch('/system/llm-pull', { method: 'POST' });
    setStatus('system-status', r.message || '模型拉取完成', true);
    await loadLlmSetupPanel();
  } catch (err) {
    setStatus('system-status', err.message, false);
  }
});

bind('test-emb-btn', 'click', () => runProviderTest('/system/test-embedding', 'emb', 'emb-test-result').catch((e) => setStatus('system-status', e.message, false)));
bind('test-llm-btn', 'click', () => runProviderTest('/system/test-llm', 'llm', 'llm-test-result').catch((e) => setStatus('system-status', e.message, false)));
bind('test-rerank-btn', 'click', () => runProviderTest('/system/test-rerank', 'rerank', 'rerank-test-result').catch((e) => setStatus('system-status', e.message, false)));
bind('test-models-btn', 'click', async () => {
  const r = await adminFetch('/system/test-models', { method: 'POST' });
  const el = document.getElementById('model-test-result');
  if (el) { el.classList.remove('hidden'); el.textContent = JSON.stringify(r, null, 2); }
  setStatus('system-status', r.all_ok ? '模型正常' : '部分失败', r.all_ok);
});

bind('rebuild-index-btn', 'click', async () => {
  if (!confirm('确定异步重建向量索引？')) return;
  const result = await adminFetch('/rag/rebuild-index/async?force=true', { method: 'POST' });
  updateRebuildProgress(result);
  startRebuildPolling();
});

bind('rebuild-index-sync-btn', 'click', async () => {
  if (!confirm('同步重建会阻塞请求，仅建议小数据量调试。继续？')) return;
  setStatus('system-status', '同步重建中…', true);
  try {
    const result = await adminFetch('/rag/rebuild-index?force=true', { method: 'POST' });
    setStatus('system-status', `同步完成：${result.chunks || 0} chunks`, true);
    loadKnowledgeIndexPanel().catch(() => {});
  } catch (err) {
    setStatus('system-status', err.message, false);
  }
});

bind('regen-key-btn', 'click', async () => {
  if (!confirm('重新生成 Key？旧 Key 立即失效')) return;
  const result = await adminFetch('/config/regenerate-key', { method: 'POST' });
  const newKey = result.admin_api_key;
  syncHiddenApiKeyInput('');
  const apiKeyInput = document.getElementById('api-key-input');
  if (apiKeyInput) apiKeyInput.value = '';
  const loginKey = document.getElementById('login-api-key');
  if (loginKey) loginKey.value = '';
  await fetch('/api/admin/session/logout', { method: 'POST', credentials: 'include' }).catch(() => {});
  await attemptLogin({ key: newKey });
  alert(
    '新 Admin Key 已生效。\n\n请立即复制保存（关闭此对话框后页面不再显示完整 Key）：\n\n' + newKey
  );
  setStatus('system-status', 'Admin Key 已轮换，请妥善保管', true);
});

bind('import-files-btn', 'click', async () => {
  const input = document.getElementById('import-files');
  if (!input?.files?.length) return alert('请选择文件');
  const fd = new FormData();
  for (const f of input.files) fd.append('files', f);
  fd.append('subdir', document.getElementById('import-subdir').value.trim() || 'cases');
  fd.append('overwrite', document.getElementById('import-overwrite').checked ? 'true' : 'false');
  const result = await adminUploadFiles('/knowledge/import-files', fd);
  const el = document.getElementById('import-result');
  if (el) { el.classList.remove('hidden'); el.textContent = JSON.stringify(result, null, 2); }
  await initKnowledgePanel();
  switchKnowledgeTab((document.getElementById('import-subdir')?.value.trim() || '').startsWith('cases') ? 'cases' : 'docs');
});

bind('upload-knowledge-btn', 'click', async () => {
  await adminFetch('/knowledge/upload', {
    method: 'POST',
    body: JSON.stringify({
      path: document.getElementById('upload-path').value.trim(),
      content: document.getElementById('upload-content').value,
      overwrite: document.getElementById('upload-overwrite').checked,
    }),
  });
  setStatus('system-status', '上传成功', true);
  await initKnowledgePanel();
});

document.querySelectorAll('.knowledge-tab').forEach((btn) => {
  btn.addEventListener('click', () => switchKnowledgeTab(btn.dataset.knowledgeTab));
});

bind('knowledge-doc-search', 'input', () => renderKnowledgeDocs());
bind('knowledge-doc-search', 'keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    searchKnowledgeKeywords().catch(() => {});
  }
});
bind('knowledge-keyword-search-btn', 'click', () => searchKnowledgeKeywords().catch(() => {}));
bind('knowledge-doc-filter', 'change', () => renderKnowledgeDocs());
bind('search-case-library-btn', 'click', () => searchCaseLibrary(false).catch((e) => setStatus('system-status', e.message, false)));
bind('knowledge-refresh-index-btn', 'click', () => loadKnowledgeIndexPanel().catch(() => {}));
bind('knowledge-rebuild-index-btn', 'click', async () => {
  if (!confirm('确定重建向量索引？')) return;
  await adminFetch('/rag/rebuild-index/async?force=true', { method: 'POST' });
  setStatus('system-status', '索引重建已启动', true);
  loadKnowledgeIndexPanel().catch(() => {});
});
bind('knowledge-sync-index-btn', 'click', async () => {
  switchKnowledgeTab('index');
  await loadKnowledgeIndexPanel();
  if (!confirm('立即重建向量索引以同步最新文件？')) return;
  await adminFetch('/rag/rebuild-index/async?force=true', { method: 'POST' });
  setStatus('system-status', '索引重建已启动', true);
});
bind('knowledge-goto-import-btn', 'click', () => {
  document.getElementById('knowledge-import-section')?.scrollIntoView({ behavior: 'smooth' });
});

const caseSearchInput = document.getElementById('case-library-search');
if (caseSearchInput) {
  let t;
  caseSearchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') searchCaseLibrary(false).catch(() => {});
  });
  caseSearchInput.addEventListener('input', () => {
    clearTimeout(t);
    t = setTimeout(() => searchCaseLibrary(false).catch(() => {}), 400);
  });
}

bind('refresh-patients-btn', 'click', () => loadPatients().catch((e) => setStatus('patient-status', e.message, false)));
bind('new-patient-btn', 'click', () => openPatientForm(null));
bind('pf-save-btn', 'click', () => savePatientForm());
bind('pf-cancel-btn', 'click', clearPatientForm);
bind('vf-save-btn', 'click', () => saveVisitForm().catch((e) => setStatus('patient-status', e.message, false)));
bind('vf-cancel-btn', 'click', () => document.getElementById('visit-form-panel')?.classList.add('hidden'));

const patientSearch = document.getElementById('patient-search');
if (patientSearch) {
  let searchTimer;
  patientSearch.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadPatients().catch(() => {}), 300);
  });
}

bind('load-index-status-btn', 'click', async () => {
  const s = await adminFetch('/system/index-status');
  const el = document.getElementById('index-status');
  if (el) el.textContent = JSON.stringify(s, null, 2);
});

bind('load-rag-stats-btn', 'click', async () => {
  const s = await adminFetch('/rag/logs/stats');
  const el = document.getElementById('rag-stats');
  if (el) el.textContent = JSON.stringify(s, null, 2);
});

bind('load-rag-logs-btn', 'click', () => loadRagLogs().catch(() => {}));
bind('rag-log-source', 'change', () => loadRagLogs().catch(() => {}));
bind('rag-log-kind', 'change', () => loadRagLogs().catch(() => {}));
bind('clear-rag-logs-btn', 'click', async () => { if (confirm('清空日志？')) { await adminFetch('/rag/logs', { method: 'DELETE' }); loadRagLogs(); } });

bind('clear-rag-btn', 'click', () => {
  const q = document.getElementById('question');
  const ans = document.getElementById('rag-answer');
  if (q) q.value = '';
  if (ans) ans.textContent = '等待查询…';
  ['rag-retrieved', 'rag-reranked'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '';
  });
  const dur = document.getElementById('rag-duration');
  if (dur) dur.textContent = '—';
  const tok = document.getElementById('rag-token-estimate');
  if (tok) tok.textContent = '—';
  const hint = document.getElementById('rag-providers-hint');
  if (hint) hint.textContent = '';
});

bind('llm-key-toggle-btn', 'click', () => {
  const input = document.getElementById('llm-api-key');
  if (!input) return;
  input.type = input.type === 'password' ? 'text' : 'password';
});

wireAdminPlaceholderControls();

bind('run-rag-btn', 'click', async () => {
  const question = document.getElementById('question')?.value.trim();
  if (!question) return alert('请输入问题');
  const payload = { question, enable_llm_answer: document.getElementById('enable-llm')?.checked !== false };
  const rtk = document.getElementById('retrieval-top-k')?.value;
  const ftk = document.getElementById('final-top-k')?.value;
  if (rtk) payload.retrieval_top_k = parseInt(rtk, 10);
  if (ftk) payload.final_top_k = parseInt(ftk, 10);
  setStatus('rag-status', '检索中…', true);
  const result = await adminFetch('/rag/query', { method: 'POST', body: JSON.stringify(payload) });
  const ans = document.getElementById('rag-answer');
  if (ans) ans.textContent = result.answer || '（未生成）';
  renderChunks('rag-reranked', result.reranked, 'rerank_score');
  renderChunks('rag-retrieved', result.retrieved, 'score');
  const dur = document.getElementById('rag-duration');
  if (dur) dur.textContent = result.duration_ms != null ? `${(result.duration_ms / 1000).toFixed(2)}s` : '—';
  const tok = document.getElementById('rag-token-estimate');
  if (tok) tok.textContent = result.token_estimate != null ? `~${result.token_estimate} tokens` : '—';
  const hint = document.getElementById('rag-providers-hint');
  if (hint && result.providers) {
    hint.textContent = `emb:${result.providers.embedding || '-'} · llm:${result.providers.llm || '-'} · rerank:${result.providers.rerank || '-'}`;
  }
  setStatus('rag-status', `完成 · ${result.retrieved_count} 条`, true);
  loadRagLogs().catch(() => {});
});

const savedName = getStoredDisplayName();
if (savedName) {
  const loginAccount = document.getElementById('login-account');
  if (loginAccount) loginAccount.value = savedName;
}
loadConfig().catch(() => setAuthGate('', false));

async function loadBranding() {
  try {
    const res = await fetch('/api/public/branding');
    if (!res.ok) return;
    const b = await res.json();
    const mp = b.miniprogram?.shortName || b.miniprogram?.name || '御心调理';
    const product = b.productName || 'ZenPulse AI';
    const tagline = b.tagline ? `${product} · ${b.tagline}` : `${product} 智慧中医管理后台`;
    const title = document.getElementById('admin-brand-title');
    if (title) title.textContent = `${product} · 管理端`;
    const loginTitle = document.getElementById('login-brand-title');
    if (loginTitle) loginTitle.textContent = product;
    const loginTagline = document.getElementById('login-tagline');
    if (loginTagline) loginTagline.textContent = `欢迎使用 ${tagline}`;
    const hint = document.getElementById('admin-mp-hint');
    if (hint) hint.innerHTML = `<span class="material-symbols-outlined text-base">smartphone</span>${mp}`;
    const sideMp = document.getElementById('sidebar-mp-name');
    if (sideMp) sideMp.textContent = `微信小程序 · ${mp}`;
  } catch (_) {}
}

loadBranding();
