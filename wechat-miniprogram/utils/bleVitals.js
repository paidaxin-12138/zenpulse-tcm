/**
 * ESP32 ZenPulse 腕带 BLE 采集（与固件协议一致：CH1/CH2 行）
 */

import { isPrivacyApiBannedError, privacyBannedMessage } from './privacy';

function normalizeBleError(err) {
  if (isPrivacyApiBannedError(err)) {
    return new Error(privacyBannedMessage());
  }
  const msg = (err && (err.errMsg || err.message)) || '蓝牙操作失败';
  return new Error(msg);
}

const DEVICE_NAME_PREFIX = 'ZenPulse';
const SERVICE_UUID = '0000FFF0-0000-1000-8000-00805F9B34FB';
const NOTIFY_UUID = '0000FFF1-0000-1000-8000-00805F9B34FB';
const DEFAULT_FS = 100;

let activeCharChangeHandler = null;

function parseLine(line) {
  const out = { ch1: null, ch2: null };
  const parts = String(line).split(',');
  for (const part of parts) {
    const idx = part.indexOf(':');
    if (idx < 0) continue;
    const key = part.slice(0, idx).trim().toUpperCase();
    const val = parseInt(part.slice(idx + 1).trim(), 10);
    if (Number.isNaN(val)) continue;
    if (key === 'CH1') out.ch1 = val;
    if (key === 'CH2') out.ch2 = val;
  }
  return out;
}

function openAdapter() {
  return new Promise((resolve, reject) => {
    wx.openBluetoothAdapter({
      success: resolve,
      fail: (err) => reject(normalizeBleError(err))
    });
  });
}

function closeAdapter() {
  return new Promise((resolve) => {
    wx.closeBluetoothAdapter({ complete: resolve });
  });
}

function stopDiscovery() {
  return new Promise((resolve) => {
    wx.stopBluetoothDevicesDiscovery({ complete: resolve });
  });
}

function teardownBleListeners(onDeviceFound) {
  if (onDeviceFound) {
    wx.offBluetoothDeviceFound(onDeviceFound);
  }
  if (activeCharChangeHandler) {
    wx.offBLECharacteristicValueChange(activeCharChangeHandler);
    activeCharChangeHandler = null;
  }
}

function findDevice(timeoutMs = 12000) {
  return new Promise((resolve, reject) => {
    const found = new Map();
    let settled = false;

    const onDeviceFound = (res) => {
      (res.devices || []).forEach((d) => {
        const name = d.name || d.localName || '';
        if (name.indexOf(DEVICE_NAME_PREFIX) >= 0) {
          found.set(d.deviceId, d);
        }
      });
    };

    const finish = (fn) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      teardownBleListeners(onDeviceFound);
      stopDiscovery().finally(fn);
    };

    const timer = setTimeout(() => {
      finish(() => {
        const list = [...found.values()];
        if (!list.length) {
          reject(new Error('未找到 ZenPulse 设备，请确认腕带已开机且在附近'));
        } else {
          resolve(list[0]);
        }
      });
    }, timeoutMs);

    wx.onBluetoothDeviceFound(onDeviceFound);
    wx.startBluetoothDevicesDiscovery({
      allowDuplicatesKey: false,
      success: () => {},
      fail: (err) => {
        finish(() => reject(err));
      }
    });
  });
}

function connectDevice(deviceId) {
  return new Promise((resolve, reject) => {
    wx.createBLEConnection({
      deviceId,
      timeout: 10000,
      success: resolve,
      fail: reject
    });
  });
}

