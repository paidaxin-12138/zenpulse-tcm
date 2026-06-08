/**
 * 诊断历史 — 微信云开发存储桶
 * 结构：
 *   {prefix}/{userId}/index.json          历史索引（摘要列表）
 *   {prefix}/{userId}/{entryId}.json      单条完整诊断
 */

import { cloudConfig } from '../config/cloud';
import { getStoredUser, getAuthHeaders } from './auth';
import { mergeEntryDetail, mergeHistoryEntries, normalizeResult, saveFullRecord } from './historyStore';
import { request } from './api';

const INDEX_META_KEY = cloudConfig.indexFileIdStorageKey || 'cloudHistoryIndexFileId';

let _inited = false;

function fs() {
  return wx.getFileSystemManager();
}

function tempPath(name) {
  return `${wx.env.USER_DATA_PATH}/${name}`;
}

function writeTempJson(name, data) {
  const path = tempPath(name);
  fs().writeFileSync(path, JSON.stringify(data), 'utf8');
  return path;
}

function readTempJson(path) {
  return JSON.parse(fs().readFileSync(path, 'utf8'));
}

export function isCloudStorageEnabled() {
  return !!(cloudConfig.enabled && wx.cloud);
}

export function initCloud() {
  if (!cloudConfig.enabled || !wx.cloud || _inited) {
    return isCloudStorageEnabled();
  }
  wx.cloud.init({
    env: cloudConfig.envId || wx.cloud.DYNAMIC_CURRENT_ENV,
    traceUser: true
  });
  _inited = true;
  return true;
}

export function getUserScope() {
  const user = getStoredUser();
  return user && user.id ? String(user.id) : 'anonymous';
}

function indexFileIdKey(userId) {
  return `${INDEX_META_KEY}_${userId}`;
}

function getLocalIndexFileId(userId) {
  return wx.getStorageSync(indexFileIdKey(userId)) || '';
}

function setLocalIndexFileId(userId, fileID) {
  if (fileID) {
    wx.setStorageSync(indexFileIdKey(userId), fileID);
  }
}

function cloudPath(userId, filename) {
  const prefix = cloudConfig.storagePrefix || 'diagnosis-history';
  return `${prefix}/${userId}/${filename}`;
}

function uploadJson(cloudPathStr, data) {
  return new Promise((resolve, reject) => {
    const local = writeTempJson(`upload_${Date.now()}.json`, data);
    wx.cloud.uploadFile({
      cloudPath: cloudPathStr,
      filePath: local,
      success: resolve,
      fail: reject
    });
  });
}

function downloadJson(fileID) {
  return new Promise((resolve, reject) => {
    wx.cloud.downloadFile({
      fileID,
      success: (res) => {
        try {
          resolve(readTempJson(res.tempFilePath));
        } catch (err) {
          reject(err);
        }
      },
      fail: reject
    });
  });
}

function emptyIndex() {
  return { version: 1, updated_at: new Date().toISOString(), entries: [] };
}

function toSummary(record, fileID) {
  const time = record.time || record.timestamp || new Date().toISOString();
  return {
    id: record.id,
    time,
    timestamp: record.timestamp || time,
    syndrome: record.syndrome || '',
    diagnosis: record.diagnosis || '',
    summary: record.analysis || record.summary || record.syndrome || record.diagnosis || '',
    diagnosis_mode: record.diagnosis_mode || '',
    has_detail: true,
    fileID: fileID || record.fileID || '',
    storage: 'cloud'
  };
}

function syncIndexFileIdToServer(fileID) {
  if (!fileID) return Promise.resolve();
  return request('/wx/profile', { cloudHistoryIndexFileId: fileID }, 'PUT', getAuthHeaders()).catch(
    (err) => console.warn('同步云索引 fileID 失败', err)
  );
}

function resolveIndexFileId(userId) {
  const local = getLocalIndexFileId(userId);
  if (local) return Promise.resolve(local);

  const user = getStoredUser();
  if (user && user.cloudHistoryIndexFileId) {
    setLocalIndexFileId(userId, user.cloudHistoryIndexFileId);
    return Promise.resolve(user.cloudHistoryIndexFileId);
  }
  return Promise.resolve('');
}

