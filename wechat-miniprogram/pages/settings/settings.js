import {
  fetchDevHints,
  getStoredBaseUrl,
  clearBaseUrl,
  testAndSaveApiBase,
  probeBaseUrl,
  normalizeApiBase
} from '../../utils/devServer';
import { bootstrapServer } from '../../utils/api';

Page({
  data: {
    apiBase: '',
    currentBase: '',
    suggestedBase: '',
    connected: false,
    testing: false,
    statusText: '',
    checklist: []
  },

  onShow() {
    const current = getStoredBaseUrl();
    this.setData({ currentBase: current, apiBase: current });
    this.refreshHints(current);
    if (current) this.checkCurrent(current);
  },

  onInput(e) {
    this.setData({ apiBase: e.detail.value });
  },

  refreshHints(baseUrl) {
    const tryFetch = (url) => {
      if (!url) return;
      fetchDevHints(url)
        .then((hints) => {
          this.setData({
            suggestedBase: hints.suggested_api_base || '',
            checklist: hints.checklist || []
          });
          if (!this.data.apiBase && hints.suggested_api_base) {
            this.setData({ apiBase: hints.suggested_api_base });
          }
        })
        .catch(() => {});
    };
    tryFetch(baseUrl);
    if (!baseUrl) {
      tryFetch('http://127.0.0.1:8000/api');
    }
  },

  checkCurrent(baseUrl) {
    probeBaseUrl(baseUrl)
      .then(() => this.setData({ connected: true, statusText: '连接正常' }))
      .catch((err) => this.setData({ connected: false, statusText: '无法连接: ' + (err.errMsg || err.message || '') }));
  },

  onUseSuggested() {
    if (this.data.suggestedBase) {
      this.setData({ apiBase: this.data.suggestedBase });
    }
  },

  onTestSave() {
    this.setData({ testing: true });
    testAndSaveApiBase(this.data.apiBase)
      .then((saved) => {
        bootstrapServer(getApp()).catch(() => {});
        this.setData({
          testing: false,
          currentBase: saved,
          connected: true,
          statusText: '已保存并连接成功'
        });
        wx.showToast({ title: '连接成功', icon: 'success' });
        this.refreshHints(saved);
      })
      .catch((err) => {
        this.setData({ testing: false, connected: false, statusText: err.message || '连接失败' });
        wx.showToast({ title: err.message || '连接失败', icon: 'none' });
      });
  },

  onClear() {
    clearBaseUrl();
    bootstrapServer(getApp()).then(() => {
      this.setData({
        apiBase: '',
        currentBase: '',
        connected: false,
        statusText: '已恢复自动探测'
      });
      wx.showToast({ title: '已恢复', icon: 'none' });
    });
  }
});