function enableNotify(deviceId, onLine) {
  return new Promise((resolve, reject) => {
    wx.getBLEDeviceServices({
      deviceId,
      success: (svcRes) => {
        const service = (svcRes.services || []).find(
          (s) => s.uuid.toUpperCase() === SERVICE_UUID
        );
        if (!service) {
          reject(new Error('未找到 ZenPulse BLE 服务'));
          return;
        }
        wx.getBLEDeviceCharacteristics({
          deviceId,
          serviceId: service.uuid,
          success: (charRes) => {
            const notifyChar = (charRes.characteristics || []).find(
              (c) => c.uuid.toUpperCase() === NOTIFY_UUID && c.properties.notify
            );
            if (!notifyChar) {
              reject(new Error('未找到数据通知特征值'));
              return;
            }
            wx.notifyBLECharacteristicValueChange({
              deviceId,
              serviceId: service.uuid,
              characteristicId: notifyChar.uuid,
              state: true,
              success: () => {
                if (activeCharChangeHandler) {
                  wx.offBLECharacteristicValueChange(activeCharChangeHandler);
                }
                activeCharChangeHandler = (evt) => {
                  const text = ab2str(evt.value);
                  text.split('\n').forEach((line) => {
                    if (line.trim()) onLine(line.trim());
                  });
                };
                wx.onBLECharacteristicValueChange(activeCharChangeHandler);
                resolve({ serviceId: service.uuid, characteristicId: notifyChar.uuid });
              },
              fail: reject
            });
          },
          fail: reject
        });
      },
      fail: reject
    });
  });
}

function ab2str(buffer) {
  const arr = new Uint8Array(buffer);
  let s = '';
  for (let i = 0; i < arr.length; i++) s += String.fromCharCode(arr[i]);
  try {
    return decodeURIComponent(escape(s));
  } catch (_) {
    return s;
  }
}

function finalizeCapturedChannels(ch1, ch2) {
  const alignedTo = Math.min(ch1.length, ch2.length);
  const delta = Math.abs(ch1.length - ch2.length);
  const channelMismatch =
    delta > 0
      ? { ch1Len: ch1.length, ch2Len: ch2.length, alignedTo, delta }
      : null;
  return {
    ch1: ch1.slice(0, alignedTo),
    ch2: ch2.slice(0, alignedTo),
    channelMismatch
  };
}

/**
 * 通过 BLE 采集指定时长 MAX30102 原始 IR
 * @param {number} durationSec
 * @param {(progress:number)=>void} onProgress
 */
export function captureBleVitals(durationSec = 10, onProgress) {
  const ch1 = [];
  const ch2 = [];
  let deviceId = '';
  const target = durationSec * DEFAULT_FS;

  return openAdapter()
    .then(() => findDevice())
    .then((device) => {
      deviceId = device.deviceId;
      return connectDevice(deviceId).then(() => device);
    })
    .then(() =>
      enableNotify(deviceId, (line) => {
        const parsed = parseLine(line);
        if (parsed.ch1 != null) ch1.push(parsed.ch1);
        if (parsed.ch2 != null) ch2.push(parsed.ch2);
        const sampleCount = Math.max(ch1.length, ch2.length);
        if (typeof onProgress === 'function') {
          onProgress(Math.min(100, Math.round((sampleCount / target) * 100)));
        }
      })
    )
    .then(
      () =>
        new Promise((resolve, reject) => {
          const start = Date.now();
          const tick = () => {
            if (Date.now() - start >= durationSec * 1000 && ch1.length >= DEFAULT_FS * 5) {
              const aligned = finalizeCapturedChannels(ch1, ch2);
              resolve({
                ch1: aligned.ch1,
                ch2: aligned.ch2,
                fs: DEFAULT_FS,
                deviceId,
                channelMismatch: aligned.channelMismatch
              });
              return;
            }
            if (Date.now() - start > (durationSec + 5) * 1000) {
              reject(new Error('采集超时，请保持静止并检查佩戴'));
              return;
            }
            setTimeout(tick, 200);
          };
          tick();
        })
    )
    .finally(() => {
      teardownBleListeners();
      if (deviceId) {
        wx.closeBLEConnection({ deviceId, complete: () => {} });
      }
      return closeAdapter();
    });
}

export { DEFAULT_FS as BLE_DEFAULT_FS };
