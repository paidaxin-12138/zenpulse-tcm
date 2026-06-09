// Copyright (c) 2026 paidaxin-12138
// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
// https://creativecommons.org/licenses/by-nc/4.0/

/**
 * 微信云开发配置
 * 开通云开发后：填写 envId，并将 enabled 设为 true
 */
export const cloudConfig = {
  /** 是否使用云存储桶保存诊断历史（true 时不再走 FastAPI /diagnosis/history） */
  enabled: false,
  /** 云环境 ID，在微信开发者工具 → 云开发 中查看 */
  envId: '',
  /** 存储桶路径前缀 */
  storagePrefix: 'diagnosis-history',
  /** 单用户 index.json 在本地缓存的 fileID 键名后缀 */
  indexFileIdStorageKey: 'cloudHistoryIndexFileId'
};
