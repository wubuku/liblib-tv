// 批次 79 · A：全册「节点 canvas 尺寸」审计。
// 批次 78 证明了「屏上 ÷ 写死的 0.6」是系统性错误。这一批把同一手法用完：
// **同会话、同一 scale、逐类量节点本体**，核对手册里每一处节点尺寸说法。
// 手册现有说法（读者页）：
//   文本/导演台 320×320 ｜ 视频 569×320 ｜ 主体 约 310×310
//   音频 240×240（audio-node-voice.md:186）｜ 带内容图片 320×427（use-node-toolbar.md:103）
//   create-first-node.md:81「卡片尺寸 341×192」—— 疑似 569×320 在 60% 下的**屏上**尺寸，未标单位
// 方法：节点本体尺寸**不需要选中**就能读，所以除「主体」外全部**只读**他人既有节点，
//        只新建 1 个自建主体节点。绝不触碰他人节点。
// 除数：当场连读两次真实 scale（相同才算静止），**绝不写死 0.6**。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const EXT = BASE._external_nodes || {};
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const labelOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), nodes: [], claimCheck: {} };
let mine = null;
const scaleOf = () => p.evaluate(() => { const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(v).transform); return m ? +(+m[1]).toFixed(6) : null; });
const settle = async () => { for (let i = 0; i < 15; i++) { const a = await scaleOf(); await p.waitForTimeout(200); const c = await scaleOf();
  if (a === c) return { scale: c, label: await labelOf() }; } return { scale: await scaleOf(), label: await labelOf(), unstable: true }; };
