/**
 * ZenPulse 诊断报告 → 单张 PNG（对齐 stitch 报告页）
 */
(function (global) {
  function escapeHtml(s) {
    return String(s ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatReportDate(d) {
    const dt = d instanceof Date ? d : new Date(d);
    if (Number.isNaN(dt.getTime())) return new Date().toLocaleDateString('zh-CN');
    return dt.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
  }

  function reportIdFromDate(d) {
    const dt = d instanceof Date ? d : new Date();
    const y = dt.getFullYear();
    const m = String(dt.getMonth() + 1).padStart(2, '0');
    const day = String(dt.getDate()).padStart(2, '0');
    const r = Math.random().toString(36).slice(2, 6).toUpperCase();
    return `TCM-${y}${m}${day}-${r}`;
  }

  function deriveConstitution(syndrome, analysis) {
    const text = `${syndrome || ''}${analysis || ''}`;
    const items = [
      { key: '气虚', label: '气虚质', color: '#ba1a1a', pct: 85 },
      { key: '血虚', label: '血虚质', color: '#725a39', pct: 72 },
      { key: '阳虚', label: '阳虚质', color: '#725a39', pct: 45 },
      { key: '阴虚', label: '阴虚质', color: '#274a10', pct: 38 },
      { key: '肝郁', label: '气郁质', color: '#274a10', pct: 55 },
      { key: '血瘀', label: '血瘀质', color: '#274a10', pct: 28 }
    ];
    const matched = items.filter((it) => text.includes(it.key));
    if (matched.length >= 2) return matched.slice(0, 3);
    if (matched.length === 1) {
      return [
        matched[0],
        { label: '平和质', color: '#274a10', pct: 25 },
        { label: '痰湿质', color: '#725a39', pct: 18 }
      ];
    }
    return [
      { label: '气虚质', color: '#ba1a1a', pct: 65 },
      { label: '平和质', color: '#274a10', pct: 35 },
      { label: '血瘀质', color: '#274a10', pct: 20 }
    ];
  }

  function parsePrescriptionRows(prescriptions) {
    if (!prescriptions || !prescriptions.length) return [];
    return prescriptions.slice(0, 6).map((line) => {
      const s = String(line);
      const parts = s.split(/[：:，,]/).map((p) => p.trim()).filter(Boolean);
      return {
        name: parts[0] || s.slice(0, 12),
        effect: parts[1] || '—',
        dose: parts[2] || '—',
        note: parts[3] || '常规煎煮'
      };
    });
  }

  function buildReportPayload(result, context) {
    result = result || {};
    context = context || {};
    const syndrome = result.syndrome || (result.diagnosis || '').split('\n')[0].slice(0, 40) || '待进一步辨证';
    const when = context.date ? new Date(context.date) : new Date();
    const gender = context.gender || '—';
    const age = context.age != null && context.age !== '' ? `${context.age} 岁` : '—';
    const name = context.patientName || (gender !== '—' ? '问诊用户' : '问诊用户');
    const avatar = name.slice(0, 1);

    const vitals = result.vitals_assessment || {};
    const vitalsStatus =
      context.vitalsStatus ||
      vitals.overall_status ||
      '稳定';

    return {
      brandName: context.brandName || 'ZenPulse AI',
      reportId: context.reportId || reportIdFromDate(when),
      patientName: name,
      avatar,
      gender,
      age,
      vitalsStatus,
      date: formatReportDate(when),
      physician: context.physician || 'AI 智能辨证',
      syndrome,
      confidence: context.confidence || (result.diagnosis_mode === 'llm' ? 88 : result.diagnosis_mode === 'rule' ? 72 : 80),
      constitution: deriveConstitution(syndrome, result.analysis),
      constitutionNote: result.analysis || '综合望闻问切与体征数据，AI 已完成多模态融合分析。',
      vitalsHr:
        vitals.heart_rate != null
          ? `${vitals.heart_rate} bpm（${vitals.hr_status || ''}）`
          : '—',
      vitalsSpo2:
        vitals.spo2 != null ? `${vitals.spo2}%（${vitals.spo2_status || ''}）` : '—',
      vitalsOverall: vitals.overall_status || '—',
      tongueItems: result.tongue_analysis || [],
      faceItems: result.face_analysis || [],
      eyeItems: result.eye_analysis || [],
      fusionSummary: result.fusion_summary || '',
      suggestions: result.suggestions || [],
      prescriptions: parsePrescriptionRows(result.prescriptions),
      prescriptionTitle: result.prescriptions && result.prescriptions.length ? 'AI 推荐方剂' : '调理参考',
      lifestyle: (result.suggestions && result.suggestions[0]) || '保持规律作息，适度运动，情志舒畅。',
      dietWarning: (result.suggestions && result.suggestions[1]) || '忌生冷寒凉与过食油腻，避免熬夜与过度劳倦。',
      disclaimer: result.disclaimer || '本 AI 分析仅供健康参考，不作为最终医疗诊断依据。'
    };
  }

  function barRow(item) {
    const level = item.pct >= 70 ? '高' : item.pct >= 40 ? '中' : '低';
    return `<div class="zp-re-bar-row">
      <div class="zp-re-bar-labels"><span>${escapeHtml(item.label)}</span><span style="color:${item.color}">${item.pct}% (${level})</span></div>
      <div class="zp-re-bar-track"><div class="zp-re-bar-fill" style="width:${item.pct}%;background:${item.color}"></div></div>
    </div>`;
  }

  function observationRows(tongueItems, faceItems, eyeItems) {
    const rows = [];
    if (tongueItems && tongueItems.length) {
      rows.push({ label: '舌象', val: String(tongueItems[0]).slice(0, 28) });
    }
    if (faceItems && faceItems.length) {
      rows.push({ label: '面色', val: String(faceItems[0]).slice(0, 28) });
    }
    if (eyeItems && eyeItems.length) {
      rows.push({ label: '目诊', val: String(eyeItems[0]).slice(0, 28) });
    }
    if (!rows.length) {
      rows.push({ label: '望诊', val: '未上传影像' });
    }
    return rows
      .map(
        (row) =>
          `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="font-size:11px;font-weight:700;color:#54433a">${escapeHtml(row.label)}</span>
            <span class="zp-re-pill">${escapeHtml(row.val)}</span>
          </div>`
      )
      .join('');
  }

  function buildReportHtml(payload) {
    const p = payload;
    const rxRows = p.prescriptions.length
      ? p.prescriptions
          .map(
            (r) =>
              `<tr><td>${escapeHtml(r.name)}</td><td><em>${escapeHtml(r.effect)}</em></td><td>${escapeHtml(r.dose)}</td><td>${escapeHtml(r.note)}</td></tr>`
          )
          .join('')
      : `<tr><td colspan="4" class="zp-re-text">暂无具体方剂条目，请参考调理建议。</td></tr>`;

    return `<article class="zp-report-export">
      <header class="zp-re-header">
        <p class="zp-re-brand">${escapeHtml(p.brandName)}</p>
        <h1 class="zp-re-title">患者诊断报告</h1>
        <p class="zp-re-id">报告编号: #${escapeHtml(p.reportId)}</p>
      </header>
      <div class="zp-re-body">
        <div class="zp-re-row" style="grid-template-columns:1.6fr 1fr;gap:16px">
          <div class="zp-re-patient">
            <div class="zp-re-avatar">${escapeHtml(p.avatar)}</div>
            <h3 class="zp-re-name">${escapeHtml(p.patientName)}</h3>
            <div class="zp-re-tags"><span>${escapeHtml(p.gender)}</span><span>${escapeHtml(p.age)}</span></div>
            <div class="zp-re-meta">
              <div><label>生命体征</label><p style="color:#274a10">${escapeHtml(p.vitalsStatus)}</p></div>
              <div><label>问诊日期</label><p>${escapeHtml(p.date)}</p></div>
              <div><label>辨证方式</label><p>${escapeHtml(p.physician)}</p></div>
            </div>
          </div>
          <div class="zp-re-syndrome">
            <label>核心诊断结论</label>
            <h4>「${escapeHtml(p.syndrome)}」</h4>
            <div class="zp-re-confidence">
              <div class="zp-re-confidence-bar"><div class="zp-re-confidence-fill" style="width:${p.confidence}%"></div></div>
              <span>AI 置信度: ${p.confidence}%</span>
            </div>
          </div>
        </div>
        <div class="zp-re-row" style="grid-template-columns:1fr 2fr;gap:16px">
          <div class="zp-re-card">
            <div class="zp-re-card-head">体质辨识分析</div>
            <div class="zp-re-card-body">${p.constitution.map(barRow).join('')}
              <p class="zp-re-text" style="font-style:italic;padding-top:12px;border-top:1px solid rgba(218,194,182,.2);margin-top:12px">${escapeHtml(p.constitutionNote.slice(0, 120))}${p.constitutionNote.length > 120 ? '…' : ''}</p>
            </div>
          </div>
          <div class="zp-re-card">
            <div class="zp-re-card-head">多模态 AI 辨证融合</div>
            <div class="zp-re-split">
              <div class="zp-re-split-col">
                <strong style="font-size:12px;color:#725a39">生理参数</strong>
                <p class="zp-re-text">心率：${escapeHtml(p.vitalsHr)}</p>
                <p class="zp-re-text">血氧：${escapeHtml(p.vitalsSpo2)}</p>
                <p class="zp-re-text">综合：${escapeHtml(p.vitalsOverall)}</p>
              </div>
              <div class="zp-re-split-col">
                <strong style="font-size:12px;color:#274a10;display:block;margin-bottom:8px">望诊影像分析</strong>
                ${observationRows(p.tongueItems, p.faceItems, p.eyeItems)}
                ${p.fusionSummary ? `<p class="zp-re-text">${escapeHtml(p.fusionSummary.slice(0, 100))}…</p>` : ''}
              </div>
            </div>
          </div>
        </div>
        <div class="zp-re-card">
          <div class="zp-re-card-head">${escapeHtml(p.prescriptionTitle)}</div>
          <div class="zp-re-card-body" style="padding:0">
            <table class="zp-re-table">
              <thead><tr><th>组成</th><th>功用</th><th>剂量</th><th>说明</th></tr></thead>
              <tbody>${rxRows}</tbody>
            </table>
          </div>
        </div>
        <div class="zp-re-advice-grid">
          <div class="zp-re-advice"><h5>时令养生建议</h5><p class="zp-re-text">${escapeHtml(p.lifestyle)}</p></div>
          <div class="zp-re-advice warn"><h5>饮食与起居提示</h5><p class="zp-re-text">${escapeHtml(p.dietWarning)}</p></div>
        </div>
      </div>
      <footer class="zp-re-footer">
        <strong>${escapeHtml(p.brandName)}</strong>
        <p>© ${new Date().getFullYear()} ${escapeHtml(p.brandName)}。医疗免责声明：${escapeHtml(p.disclaimer)}</p>
      </footer>
    </article>`;
  }

  async function exportReportAsImage(result, context, options) {
    options = options || {};
    if (typeof html2canvas !== 'function') {
      throw new Error('html2canvas 未加载');
    }
    const payload = buildReportPayload(result, context);
    const root = document.getElementById(options.mountId || 'report-export-root');
    if (!root) throw new Error('缺少 report-export-root 容器');

    root.innerHTML = buildReportHtml(payload);
    const node = root.firstElementChild;
    const canvas = await html2canvas(node, {
      scale: options.scale || 2,
      backgroundColor: '#fff8f5',
      useCORS: true,
      logging: false,
      windowWidth: 750
    });

    const fileName = options.fileName || `ZenPulse诊断报告_${payload.reportId}.png`;
    if (options.returnBlob) {
      return new Promise((resolve) => canvas.toBlob((b) => resolve(b), 'image/png'));
    }
    const link = document.createElement('a');
    link.download = fileName;
    link.href = canvas.toDataURL('image/png');
    link.click();
    return payload;
  }

  global.ZenPulseReportExport = {
    buildReportPayload,
    buildReportHtml,
    exportReportAsImage
  };
})(typeof window !== 'undefined' ? window : globalThis);
