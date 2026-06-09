// Copyright (c) 2026 paidaxin-12138
// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
// https://creativecommons.org/licenses/by-nc/4.0/

// auth.js — 微信小程序登录与 Token 刷新

import { request } from './api';
import { getAppSafe, patchGlobalData } from './appContext';

const TOKEN_KEY = 'wx_token';
const USER_KEY = 'wx_user';
const EXPIRES_AT_KEY = 'wx_token_expires_at';
const REFRESH_LEAD_MS = 24 * 60 * 60 * 1000;

export function getToken() {
  return wx.getStorageSync(TOKEN_KEY) || '';
}

export function getStoredUser() {
  return wx.getStorageSync(USER_KEY) || null;
}

export function getTokenExpiresAt() {
  return wx.getStorageSync(EXPIRES_AT_KEY) || 0;
}

export function setSession(token, user, appRef, expiresIn) {
  wx.setStorageSync(TOKEN_KEY, token);
  wx.setStorageSync(USER_KEY, user);
  if (expiresIn) {
    wx.setStorageSync(EXPIRES_AT_KEY, Date.now() + Number(expiresIn) * 1000);
  }
  patchGlobalData(
    {
      token,
      userInfo: user,
      isLoggedIn: true
    },
    appRef
  );
}

export function clearSession(appRef) {
  wx.removeStorageSync(TOKEN_KEY);
  wx.removeStorageSync(USER_KEY);
  wx.removeStorageSync(EXPIRES_AT_KEY);
  patchGlobalData(
    {
      token: '',
      userInfo: null,
      isLoggedIn: false
    },
    appRef
  );
}

export function getAuthHeaders() {
  const token = getToken();
  if (!token) return {};
  return {
    Authorization: `Bearer ${token}`,
    'X-WX-Token': token
  };
}

export function shouldRefreshToken() {
  const token = getToken();
  if (!token) return false;
  const expiresAt = getTokenExpiresAt();
  // 旧版登录未写入过期时间：session 有效即可，勿每次启动都调 refresh
  if (!expiresAt) return false;
  return Date.now() >= expiresAt - REFRESH_LEAD_MS;
}

/**
 * 使用当前 Token 换取新 Token（未过期或宽限期内）
 */
export function refreshToken(appRef) {
  return request('/wx/refresh', {}, 'POST', getAuthHeaders(), { timeout: 10000 })
    .then((data) => {
      setSession(data.token, data.user || getStoredUser(), appRef, data.expires_in);
      return data;
    });
}

/**
 * wx.login → POST /api/wx/login
 */
export function wxLogin(appRef) {
  return new Promise((resolve, reject) => {
    wx.login({
      success(res) {
        if (!res.code) {
          reject(new Error('未获取到登录 code'));
          return;
        }
        request('/wx/login', { code: res.code }, 'POST', {}, { timeout: 10000 })
          .then((data) => {
            setSession(data.token, data.user, appRef, data.expires_in);
            resolve(data);
          })
          .catch(reject);
      },
      fail(err) {
        reject(err);
      }
    });
  });
}

function afterSessionValidated(data, appRef) {
  const token = getToken();
  if (data.logged_in && data.user) {
    setSession(token, data.user, appRef);
    if (shouldRefreshToken()) {
      return refreshToken(appRef).catch(() => data);
    }
    // 首次升级：无 expires_at 时静默刷新一次以写入 expires_in（404/401 忽略）
    if (!getTokenExpiresAt()) {
      return refreshToken(appRef)
        .catch(() => data)
        .then((result) => result || data);
    }
    return data;
  }
  clearSession(appRef);
  return wxLogin(appRef);
}

/**
 * 启动时静默登录；失败不阻断主流程
 * @param {object} [appRef] onLaunch 内传入 App 实例（this）
 */
export function ensureLogin(appRef) {
  const token = getToken();
  if (token) {
    patchGlobalData(
      {
        token,
        userInfo: getStoredUser(),
        isLoggedIn: true
      },
      appRef
    );
    return request('/wx/session', {}, 'GET', getAuthHeaders(), { timeout: 10000 })
      .then((data) => afterSessionValidated(data, appRef))
      .catch(() => {
        if (shouldRefreshToken()) {
          return refreshToken(appRef).catch(() => wxLogin(appRef));
        }
        return wxLogin(appRef);
      });
  }
  return wxLogin(appRef);
}

export function updateProfile(profile) {
  return request('/wx/profile', profile, 'PUT', getAuthHeaders()).then((data) => {
    if (data.user) {
      setSession(getToken(), data.user, null, getExpiresInRemaining());
    }
    return data;
  });
}

function getExpiresInRemaining() {
  const expiresAt = getTokenExpiresAt();
  if (!expiresAt) return null;
  return Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
}

export function logout() {
  clearSession();
}
