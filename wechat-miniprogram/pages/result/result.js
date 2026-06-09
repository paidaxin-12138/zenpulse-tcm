// Copyright (c) 2026 paidaxin-12138
// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
// https://creativecommons.org/licenses/by-nc/4.0/

// result.js
import { fetchDiagnosisHistoryDetail, saveDiagnosisHistory } from '../../utils/api';
import { getAuthHeaders } from '../../utils/auth';
import {
  isCloudStorageEnabled,
  loadHistoryDetailForView,
  saveDiagnosisToCloud
} from '../../utils/cloudHistory';
import {
  getFullRecord,
  migrateFullRecord,
  normalizeResult,
  resolveHistoryItem,
  saveFullRecord
} from '../../utils/historyStore';
import { saveReportToAlbum } from '../../utils/reportExport';
import { getBranding } from '../../utils/branding';

function getAppInstance() {
  try {
    return getApp();
  } catch (e) {
    return null;
  }
}

Page({
  data: {
    fromHistory: false,
    diagnosisResult: normalizeResult(null),
    reportContext: {}
  },

  onLoad(options) {
    this._resultApplied = false;
    const fromHistory = options.fromHistory === '1';
    const ctx = wx.getStorageSync('lastDiagnosisContext') || {};
    this.setData({
      fromHistory,
      reportContext: this.buildReportContext(ctx)
    });

    try {
      const eventChannel = this.getOpenerEventChannel();
      if (eventChannel && typeof eventChannel.on === 'function') {
        eventChannel.on('passDiagnosisResult', (data) => {
          if (data && data.result) {
            this._resultApplied = true;
            this.applyResult(data.result, { saveHistory: true });
          }
        });
      }
    } catch (error) {
      console.warn('eventChannel 不可用', error);
    }

    if (fromHistory) {
      this.loadHistoryResult(options.id);
    } else {
      setTimeout(() => {
        if (!this._resultApplied) {
          this.loadCachedResult({ saveHistory: false });
        }
      }, 250);
    }
  },

  onShow() {
    if (this.data.fromHistory && !this._resultApplied) {
      const pages = getCurrentPages();
      const current = pages[pages.length - 1];
      const id = current && current.options && current.options.id;
      this.loadHistoryResult(id);
    }
  },

  loadHistoryResult(id) {
    const app = getAppInstance();
    const list =
      (app && app.getDiagnosisHistory && app.getDiagnosisHistory()) ||
      wx.getStorageSync('diagnosisHistory') ||
      [];
    let item = null;

    if (id) {
      item = list.find(
        (h) =>
          String(h.id) === String(id) ||
          String(h.timestamp) === String(id) ||
          String(h.time) === String(id)
      );
    }

    const fromMap = id ? getFullRecord(id) : null;
    const localResolved = fromMap || (item ? resolveHistoryItem(item) : null);

    if (
      localResolved &&
      (localResolved.syndrome || localResolved.diagnosis || localResolved.analysis) &&
      (!item || !item.has_detail || localResolved.analysis)
    ) {
      this._resultApplied = true;
      this.applyResult(localResolved, { saveHistory: false });
      return;
    }

    if (item && item.id && !String(item.id).startsWith('local_')) {
      loadHistoryDetailForView(item, fetchDiagnosisHistoryDetail, getAuthHeaders())
        .then(({ full }) => {
          if (full && (full.syndrome || full.diagnosis || full.analysis)) {
            this._resultApplied = true;
            this.applyResult(full, { saveHistory: false });
            return;
          }
          this.loadCachedResult({ saveHistory: false });
        })
        .catch(() => this.loadCachedResult({ saveHistory: false }));
      return;
    }

    this.loadCachedResult({ saveHistory: false });
  },

  loadCachedResult({ saveHistory }) {
    const cached = wx.getStorageSync('lastDiagnosisResult');
    if (!cached) {
      wx.showToast({ title: '未找到诊断详情', icon: 'none' });
      return;
    }
    this._resultApplied = true;
    this.applyResult(cached, { saveHistory });
  },

  applyResult(raw, { saveHistory }) {
    const normalized = normalizeResult(raw);
    this.setData({ diagnosisResult: normalized });
    wx.setStorageSync('lastDiagnosisResult', normalized);
    if (saveHistory) {
      this.persistHistory(normalized);
    }
  },

  persistHistory(result) {
    const app = getAppInstance();
    const diagnosisWithTime = {
      ...result,
      id: result.id || `local_${Date.now()}`,
      timestamp: result.timestamp || new Date().toISOString()
    };

    saveFullRecord(diagnosisWithTime);
    if (app && app.addDiagnosisHistory) {
      app.addDiagnosisHistory(diagnosisWithTime);
    }

    if (isCloudStorageEnabled()) {
      saveDiagnosisToCloud(diagnosisWithTime)
        .then((entry) => {
          const withCloud = {
            ...diagnosisWithTime,
            id: entry.id,
            fileID: entry.fileID,
            has_detail: true,
            storage: 'cloud'
          };
          migrateFullRecord(diagnosisWithTime.id, withCloud);
          if (app && app.getDiagnosisHistory) {
            const list = app.getDiagnosisHistory().map((item) =>
              item.timestamp === diagnosisWithTime.timestamp || item.id === diagnosisWithTime.id
                ? withCloud
                : item
            );
            app.globalData.diagnosisHistory = list;
            wx.setStorageSync('diagnosisHistory', list);
          }
        })
        .catch((err) => {
          console.warn('诊断历史写入云存储失败（已保留本地）', err);
        });
      return;
    }

    const payload = {
      syndrome: result.syndrome || '',
      diagnosis: result.diagnosis || '',
      summary: result.analysis || result.syndrome || result.diagnosis || '',
      diagnosis_mode: result.diagnosis_mode || '',
      detail: result
    };

    saveDiagnosisHistory(payload, getAuthHeaders())
      .then((res) => {
        if (res && res.entry && res.entry.id) {
          const withId = { ...diagnosisWithTime, id: res.entry.id };
          migrateFullRecord(diagnosisWithTime.id, withId);
          if (app && app.getDiagnosisHistory) {
            const list = app.getDiagnosisHistory().map((item) =>
              item.timestamp === diagnosisWithTime.timestamp ||
              item.id === diagnosisWithTime.id
                ? withId
                : item
            );
            app.globalData.diagnosisHistory = list;
            wx.setStorageSync('diagnosisHistory', list);
          }
        }
      })
      .catch((err) => {
        console.warn('诊断历史上云失败（已保留本地）', err);
      });
  },

  buildReportContext(stored) {
    stored = stored || {};
    const metrics = stored.metrics || {};
    const brand = getBranding();
    return {
      age: metrics.age || '',
      gender: metrics.gender || '—',
      date: stored.date || new Date().toISOString(),
      brandName: brand.productName || brand.brandName || 'ZenPulse AI',
      patientName: '问诊用户'
    };
  },

  saveReportImage() {
    const { diagnosisResult, reportContext } = this.data;
    if (!diagnosisResult || (!diagnosisResult.syndrome && !diagnosisResult.diagnosis)) {
      wx.showToast({ title: '暂无报告内容', icon: 'none' });
      return;
    }
    wx.showLoading({ title: '生成报告中...', mask: true });
    saveReportToAlbum(this, 'reportCanvas', diagnosisResult, reportContext)
      .then(() => {
        wx.showToast({ title: '已保存到相册', icon: 'success' });
      })
      .catch((err) => {
        const msg = (err && err.message) || '保存失败';
        if (/auth|authorize|权限/i.test(msg)) {
          wx.showModal({
            title: '需要相册权限',
            content: '请在设置中允许保存图片到相册',
            confirmText: '去设置',
            success: (r) => {
              if (r.confirm) wx.openSetting();
            }
          });
        } else {
          wx.showToast({ title: msg.slice(0, 20), icon: 'none' });
        }
      })
      .finally(() => wx.hideLoading());
  },

  shareResult() {
    wx.showActionSheet({
      itemList: ['分享给朋友', '保存报告图片'],
      success: (res) => {
        if (res.tapIndex === 0) {
          wx.showShareMenu({ withShareTicket: true, menus: ['shareAppMessage'] });
        } else if (res.tapIndex === 1) {
          this.saveReportImage();
        }
      }
    });
  },

  newDiagnosis() {
    wx.showModal({
      title: '重新诊断',
      content: '确定要开始新的诊断吗？',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({ url: '/pages/metrics/metrics' });
        }
      }
    });
  },

  backToHome() {
    if (this.data.fromHistory) {
      wx.navigateBack({
        fail: () => wx.switchTab({ url: '/pages/profile/profile' })
      });
      return;
    }
    wx.navigateBack({
      delta: 3,
      fail: () => wx.switchTab({ url: '/pages/index/index' })
    });
  },

  onShareAppMessage() {
    const { diagnosisResult } = this.data;
    const text = diagnosisResult.diagnosis || diagnosisResult.syndrome || '中医智能诊断';
    return {
      title: '中医智能诊断系统 - 诊断结果',
      path: '/pages/index/index',
      desc: text.substring(0, 50)
    };
  }
});
