/**
 * 安全获取 App 实例（onLaunch 同步阶段 getApp() 可能尚未就绪）
 */
export function getAppSafe() {
  try {
    return getApp();
  } catch (e) {
    return null;
  }
}

export function patchGlobalData(patch, appRef) {
  const app = appRef || getAppSafe();
  if (app && app.globalData) {
    Object.assign(app.globalData, patch);
  }
}
