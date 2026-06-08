/**
 * 本地完整诊断历史（云端仅存摘要，详情存本地 Map）
 */

const FULL_KEY = 'diagnosisHistoryFull';

function readMap() {
  const map = wx.getStorageSync(FULL_KEY);
  return map && typeof map === 'object' ? map : {};
}

function writeMap(map) {
  wx.setStorageSync(FULL_KEY, map);
}

export function recordKey(item) {
  if (!item) return '';
  return String(item.id || item.timestamp || item.time || '');
}

export function saveFullRecord(record) {
  if (!record) return;
  const map = readMap();
  const normalized = {
    ...record,
    id: record.id || recordKey(record),
    timestamp: record.timestamp || record.time || ''
  };
  const keys = new Set([
    recordKey(normalized),
    normalized.id,
    normalized.timestamp,
    normalized.time
  ].filter(Boolean).map(String));
  keys.forEach((key) => {
    map[key] = { ...normalized, id: normalized.id || key };
  });
  writeMap(map);
}

export function migrateFullRecord(oldKey, record) {
  if (oldKey) removeFullRecord(oldKey);
  saveFullRecord(record);
}

export function getFullRecord(key) {
  if (!key) return null;
  const map = readMap();
  const direct = map[String(key)];
  if (direct) return direct;
  const values = Object.values(map);
  return values.find(
    (item) =>
      String(item.id) === String(key) ||
      String(item.timestamp) === String(key) ||
      String(item.time) === String(key)
  ) || null;
}

/** 将历史列表项（可能只有摘要）还原为结果页所需结构 */
export function normalizeResult(item) {
  if (!item || typeof item !== 'object') {
    return emptyResult();
  }

  const full = getFullRecord(item.id) || getFullRecord(item.timestamp) || getFullRecord(item.time);
  const src = full ? { ...full, ...item } : item;

  const syndrome = src.syndrome || '';
  const diagnosis = src.diagnosis || src.summary || syndrome || '';
  const analysis = src.analysis || src.summary || '';

  return {
    syndrome,
    diagnosis,
    analysis,
    suggestions: src.suggestions || [],
    prescriptions: src.prescriptions || [],
    face_analysis: src.face_analysis || [],
    tongue_analysis: src.tongue_analysis || [],
    eye_analysis: src.eye_analysis || [],
    fusion_summary: src.fusion_summary || '',
    diagnosis_mode: src.diagnosis_mode || '',
    llm_fallback_reason: src.llm_fallback_reason || '',
    pulse_characteristics: src.pulse_characteristics || null,
    source: src.source || '历史记录',
    disclaimer: src.disclaimer || '本诊断结果仅供参考，不能替代专业医生的诊断',
    timestamp: src.timestamp || src.time || '',
    id: src.id || ''
  };
}

export function emptyResult() {
  return {
    syndrome: '',
    diagnosis: '',
    analysis: '',
    suggestions: [],
    source: '',
    pulse_characteristics: null,
    disclaimer: '本诊断结果仅供参考，不能替代专业医生的诊断'
  };
}

/** 打开历史详情前解析完整记录 */
export function resolveHistoryItem(item) {
  return normalizeResult(item);
}

/** 合并云端 detail 与列表项 */
export function mergeEntryDetail(entry, detail) {
  if (!detail || typeof detail !== 'object') {
    return normalizeResult(entry);
  }
  return normalizeResult({
    ...detail,
    ...entry,
    id: entry.id || detail.id,
    timestamp: entry.time || entry.timestamp || detail.timestamp,
    syndrome: entry.syndrome || detail.syndrome,
    diagnosis: entry.diagnosis || detail.diagnosis || entry.summary,
    analysis: detail.analysis || entry.summary || detail.summary || ''
  });
}

/** 合并云端列表与本地完整记录 */
export function mergeHistoryEntries(entries) {
  return (entries || []).map((item) => {
    const full =
      getFullRecord(item.id) ||
      getFullRecord(item.timestamp) ||
      getFullRecord(item.time);
    let merged;
    if (full) {
      merged = {
        ...full,
        id: item.id || full.id,
        timestamp: item.time || item.timestamp || full.timestamp,
        syndrome: item.syndrome || full.syndrome,
        diagnosis: item.diagnosis || full.diagnosis || item.summary,
        has_detail: item.has_detail || full.has_detail
      };
    } else {
      merged = {
        ...item,
        timestamp: item.timestamp || item.time,
        diagnosis: item.diagnosis || item.summary || item.syndrome || '',
        analysis: item.analysis || item.summary || '',
        has_detail: !!item.has_detail
      };
    }
    if (merged.syndrome || merged.diagnosis || merged.analysis || merged.summary) {
      saveFullRecord(merged);
    }
    return merged;
  });
}

export function removeFullRecord(key) {
  if (!key) return;
  const map = readMap();
  delete map[String(key)];
  writeMap(map);
}

export function clearFullRecords() {
  wx.removeStorageSync(FULL_KEY);
}
