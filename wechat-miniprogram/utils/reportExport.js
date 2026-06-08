/**
 * 小程序诊断报告 → PNG（布局对齐 stitch 报告页）
 */

function wrapText(ctx, text, x, y, maxWidth, lineHeight, maxLines) {
  const chars = String(text || '').split('');
  let line = '';
  let lines = 0;
  let cy = y;
  for (let i = 0; i < chars.length; i++) {
    const test = line + chars[i];
    if (ctx.measureText(test).width > maxWidth && line) {
      ctx.fillText(line, x, cy);
      line = chars[i];
      cy += lineHeight;
      lines += 1;
      if (maxLines && lines >= maxLines - 1) {
        ctx.fillText(line.slice(0, 20) + '…', x, cy);
        return cy + lineHeight;
      }
    } else {
      line = test;
    }
  }
  if (line) {
    ctx.fillText(line, x, cy);
    cy += lineHeight;
  }
  return cy;
}

function deriveConstitution(syndrome, analysis) {
  const text = `${syndrome || ''}${analysis || ''}`;
  const items = [
    { key: '气虚', label: '气虚质', color: '#ba1a1a', pct: 85 },
    { key: '血虚', label: '血虚质', color: '#725a39', pct: 72 },
    { key: '肝郁', label: '气郁质', color: '#274a10', pct: 55 },
    { key: '血瘀', label: '血瘀质', color: '#274a10', pct: 28 }
  ];
  const matched = items.filter((it) => text.includes(it.key));
  if (matched.length >= 2) return matched.slice(0, 3);
  if (matched.length === 1) {
    return [matched[0], { label: '平和质', color: '#274a10', pct: 25 }];
  }
  return [
    { label: '气虚质', color: '#ba1a1a', pct: 65 },
    { label: '平和质', color: '#274a10', pct: 35 }
  ];
}

export function buildReportPayload(result, context) {
  result = result || {};
  context = context || {};
  const syndrome = result.syndrome || (result.diagnosis || '').split('\n')[0].slice(0, 36) || '待辨证';
  const when = context.date ? new Date(context.date) : new Date();
  const y = when.getFullYear();
  const m = String(when.getMonth() + 1).padStart(2, '0');
  const d = String(when.getDate()).padStart(2, '0');
  const r = Math.random().toString(36).slice(2, 6).toUpperCase();

  return {
    brandName: context.brandName || 'ZenPulse AI',
    reportId: context.reportId || `TCM-${y}${m}${d}-${r}`,
    patientName: context.patientName || '问诊用户',
    avatar: (context.patientName || '问').slice(0, 1),
    gender: context.gender || '—',
    age: context.age != null && context.age !== '' ? `${context.age} 岁` : '—',
    vitalsStatus: context.vitalsStatus || '稳定',
    date: `${y}年${parseInt(m, 10)}月${parseInt(d, 10)}日`,
    physician: 'AI 智能辨证',
    syndrome,
    confidence: result.diagnosis_mode === 'llm' ? 88 : result.diagnosis_mode === 'rule' ? 72 : 80,
    constitution: deriveConstitution(syndrome, result.analysis),
    constitutionNote: (result.analysis || '综合体征与望诊数据完成 AI 辨证。').slice(0, 100),
    pulseType: (result.pulse_characteristics && result.pulse_characteristics.pulse_type) || '—',
    pulseDesc: (result.pulse_characteristics && result.pulse_characteristics.description) || '—',
    tongueItems: result.tongue_analysis || [],
    faceItems: result.face_analysis || [],
    suggestions: result.suggestions || [],
    prescriptions: result.prescriptions || [],
    lifestyle: (result.suggestions && result.suggestions[0]) || '保持规律作息，适度运动。',
    dietWarning: (result.suggestions && result.suggestions[1]) || '忌生冷油腻，避免熬夜。',
    disclaimer: result.disclaimer || '本 AI 分析仅供健康参考，不作为最终医疗诊断依据。'
  };
}

