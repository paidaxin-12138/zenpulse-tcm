/**
 * 小程序真机联调：自定义后端地址与探测
 */
import { API_ENV } from '../config/env';
import { getAppSafe } from './appContext';

export const BASE_URL_STORAGE_KEY = 'zp_api_base_url';

export function getStoredBaseUrl() {
  const app = getAppSafe();
  if (app?.globalData?.baseUrl) return app.globalData.baseUrl;
  try {
    return wx.getStorageSync(BASE_URL_STORAGE_KEY) || '';
  } catch (_) {
    return '';
  }
}

export function saveBaseUrl(url) {
  const normalized = (url || '').trim().replace(/\/$/, '');
  if (!normalized) return '';
  wx.setStorageSync(BASE_URL_STORAGE_KEY, normalized);
  const app = getAppSafe();
  if (app?.globalData) {
    app.globalData.baseUrl = normalized;
    app.globalData.serverReachable = true;
  }
  return normalized;
}

export function clearBaseUrl() {
  wx.removeStorageSync(BASE_URL_STORAGE_KEY);
  const app = getAppSafe();
  if (app?.globalData) {
    app.globalData.baseUrl = '';
    app.globalData.serverReachable = false;
  }
}

export function normalizeApiBase(input) {
  let url = (input || '').trim().replace(/\/$/, '');
  if (!url) return '';
  if (!/^https?:\/\//i.test(url)) url = 'http://' + url;
  if (!url.endsWith('/api')) url = url.replace(/\/?$/, '') + '/api';
  return url;
}

export function probeBaseUrl(baseUrl, timeoutMs) {
  const timeout = timeoutMs || API_ENV.probeTimeoutMs || 4000;
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

/** 从已连通的后端获取局域网联调建议 */
export function fetchDevHints(baseUrl) {
  const root = (baseUrl || getStoredBaseUrl() || API_ENV.baseUrlCandidates[0] || '').replace(/\/$/, '');
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${root}/public/dev-hints`,
      method: 'GET',
      timeout: API_ENV.probeTimeoutMs || 4000,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data);
        else reject(new Error(`HTTP ${res.statusCode}`));
      },
      fail: reject
    });
  });
}

export function buildCandidateUrls() {
  const list = [
    API_ENV.customBaseUrl,
    getStoredBaseUrl(),
    ...(API_ENV.baseUrlCandidates || [])
  ].filter(Boolean).map((u) => normalizeApiBase(u));
  return [...new Set(list)];
}

export async function testAndSaveApiBase(input) {
  const baseUrl = normalizeApiBase(input);
  if (!baseUrl) throw new Error('请输入后端地址');
  await probeBaseUrl(baseUrl);
  saveBaseUrl(baseUrl);
  return baseUrl;
}
