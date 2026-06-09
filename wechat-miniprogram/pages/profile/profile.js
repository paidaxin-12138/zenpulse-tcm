// profile.js
import { getStoredUser, logout, updateProfile, wxLogin } from '../../utils/auth';
import { fetchDiagnosisHistory, fetchDiagnosisHistoryDetail } from '../../utils/api';
import { getAuthHeaders } from '../../utils/auth';
import {
  isCloudStorageEnabled,
  loadHistoryDetailForView,
  syncHistoryFromCloud
} from '../../utils/cloudHistory';
import { mergeHistoryEntries } from '../../utils/historyStore';
import { fetchBranding, getBranding, getWebUrl } from '../../utils/branding';

Page({
  data: {
    userInfo: {
      nickName: '未登录',
      avatarUrl: '',
      id: ''
    },
    isLoggedIn: false,
    loginLoading: false,
    diagnosisHistory: [],
    platformHint: 'ZenPulse AI · Web 与御心调理小程序共用同一后端'
  },

  onLoad() {
    this.refreshUser();
    fetchBranding().then(() => this.refreshPlatformLinks());
  },

  onShow() {
    this.refreshUser();
    this.loadDiagnosisHistory();
    this.refreshPlatformLinks();
  },

  refreshPlatformLinks() {
    const b = getBranding();
    const mp = b.miniprogram?.name || '御心调理';
    this.setData({
      platformHint: `${b.productName || 'ZenPulse AI'} · Web 与 ${mp} 小程序共用同一后端`
    });
  },

  openWebClient() {
    const url = getWebUrl();
    wx.setClipboardData({
      data: url,
      success: () => wx.showToast({ title: 'Web 地址已复制', icon: 'none' })
    });
  },

  refreshUser() {
    const stored = getStoredUser();
    const app = getApp();
    const loggedIn = !!(app.globalData && app.globalData.isLoggedIn && stored);
    this.setData({
      userInfo: stored || { nickName: '未登录', avatarUrl: '', id: '' },
      isLoggedIn: loggedIn
    });
  },

  loadDiagnosisHistory() {
    const app = getApp();
    const local = app.getDiagnosisHistory() || [];
    this.setData({ diagnosisHistory: local.slice(0, 5) });

    if (isCloudStorageEnabled()) {
      syncHistoryFromCloud()
        .then((entries) => {
          if (entries.length) {
            this.setData({ diagnosisHistory: entries.slice(0, 5) });
            app.globalData.diagnosisHistory = entries;
            wx.setStorageSync('diagnosisHistory', entries);
          }
        })
        .catch((err) => console.warn('拉取云存储历史失败', err));
      return;
    }

    if (!this.data.isLoggedIn) return;

    fetchDiagnosisHistory(getAuthHeaders())
      .then((res) => {
        const entries = mergeHistoryEntries(res.entries || []);
        if (entries.length) {
          this.setData({ diagnosisHistory: entries.slice(0, 5) });
          app.globalData.diagnosisHistory = entries;
          wx.setStorageSync('diagnosisHistory', entries);
        }
      })
      .catch((err) => console.warn('拉取云端历史失败', err));
  },

  onLoginTap() {
    this.setData({ loginLoading: true });
    wxLogin()
      .then((data) => {
        this.setData({
          userInfo: data.user,
          isLoggedIn: true,
          loginLoading: false
        });
        wx.showToast({ title: '登录成功', icon: 'success' });
        this.loadDiagnosisHistory();
      })
      .catch((err) => {
        this.setData({ loginLoading: false });
        wx.showToast({ title: err.message || '登录失败', icon: 'none' });
      });
  },

  onChooseAvatar(e) {
    const avatarUrl = e.detail.avatarUrl;
    if (!avatarUrl) return;
    updateProfile({ avatarUrl })
      .then((data) => {
        this.setData({ userInfo: data.user, isLoggedIn: true });
      })
      .catch(() => wx.showToast({ title: '头像更新失败', icon: 'none' }));
  },

  onNicknameBlur(e) {
    const nickName = (e.detail.value || '').trim();
    if (!nickName || !this.data.isLoggedIn) return;
    updateProfile({ nickName })
      .then((data) => this.setData({ userInfo: data.user }))
      .catch(() => wx.showToast({ title: '昵称更新失败', icon: 'none' }));
  },

  onLogoutTap() {
    wx.showModal({
      title: '退出登录',
      content: '退出后云端历史需重新登录才能同步',
      success: (res) => {
        if (res.confirm) {
          logout();
          this.setData({
            isLoggedIn: false,
            userInfo: { nickName: '未登录', avatarUrl: '', id: '' }
          });
          wx.showToast({ title: '已退出', icon: 'none' });
        }
      }
    });
  },

  formatDate(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const pad = (n) => String(n).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
  },

  showDiagnosisHistory() {
    wx.navigateTo({ url: '/pages/history/history' });
  },

  showSettings() {
    wx.navigateTo({ url: '/pages/settings/settings' });
  },

  showHelp() {
    wx.showModal({
      title: '帮助与反馈',
      content: '如有问题请联系客服。\n客服邮箱：lkc041002@outlook.com',
      showCancel: false
    });
  },

  showAbout() {
    const b = getBranding();
    wx.showModal({
      title: '关于我们',
      content: `${b.brandName || '御心调理'} v1.1.0\n${b.productName || 'ZenPulse AI'} 中医智能诊断\n\nWeb：${getWebUrl()}`,
      showCancel: false
    });
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

  startNewDiagnosis() {
    wx.switchTab({ url: '/pages/index/index' });
  },

  onShareAppMessage() {
    return { title: '中医智能诊断系统', path: '/pages/index/index' };
  }
});
