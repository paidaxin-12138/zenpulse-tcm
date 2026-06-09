// Copyright (c) 2026 paidaxin-12138
// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
// https://creativecommons.org/licenses/by-nc/4.0/

// history.js
import { clearDiagnosisHistory, fetchDiagnosisHistory, fetchDiagnosisHistoryDetail } from '../../utils/api';
import { getAuthHeaders } from '../../utils/auth';
import {
  clearCloudHistory,
  isCloudStorageEnabled,
  loadHistoryDetailForView,
  syncHistoryFromCloud
} from '../../utils/cloudHistory';
import { clearFullRecords, mergeHistoryEntries } from '../../utils/historyStore';

Page({
  data: {
    diagnosisHistory: []
  },

  onShow() {
    this.loadDiagnosisHistory();
  },

  loadDiagnosisHistory() {
    const app = getApp();
    const local = app.getDiagnosisHistory() || [];
    this.setData({ diagnosisHistory: local });

    if (isCloudStorageEnabled()) {
      syncHistoryFromCloud()
        .then((entries) => {
          if (entries.length) {
            this.setData({ diagnosisHistory: entries });
            app.globalData.diagnosisHistory = entries;
            wx.setStorageSync('diagnosisHistory', entries);
          }
        })
        .catch((err) => console.warn('拉取云存储历史失败', err));
      return;
    }

    fetchDiagnosisHistory(getAuthHeaders())
      .then((res) => {
        const entries = mergeHistoryEntries(res.entries || []);
        if (entries.length) {
          this.setData({ diagnosisHistory: entries });
          app.globalData.diagnosisHistory = entries;
          wx.setStorageSync('diagnosisHistory', entries);
        }
      })
      .catch((err) => console.warn('拉取云端历史失败', err));
  },

  formatDate(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const pad = (n) => String(n).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
  },

  showHistoryDetail(e) {
    const index = e.currentTarget.dataset.index;
    const historyItem = this.data.diagnosisHistory[index];
    if (!historyItem) {
      wx.showToast({ title: '记录不存在', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '加载中...', mask: true });
    loadHistoryDetailForView(historyItem, fetchDiagnosisHistoryDetail, getAuthHeaders())
      .then(({ full, id }) => {
        wx.hideLoading();
        wx.setStorageSync('lastDiagnosisResult', full);
        wx.navigateTo({
          url: `/pages/result/result?fromHistory=1&id=${encodeURIComponent(id)}`
        });
      })
      .catch(() => {
        wx.hideLoading();
        wx.showToast({ title: '加载失败', icon: 'none' });
      });
  },

  clearHistory() {
    wx.showModal({
      title: '确认清空',
      content: '确定要清空所有诊断历史记录吗？',
      success: (res) => {
        if (!res.confirm) return;
        const app = getApp();
        app.globalData.diagnosisHistory = [];
        wx.removeStorageSync('diagnosisHistory');
        clearFullRecords();
        this.setData({ diagnosisHistory: [] });

        if (isCloudStorageEnabled()) {
          clearCloudHistory().catch((err) => console.warn('云存储清空失败', err));
        } else {
          clearDiagnosisHistory(getAuthHeaders()).catch((err) => {
            console.warn('云端清空失败', err);
          });
        }

        wx.showToast({ title: '历史记录已清空', icon: 'success' });
      }
    });
  },

  startNewDiagnosis() {
    wx.switchTab({ url: '/pages/index/index' });
  }
});