/** 只读量一个节点本体。** 不点、不选中、不改任何东西。 */
const measure = (id, kind, note) => p.evaluate(([v, k, nt]) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return { missing: true };
  const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform);
  const S = m ? +(+m[1]).toFixed(6) : null; if (S === null) return { noScale: true };
  const r = n.getBoundingClientRect();
  // 本体：优先取 testid 命名的表面层，取不到就用节点矩形
  const surf = n.querySelector('[data-testid=video-flow-node-surface], [data-testid=audio-flow-node-surface], [data-testid=image-flow-node-surface], [data-testid=subject-flow-node-surface]');
  const b = surf ? surf.getBoundingClientRect() : r;
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  return { kind: k, note: nt, scale: S,
    className: n.className.replace('react-flow__node react-flow__node-', '').split(' ').slice(0, 4).join(' '),
    title: (n.querySelector('[data-testid=flow-node-title]') || {}).innerText || (n.innerText || '').split('\n')[0] || '',
    usedSurface: !!surf, surfaceTestId: surf ? surf.getAttribute('data-testid') : null,
    nodeScreen: [+r.width.toFixed(2), +r.height.toFixed(2)], nodeCanvas: [+(r.width / S).toFixed(2), +(r.height / S).toFixed(2)],
    bodyScreen: [+b.width.toFixed(2), +b.height.toFixed(2)], bodyCanvas: [+(b.width / S).toFixed(2), +(b.height / S).toFixed(2)],
    ratio: +(b.width / b.height).toFixed(4),
    canvasPos: t ? [+t[1], +t[2]] : null,
    innerTextHead: (n.innerText || '').split('\n').filter(Boolean).slice(0, 2) };
}, [id, kind, note || '']);
try {
  const z = await settle(); log('scale', JSON.stringify(z)); out.scale = z;
  if (z.unstable) throw new Error('缩放未静止 ⇒ 读数作废(VOID)');
  const all = await ids();
  const titleOf = async (id) => (await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    return n ? ((n.querySelector('[data-testid=flow-node-title]') || {}).innerText || (n.innerText || '').split('\n')[0] || '') : null; }, id)) || '';
  // —— 按标题分类挑代表节点（只读）
  const wanted = { '文本': 0, '视频': 0, '时间线': 0, '导演台': 0, '图片': 0, '音频': 0, '主体': 0 };
  const picks = [];
  for (const id of all) {
    const t = await titleOf(id);
    const kind = Object.keys(wanted).find((k) => t.includes(k) && !wanted[k]);
    if (kind) { wanted[kind] = 1; picks.push({ id, kind, title: t, mine: false, note: '' }); }
  }
  // b22-upload（他人建的带内容图片节点）单独挑出来
  for (const [id, rec] of Object.entries(EXT)) if (/b22-upload/.test(rec.title || '') && all.includes(id) && !picks.some((x) => x.id === id))
    picks.push({ id, kind: '图片(带内容)', title: rec.title, mine: false, note: '他人建的，只读' });
  // —— 主体：画布上没有，新建 1 个自建的
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^主体$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!rail) throw new Error('左栏找不到「主体」按钮');
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3200);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建主体异常：' + JSON.stringify(made));
  mine = made[0];
  picks.push({ id: mine, kind: '主体', title: await titleOf(mine), mine: true, note: '自建' });
  const z2 = await settle(); log('建主体后 scale', JSON.stringify(z2)); out.scaleAfterCreate = z2;
  // —— 逐个量（scale 可能有变，每个都重读一次）
  for (const pk of picks) {
    const zz = await settle();
    if (zz.unstable) { log('⚠️', pk.kind, '缩放未稳定，跳过（VOID）'); continue; }
    const m = await measure(pk.id, pk.kind, pk.note);
    out.nodes.push({ ...pk, scaleAtMeasure: zz.scale, zoomLabelAtMeasure: zz.label, ...m });
    log(pk.kind.padEnd(12), 'scale', String(zz.scale).padEnd(9), 'canvas', JSON.stringify(m.bodyCanvas), '| 屏上', JSON.stringify(m.bodyScreen),
      '| testid', m.surfaceTestId, '|', m.title);
  }
  // —— 与手册现有说法对照
  const manual = { '文本': '320×320', '视频': '569×320', '时间线': '?', '导演台': '320×320', '图片': '?', '音频': '240×240', '主体': '约 310×310', '图片(带内容)': '320×427' };
  for (const n of out.nodes) {
    const got = n.bodyCanvas ? `${Math.round(n.bodyCanvas[0])}×${Math.round(n.bodyCanvas[1])}` : '?';
    const cmp = (() => { const w = manual[n.kind]; if (!w || w === '?') return '手册无数字';
      const m = /(\d+)×(\d+)/.exec(w); if (!m) return '手册说法非数字';
      const d = [Math.abs(n.bodyCanvas[0] - +m[1]), Math.abs(n.bodyCanvas[1] - +m[2])];
      return d[0] <= 1.5 && d[1] <= 1.5 ? '✅ 一致' : `❌ 差 ${d.map((x) => x.toFixed(1)).join(' / ')}`; })();
    out.claimCheck[n.kind] = { manual: manual[n.kind], measured: got, verdict: cmp, scale: n.scaleAtMeasure };
    log('对照', n.kind.padEnd(12), '手册', String(manual[n.kind]).padEnd(12), '实测', got.padEnd(12), cmp);
  }
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  if (mine && (await ids()).includes(mine)) {
    for (let a = 1; a <= 3 && (await ids()).includes(mine); a++) {
      const pt = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
          const h = document.elementFromPoint(x, y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y }; } return null; }, mine);
      if (!pt) break;
      await p.mouse.click(pt.x, pt.y, { button: 'right' }); await p.waitForTimeout(1000);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1500);
    }
    log('清理', mine, (await ids()).includes(mine) ? '🔴 仍在' : '✅');
  }
  for (let t = 0; t < 3; t++) { const z = await labelOf(); if (z && z.includes('60%')) break;
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const sl = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(sl)) { await p.fill(sl, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1400); } else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  const zf = await settle();
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  out.end = { status: await p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]),
    zoomLabel: await labelOf(), scale: zf.scale, deviation: dev };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); if (mine && !led.ids.includes(mine)) {
    led.ids = [...new Set([...led.ids, mine])].sort();
    led.per_batch = { ...(led.per_batch || {}), 79: [...new Set([...(led.per_batch?.['79'] || []), mine])] };
    writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b79.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
