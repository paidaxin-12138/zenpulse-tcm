// api.js - API调用工具类

import { API_ENV } from '../config/env';
import { getAppSafe } from './appContext';

const BASE_URL_STORAGE_KEY = 'zp_api_base_url';

function getBaseUrl() {
  const app = getAppSafe();
  if (app && app.globalData && app.globalData.baseUrl) {
    return app.globalData.baseUrl;
  }
  const cached = wx.getStorageSync(BASE_URL_STORAGE_KEY);
  if (cached) return cached;
  if (API_ENV.customBaseUrl) return API_ENV.customBaseUrl;
  return API_ENV.baseUrlCandidates[0];
}

function setBaseUrl(url) {
  if (!url) return;
  wx.setStorageSync(BASE_URL_STORAGE_KEY, url);
  const app = getAppSafe();
  if (app && app.globalData) app.globalData.baseUrl = url;
}

function probeBaseUrl(baseUrl) {
  const timeout = API_ENV.probeTimeoutMs || 4000;
  const root = baseUrl.replace(/\/$/, '');
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${root}/public/branding`,
      method: 'GET',
      timeout,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(baseUrl);
        else reject(new Error(`HTTP ${res.statusCode}`));
      },
      fail: reject
    });
  });
}

/** 启动时探测可用后端地址 */
export function bootstrapServer(appRef) {
  const app = appRef || getAppSafe();
  const candidates = [
    API_ENV.customBaseUrl,
    app && app.globalData && app.globalData.baseUrl,
    wx.getStorageSync(BASE_URL_STORAGE_KEY),
    ...(API_ENV.baseUrlCandidates || [])
  ].filter(Boolean);

  const unique = [...new Set(candidates.map((u) => u.replace(/\/$/, '')))];

  const tryNext = (index) => {
    if (index >= unique.length) {
      if (app && app.globalData) app.globalData.serverReachable = false;
      return Promise.resolve(false);
    }
    const base = unique[index];
    return probeBaseUrl(base)
      .then((okUrl) => {
        setBaseUrl(okUrl);
        if (app && app.globalData) {
          app.globalData.baseUrl = okUrl;
          app.globalData.serverReachable = true;
        }
        console.log('[API] 后端已连接:', okUrl);
        return true;
      })
      .catch(() => tryNext(index + 1));
  };

  return tryNext(0);
}

export function formatRequestError(err, url = '') {
  const msg = (err && (err.errMsg || err.message)) || String(err || '');
  if (/timeout/i.test(msg)) {
    const hint = getBaseUrl().includes('localhost')
      ? '真机请把 config/env.js 的 baseUrl 改成本机局域网 IP'
      : '请确认 python3 web_server.py 已启动且地址正确';
    return new Error(`请求超时（${url || 'API'}）。${hint}`);
  }
  if (/fail|connect|refused|network|域名|url/i.test(msg)) {
    return new Error(`无法连接服务器（${getBaseUrl()}）。请先启动后端并检查 baseUrl 配置`);
  }
  return err instanceof Error ? err : new Error(msg || '请求失败');
}

/**
 * 通用请求方法
 */
function request(url, data = {}, method = 'GET', header = {}, options = {}) {
  const timeout = options.timeout || API_ENV.defaultTimeoutMs;
  const fullUrl = getBaseUrl() + url;

  return new Promise((resolve, reject) => {
    wx.request({
      url: fullUrl,
      data,
      method,
      timeout,
      header: {
        'content-type': 'application/json',
        ...header
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
          return;
        }
        const detail = res.data && (res.data.detail || res.data.message);
        reject(new Error(typeof detail === 'string' ? detail : `请求失败: ${res.statusCode}`));
      },
      fail(err) {
        reject(formatRequestError(err, url));
      }
    });
  });
}

/** 探测当前 baseUrl 是否可达 */
export function pingServer() {
  return request('/public/branding', {}, 'GET', {}, { timeout: API_ENV.probeTimeoutMs || 4000 })
    .then(() => true)
    .catch(() => false);
}

export { request };

/**
 * 获取健康指标
 */
export function getHealthMetrics() {
  return request('/health-metrics');
}

function compressImagePath(filePath, quality) {
  return new Promise((resolve) => {
    wx.compressImage({
      src: filePath,
      quality: quality || 30,
      success: (res) => resolve(res.tempFilePath || filePath),
      fail: () => resolve(filePath)
    });
  });
}

async function compressForUpload(filePath) {
  let path = await compressImagePath(filePath, 30);
  try {
    const stat = wx.getFileSystemManager().statSync(path);
    if (stat.size > 400 * 1024) {
      path = await compressImagePath(path, 18);
    }
  } catch (_) {
    /* ignore */
  }
  return path;
}

/**
 * 将图片转换为base64（先压缩，减小超时风险）
 */
export async function getImageBase64(filePath) {
  const compressed = await compressForUpload(filePath);
  return new Promise((resolve, reject) => {
    wx.getFileSystemManager().readFile({
      filePath: compressed,
      encoding: 'base64',
      success(res) {
        resolve('data:image/jpeg;base64,' + res.data);
      },
      fail(err) {
        reject(formatRequestError(err, 'readFile'));
      }
    });
  });
}

/**
 * 微信小程序诊断（JSON + base64 多图）
 */
export async function wxDiagnose(formData, files, authHeader = {}) {
  const payload = {
    heart_rate: parseInt(formData.heartRate, 10),
    pulse: parseInt(formData.pulse, 10),
    systolic: parseInt(formData.systolic, 10),
    diastolic: parseInt(formData.diastolic, 10),
    age: formData.age ? parseInt(formData.age, 10) : null,
    gender: formData.gender || null,
    images: {}
  };

  const mapping = [
    ['tongueImage', 'tongue'],
    ['faceImage', 'face'],
    ['eyeImage', 'eye']
  ];

  for (const [fileKey, imageKey] of mapping) {
    if (files[fileKey]) {
      payload.images[imageKey] = await getImageBase64(files[fileKey]);
    }
  }

  if (Object.keys(payload.images).length === 0) {
    delete payload.images;
  }

  return request('/diagnose/json', payload, 'POST', authHeader, {
    timeout: API_ENV.diagnoseTimeoutMs
  });
}

/**
 * 诊断历史上云（需登录）
 */
export function saveDiagnosisHistory(entry, authHeader = {}) {
  return request('/diagnosis/history', entry, 'POST', authHeader);
}

export function fetchDiagnosisHistory(authHeader = {}) {
  return request('/diagnosis/history', {}, 'GET', authHeader);
}

export function fetchDiagnosisHistoryDetail(entryId, authHeader = {}) {
  return request(`/diagnosis/history/${encodeURIComponent(entryId)}`, {}, 'GET', authHeader);
}

export function clearDiagnosisHistory(authHeader = {}) {
  return request('/diagnosis/history', {}, 'DELETE', authHeader);
}

export function deleteDiagnosisHistoryEntry(entryId, authHeader = {}) {
  return request(`/diagnosis/history/${entryId}`, {}, 'DELETE', authHeader);
}

export function showLoading(title = '加载中...') {
  wx.showLoading({ title, mask: true });
}

export function hideLoading() {
  wx.hideLoading();
}

export function showToast(title, icon = 'none', duration = 2000) {
  wx.showToast({ title, icon, duration });
}

export function showConfirmModal(title, content, confirmText = '确定', cancelText = '取消') {
  return new Promise((resolve, reject) => {
    wx.showModal({
      title,
      content,
      confirmText,
      cancelText,
      success(res) {
        if (res.confirm) resolve(true);
        else if (res.cancel) resolve(false);
      },
      fail: reject
    });
  });
}