function estimateHeight(payload) {
  let h = 1200;
  h += payload.suggestions.length * 24;
  h += payload.prescriptions.length * 28;
  return Math.min(Math.max(h, 1400), 2400);
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

export function drawReport(ctx, payload, width) {
  const W = width || 750;
  const pad = 32;
  let y = 0;

  ctx.fillStyle = '#fff8f5';
  ctx.fillRect(0, 0, W, estimateHeight(payload));

  ctx.fillStyle = '#6c2f00';
  ctx.font = 'bold 22px sans-serif';
  ctx.fillText(payload.brandName, pad, 48);
  ctx.font = '600 28px serif';
  ctx.fillText('患者诊断报告', pad, 88);
  ctx.fillStyle = '#54433a';
  ctx.font = '12px sans-serif';
  ctx.fillText(`报告编号: #${payload.reportId}`, pad, 112);
  y = 130;

  ctx.strokeStyle = 'rgba(218,194,182,.5)';
  ctx.beginPath();
  ctx.moveTo(pad, y);
  ctx.lineTo(W - pad, y);
  ctx.stroke();
  y += 24;

  roundRect(ctx, pad, y, W - pad * 2 - 200, 160, 15);
  ctx.fillStyle = '#ffffff';
  ctx.fill();
  ctx.strokeStyle = 'rgba(218,194,182,.35)';
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(pad + 52, y + 56, 36, 0, Math.PI * 2);
  ctx.fillStyle = '#fbdbb0';
  ctx.fill();
  ctx.fillStyle = '#725a39';
  ctx.font = 'bold 28px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(payload.avatar, pad + 52, y + 66);
  ctx.textAlign = 'left';

  ctx.fillStyle = '#29180a';
  ctx.font = '600 26px serif';
  ctx.fillText(payload.patientName, pad + 100, y + 44);
  ctx.font = '11px sans-serif';
  ctx.fillStyle = '#54433a';
  ctx.fillText(`${payload.gender}  ${payload.age}`, pad + 100, y + 68);
  ctx.font = '12px sans-serif';
  ctx.fillText(`生命体征: ${payload.vitalsStatus}`, pad + 100, y + 100);
  ctx.fillText(`问诊日期: ${payload.date}`, pad + 280, y + 100);
  ctx.fillText(`方式: ${payload.physician}`, pad + 480, y + 100);

  const sx = W - pad - 180;
  roundRect(ctx, sx, y, 180, 160, 15);
  ctx.fillStyle = '#6c2f00';
  ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.85)';
  ctx.font = '10px sans-serif';
  ctx.fillText('核心诊断结论', sx + 16, y + 28);
  ctx.fillStyle = '#ffffff';
  ctx.font = 'italic 20px serif';
  wrapText(ctx, `「${payload.syndrome}」`, sx + 16, y + 58, 148, 26, 3);
  ctx.fillStyle = '#feddb3';
  roundRect(ctx, sx + 16, y + 130, 100, 6, 3);
  ctx.fill();
  ctx.fillStyle = '#fff';
  ctx.font = 'bold 11px sans-serif';
  ctx.fillText(`AI ${payload.confidence}%`, sx + 122, y + 136);

  y += 180;

  roundRect(ctx, pad, y, (W - pad * 2) * 0.38, 220, 15);
  ctx.fillStyle = '#fff';
  ctx.fill();
  ctx.strokeStyle = 'rgba(218,194,182,.35)';
  ctx.stroke();
  ctx.fillStyle = '#6c2f00';
  ctx.font = 'bold 12px sans-serif';
  ctx.fillText('体质辨识分析', pad + 16, y + 36);
  let by = y + 56;
  payload.constitution.forEach((item) => {
    ctx.fillStyle = '#29180a';
    ctx.font = '11px sans-serif';
    ctx.fillText(item.label, pad + 16, by);
    ctx.fillText(`${item.pct}%`, pad + 200, by);
    roundRect(ctx, pad + 16, by + 6, 240, 8, 4);
    ctx.fillStyle = '#fedcc5';
    ctx.fill();
    roundRect(ctx, pad + 16, by + 6, (240 * item.pct) / 100, 8, 4);
    ctx.fillStyle = item.color;
    ctx.fill();
    by += 36;
  });
  ctx.fillStyle = '#54433a';
  ctx.font = '12px sans-serif';
  wrapText(ctx, payload.constitutionNote, pad + 16, by + 8, 240, 18, 3);

  const rx = pad + (W - pad * 2) * 0.42;
  const rw = W - pad - rx;
  roundRect(ctx, rx, y, rw, 220, 15);
  ctx.fillStyle = '#fff';
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = '#6c2f00';
  ctx.font = 'bold 12px sans-serif';
  ctx.fillText('多模态 AI 辨证融合', rx + 16, y + 36);
  ctx.fillStyle = '#725a39';
  ctx.font = '12px sans-serif';
  ctx.fillText(`脉象: ${payload.pulseType}`, rx + 16, y + 64);
  ctx.fillStyle = '#54433a';
  wrapText(ctx, payload.pulseDesc, rx + 16, y + 88, rw - 32, 18, 4);
  ctx.fillStyle = '#274a10';
  ctx.fillText('望诊摘要', rx + 16, y + 160);
  const obs = [...payload.tongueItems, ...payload.faceItems].slice(0, 2);
  wrapText(ctx, obs.join(' · ') || '—', rx + 16, y + 184, rw - 32, 18, 2);

  y += 240;

  roundRect(ctx, pad, y, W - pad * 2, 180, 15);
  ctx.fillStyle = '#fff';
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = '#6c2f00';
  ctx.font = 'bold 12px sans-serif';
  ctx.fillText('调理与方剂建议', pad + 16, y + 32);
  let py = y + 52;
  if (payload.prescriptions.length) {
    payload.prescriptions.slice(0, 4).forEach((line) => {
      ctx.fillStyle = '#6c2f00';
      ctx.font = '12px sans-serif';
      py = wrapText(ctx, `· ${String(line).slice(0, 60)}`, pad + 16, py, W - pad * 2 - 32, 20, 1);
    });
  } else if (payload.suggestions.length) {
    payload.suggestions.slice(0, 4).forEach((line) => {
      py = wrapText(ctx, `· ${line}`, pad + 16, py, W - pad * 2 - 32, 20, 1);
    });
  } else {
    ctx.fillStyle = '#54433a';
    ctx.fillText('请参考上方核心诊断结论与脉象分析。', pad + 16, py + 16);
    py += 32;
  }

  y += 200;

  roundRect(ctx, pad, y, (W - pad * 2 - 16) / 2, 120, 15);
  ctx.fillStyle = '#fff1e9';
  ctx.fill();
  ctx.fillStyle = '#274a10';
  ctx.font = '600 16px serif';
  ctx.fillText('时令养生建议', pad + 16, y + 32);
  ctx.fillStyle = '#54433a';
  ctx.font = '12px sans-serif';
  wrapText(ctx, payload.lifestyle, pad + 16, y + 56, (W - pad * 2 - 16) / 2 - 32, 18, 3);

  const ax = pad + (W - pad * 2 - 16) / 2 + 16;
  roundRect(ctx, ax, y, (W - pad * 2 - 16) / 2, 120, 15);
  ctx.fillStyle = '#fff1e9';
  ctx.fill();
  ctx.fillStyle = '#ba1a1a';
  ctx.font = '600 16px serif';
  ctx.fillText('饮食与起居提示', ax + 16, y + 32);
  ctx.fillStyle = '#54433a';
  wrapText(ctx, payload.dietWarning, ax + 16, y + 56, (W - pad * 2 - 16) / 2 - 32, 18, 3);

  y += 140;

  ctx.fillStyle = '#f5d4bd';
  ctx.fillRect(0, y, W, 100);
  ctx.fillStyle = '#6c2f00';
  ctx.font = 'bold 12px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(payload.brandName, W / 2, y + 32);
  ctx.fillStyle = '#54433a';
  ctx.font = '10px sans-serif';
  wrapText(ctx, `免责声明：${payload.disclaimer}`, pad, y + 52, W - pad * 2, 14, 3);
  ctx.textAlign = 'left';

  return y + 100;
}

