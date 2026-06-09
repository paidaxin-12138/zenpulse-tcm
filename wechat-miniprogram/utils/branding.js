// Copyright (c) 2026 paidaxin-12138
// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
// https://creativecommons.org/licenses/by-nc/4.0/

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
