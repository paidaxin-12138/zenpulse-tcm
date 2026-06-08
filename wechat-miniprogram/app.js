// app.js
import { ensureLogin, getStoredUser, getToken } from './utils/auth';
import { fetchBranding } from './utils/branding';
import { initCloud, isCloudStorageEnabled, syncHistoryFromCloud } from './utils/cloudHistory';
import { saveFullRecord } from './utils/historyStore';
import { API_ENV } from './config/env';
import { bootstrapServer } from './utils/api';

App({
  onLaunch() {
    console.log('中医智能诊断系统启动');

    this.globalData = {
      userInfo: getStoredUser(),
      token: getToken(),
      diagnosisHistory: [],
      baseUrl: API_ENV.customBaseUrl || API_ENV.baseUrlCandidates[0],
      serverReachable: null,
      isLoggedIn: !!getToken(),
      branding: null
    };

    initCloud();

    wx.getNetworkType({
      success(res) {
        console.log('网络状态:', res.networkType);
      }
    });

    bootstrapServer(this).then((ok) => {
      if (!ok) {
        console.warn('后端不可达 — 请运行: python3 web_server.py');
        wx.showToast({
          title: '后端未连接，请先启动服务',
          icon: 'none',
          duration: 3500
        });
        return;
      }
      fetchBranding().catch(() => {});
      ensureLogin(this)
        .then((data) => {
          console.log('微信登录成功', data && data.user && data.user.nickName);
          if (isCloudStorageEnabled()) {
            syncHistoryFromCloud().then((entries) => {
              if (entries && entries.length) {
                this.globalData.diagnosisHistory = entries;
                wx.setStorageSync('diagnosisHistory', entries);
              }
            });
          }
        })
        .catch((err) => {
          console.warn('微信登录失败（可稍后在「我的」重试）', err);
        });
    });
  },

  onShow() {
    console.log('中医智能诊断系统显示');
  },

  onHide() {
    console.log('中医智能诊断系统隐藏');
  },

  onError(error) {
    console.error('应用错误:', error);
  },

  getGlobalData() {
    return this.globalData;
  },

  setUserInfo(userInfo) {
    this.globalData.userInfo = userInfo;
    this.globalData.isLoggedIn = true;
  },

  addDiagnosisHistory(diagnosis) {
    const entry = {
      ...diagnosis,
      id: diagnosis.id || `local_${Date.now()}`,
      timestamp: diagnosis.timestamp || new Date().toISOString()
    };
    saveFullRecord(entry);
    this.globalData.diagnosisHistory.unshift(entry);
    wx.setStorageSync('diagnosisHistory', this.globalData.diagnosisHistory);
  },

  getDiagnosisHistory() {
    const history = wx.getStorageSync('diagnosisHistory');
    if (history) {
      this.globalData.diagnosisHistory = history;
    }
    return this.globalData.diagnosisHistory;
  }
});
