// Copyright (c) 2026 paidaxin-12138
// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
// https://creativecommons.org/licenses/by-nc/4.0/

/**
 * 腕带 PPG 采集辅助（演示 / 未来接 ESP32 数据）
 */

const DEFAULT_FS = 100;

/** 与后端 synthetic_pulse_waveform 一致的演示波形 */
export function generateDemoWaveform(durationSec = 20, fs = DEFAULT_FS, bpm = 72) {
  const samples = [];
  const n = Math.floor(durationSec * fs);
  const period = 60 / bpm;
  for (let i = 0; i < n; i += 1) {
    const t = i / fs;
    const phase = (t % period) / period;
    const beat = 300 * Math.max(0, Math.sin(Math.PI * phase)) ** 1.5;
    samples.push(1000 + beat + 10 * Math.sin(t * 13.7));
  }
  return samples;
}

/** 将 API 波形降采样为 Canvas 折线点（0–1） */
export function downsampleForPreview(waveform, maxPoints = 80) {
  if (!waveform || !waveform.length) return [];
  const step = Math.max(Math.floor(waveform.length / maxPoints), 1);
  const picked = [];
  for (let i = 0; i < waveform.length; i += step) {
    picked.push(waveform[i]);
  }
  const min = Math.min(...picked);
  const max = Math.max(...picked);
  const span = max - min || 1;
  return picked.map((v) => (v - min) / span);
}

export function rhythmLabel(characteristics) {
  if (!characteristics) return '';
  const parts = [];
  if (characteristics.rate) parts.push(`率：${characteristics.rate}`);
  if (characteristics.rhythm) parts.push(`节律：${characteristics.rhythm}`);
  return parts.join(' · ');
}

export { DEFAULT_FS };
