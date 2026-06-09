// Copyright (c) 2026 paidaxin-12138
// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
// https://creativecommons.org/licenses/by-nc/4.0/

/**
 * 微信小程序用户隐私保护指引（蓝牙等敏感 API 调用前需授权）
 * 后台配置：mp.weixin.qq.com → 设置 → 用户隐私保护指引
 */

function privacyApiAvailable(name) {
  return typeof wx[name] === 'function';
}

export function getPrivacySetting() {
  return new Promise((resolve) => {
    if (!privacyApiAvailable('getPrivacySetting')) {
      resolve({ needAuthorization: false, privacyContractName: '用户隐私保护指引' });
      return;
    }
    wx.getPrivacySetting({
      success: (res) => {
        resolve({
          needAuthorization: !!res.needAuthorization,
          privacyContractName: res.privacyContractName || '用户隐私保护指引'
        });
      },
      fail: () => {
        resolve({ needAuthorization: false, privacyContractName: '用户隐私保护指引' });
      }
    });
  });
}

export function requirePrivacyAuthorize() {
  return new Promise((resolve, reject) => {
    if (!privacyApiAvailable('requirePrivacyAuthorize')) {
      resolve();
      return;
    }
    wx.requirePrivacyAuthorize({
      success: resolve,
      fail: reject
    });
  });
}

export function openPrivacyContract() {
  if (privacyApiAvailable('openPrivacyContract')) {
    wx.openPrivacyContract();
  }
}

export async function ensurePrivacyAuthorized() {
  const setting = await getPrivacySetting();
  if (!setting.needAuthorization) return setting;
  await requirePrivacyAuthorize();
  return getPrivacySetting();
}

export function isPrivacyApiBannedError(err) {
  const msg = String((err && (err.errMsg || err.message)) || '');
  return /privacy api banned|privacy/i.test(msg);
}

export function privacyBannedMessage() {
  return '小程序尚未在后台「用户隐私保护指引」中声明蓝牙权限，或未随版本审核生效。请在 mp.weixin.qq.com 勾选「蓝牙」后重新提审。';
}