export function exportReportImage(page, canvasId, result, context) {
  const payload = buildReportPayload(result, context);
  const height = estimateHeight(payload);

  return new Promise((resolve, reject) => {
    const query = page.createSelectorQuery();
    query
      .select(`#${canvasId}`)
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res || !res[0] || !res[0].node) {
          reject(new Error('Canvas 未就绪'));
          return;
        }
        const canvas = res[0].node;
        const dpr = wx.getSystemInfoSync().pixelRatio || 2;
        canvas.width = 750 * dpr;
        canvas.height = height * dpr;
        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        drawReport(ctx, payload, 750);

        wx.canvasToTempFilePath({
          canvas,
          x: 0,
          y: 0,
          width: 750 * dpr,
          height: height * dpr,
          destWidth: 750 * 2,
          destHeight: height * 2,
          fileType: 'png',
          success: (r) => resolve({ tempFilePath: r.tempFilePath, payload }),
          fail: reject
        });
      });
  });
}

export function saveReportToAlbum(page, canvasId, result, context) {
  return exportReportImage(page, canvasId, result, context).then(({ tempFilePath }) => {
    return new Promise((resolve, reject) => {
      wx.saveImageToPhotosAlbum({
        filePath: tempFilePath,
        success: resolve,
        fail: (err) => {
          if (err.errMsg && err.errMsg.includes('auth deny')) {
            reject(new Error('需要相册权限，请在设置中允许保存图片'));
          } else {
            reject(err);
          }
        }
      });
    });
  });
}