export function fetchCloudHistoryIndex(userId = getUserScope()) {
  if (!isCloudStorageEnabled()) {
    return Promise.resolve([]);
  }
  initCloud();

  return resolveIndexFileId(userId).then((fileID) => {
    if (!fileID) return [];
    return downloadJson(fileID)
      .then((index) => (index && index.entries) || [])
      .catch((err) => {
        console.warn('拉取云存储索引失败', err);
        return [];
      });
  });
}

export function syncHistoryFromCloud(userId = getUserScope()) {
  return fetchCloudHistoryIndex(userId).then((entries) => mergeHistoryEntries(entries));
}

export function fetchCloudDiagnosisDetail(historyItem) {
  if (!isCloudStorageEnabled()) {
    return Promise.resolve(null);
  }
  initCloud();

  const fileID = historyItem.fileID;
  if (!fileID) {
    return Promise.resolve(null);
  }

  return downloadJson(fileID).then((detail) => mergeEntryDetail(historyItem, detail));
}

export function saveDiagnosisToCloud(record, userId = getUserScope()) {
  if (!isCloudStorageEnabled()) {
    return Promise.reject(new Error('云存储未启用'));
  }
  initCloud();

  const entryId = record.id || `cloud_${Date.now()}`;
  const detailPath = cloudPath(userId, `${entryId}.json`);
  const fullRecord = { ...record, id: entryId };

  return uploadJson(detailPath, fullRecord).then((uploadRes) => {
    const fileID = uploadRes.fileID;
    const summary = toSummary(fullRecord, fileID);

    return resolveIndexFileId(userId)
      .then((indexFileID) => {
        if (!indexFileID) return emptyIndex();
        return downloadJson(indexFileID).catch(() => emptyIndex());
      })
      .then((index) => {
        const entries = (index.entries || []).filter((e) => e.id !== entryId);
        entries.unshift(summary);
        const nextIndex = {
          version: 1,
          updated_at: new Date().toISOString(),
          entries: entries.slice(0, 200)
        };
        return uploadJson(cloudPath(userId, 'index.json'), nextIndex);
      })
      .then((indexUpload) => {
        setLocalIndexFileId(userId, indexUpload.fileID);
        syncIndexFileIdToServer(indexUpload.fileID);
        saveFullRecord(fullRecord);
        return { ...summary, detail: fullRecord };
      });
  });
}

export function clearCloudHistory(userId = getUserScope()) {
  if (!isCloudStorageEnabled()) {
    return Promise.resolve();
  }
  wx.removeStorageSync(indexFileIdKey(userId));
  return uploadJson(cloudPath(userId, 'index.json'), emptyIndex()).then((res) => {
    setLocalIndexFileId(userId, res.fileID);
    syncIndexFileIdToServer(res.fileID);
  });
}

export function loadHistoryDetailFromCloud(historyItem) {
  let full = normalizeResult(historyItem);
  const id = full.id || historyItem.id || historyItem.timestamp || historyItem.time || '';

  if (!isCloudStorageEnabled()) {
    return Promise.resolve({ full, id });
  }

  return fetchCloudDiagnosisDetail(historyItem)
    .then((merged) => {
      if (merged) {
        saveFullRecord(merged);
        return { full: merged, id: merged.id || id };
      }
      return { full, id };
    })
    .catch((err) => {
      console.warn('云存储详情拉取失败，使用本地', err);
      return { full, id };
    });
}

/** 拉取历史详情：优先云存储桶，其次 FastAPI，最后本地 */
export function loadHistoryDetailForView(historyItem, fetchDetail, authHeader = {}) {
  if (isCloudStorageEnabled()) {
    return loadHistoryDetailFromCloud(historyItem);
  }

  let full = normalizeResult(historyItem);
  const id = full.id || historyItem.id || historyItem.timestamp || historyItem.time || '';
  const remoteId = historyItem.id;

  if (!fetchDetail || !remoteId || String(remoteId).startsWith('local_')) {
    return Promise.resolve({ full, id });
  }

  return fetchDetail(remoteId, authHeader)
    .then((res) => {
      if (res && res.entry) {
        full = mergeEntryDetail(res.entry, res.entry.detail);
        saveFullRecord(full);
      }
      return { full, id: full.id || id };
    })
    .catch((err) => {
      console.warn('拉取服务端诊断详情失败，使用本地缓存', err);
      return { full, id };
    });
}
