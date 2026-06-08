import { request } from './api';
import { defaultBranding } from '../config/branding';
import { API_ENV } from '../config/env';
import { getAppSafe, patchGlobalData } from './appContext';

let cached = null;

export function getBranding() {
  return cached || defaultBranding;
}

export function fetchBranding() {
  return request('/public/branding', {}, 'GET')
    .then((data) => {
      cached = { ...defaultBranding, ...data };
      if (data.links) cached.links = { ...defaultBranding.links, ...data.links };
      if (data.miniprogram) cached.miniprogram = { ...defaultBranding.miniprogram, ...data.miniprogram };
      patchGlobalData({ branding: cached });
      return cached;
    })
    .catch(() => {
      cached = defaultBranding;
      return cached;
    });
}

export function getWebUrl() {
  const app = getAppSafe();
  const base = (app && app.globalData && app.globalData.baseUrl) || API_ENV.baseUrl;
  return base.replace(/\/api\/?$/, '') || 'http://localhost:8000';
}

export function getAdminUrl() {
  return `${getWebUrl()}/admin`;
}
