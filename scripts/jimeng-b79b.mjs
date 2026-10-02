// 批次 79 · B：对三处与手册不符的数字做**确认轮**，并把「DOM 矩形」与「可见卡片」分开量。
// b79a 的结果：文本/导演台 320×320 ✅；时间线 **1200×207**（手册无数字）；
//   音频 320×320（手册写 240×240）；主体 352×352（手册写「约 310×310」）；
//   图片(带内容) 569×320（use-node-toolbar 写 320×427）；视频 1 = **320×569 竖版**，
//   而新建的视频节点是 569×320 横版 ⇒ 手册把「569×320」当成视频节点的固定尺寸，**可能随素材比例**。
// 三条要分清：
//   ① 320×320 / 352×352 是**节点矩形**；手册的 310 会不会其实是**可见卡片**（矩形内缩/外扩）？
//   ② 音频 240×240 是旧构建、是别的缩放下的屏上读数，还是量错了对象？⇒ 自建一个音频节点复核。
//   ③ 视频节点方向为何不同？⇒ 只读 dump 节点属性，不点任何比例设置。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const labelOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const mine = [];
const scaleOf = () => p.evaluate(() => { const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(v).transform); return m ? +(+m[1]).toFixed(6) : null; });
const settle = async () => { for (let i = 0; i < 15; i++) { const a = await scaleOf(); await p.waitForTimeout(200); const c = await scaleOf();
  if (a === c) return { scale: c, label: await labelOf(), stable: true }; } return { scale: await scaleOf(), stable: false }; };
/** 同时给三个口径：DOM 矩形 / 可见后代并集 / 带 testid 的表面层。 */
const three = (id, kind) => p.evaluate(([v, k]) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return { missing: true };
  // ⚠️ 自伤修正：上一版写成 `+exec(...)[1].toFixed(6)` —— `exec()` 的捕获组是**字符串**，
  //    没有 `.toFixed` ⇒ TypeError。必须先 `+` 转成数字再 `.toFixed`。
  const S0 = +(+(/matrix\(([-\d.]+)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform) || [])[1]).toFixed(6);
  const r = n.getBoundingClientRect();
  const px = (x) => +x.toFixed(2), cvs = (x) => +(x / S0).toFixed(2);
  const vis = Array.from(n.querySelectorAll('*')).filter((e) => { const b = e.getBoundingClientRect();
    return b.width > 1 && b.height > 1 && getComputedStyle(e).display !== 'none' && getComputedStyle(e).visibility !== 'hidden'; });
  const u = vis.map((e) => e.getBoundingClientRect()).reduce((a, b) => ({ x0: Math.min(a.x0, b.x), y0: Math.min(a.y0, b.y), x1: Math.max(a.x1, b.right), y1: Math.max(a.y1, b.bottom) }),
    { x0: r.x, y0: r.y, x1: r.right, y1: r.bottom });
  // 面积最大的可见后代 = 视觉上的「卡片本体」
  const big = vis.map((e) => ({ e, b: e.getBoundingClientRect() })).sort((a, c) => c.b.width * c.b.height - a.b.width * a.b.height)[0];
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  return { kind: k, scale: S0, attrs: Array.from(n.attributes).map((a) => `${a.name}=${a.value.slice(0, 40)}`),
    nodeRect: { screen: [px(r.width), px(r.height)], canvas: [cvs(r.width), cvs(r.height)] },
    union: { screen: [px(u.x1 - u.x0), px(u.y1 - u.y0)], canvas: [cvs(u.x1 - u.x0), cvs(u.y1 - u.y0)] },
    biggestVisible: big ? { tag: big.e.tagName, testid: big.e.getAttribute('data-testid'), cls: (big.e.getAttribute('class') || '').slice(0, 60),
      screen: [px(big.b.width), px(big.b.height)], canvas: [cvs(big.b.width), cvs(big.b.height)] } : null,
    canvasPos: t ? [+t[1], +t[2]] : null,
    title: (n.querySelector('[data-testid=flow-node-title]') || {}).innerText || (n.innerText || '').split('\n')[0] || '' };
}, [id, kind]);
const mk = async (label) => { const pre = await ids();
  const rail = await p.evaluate((L) => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => new RegExp('^' + L + '$').test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, label);
  if (!rail) throw new Error('找不到 rail：' + label);
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3200);
  const c = (await ids()).filter((x) => !pre.includes(x));
  if (c.length !== 1) throw new Error('新建异常 ' + label + '：' + JSON.stringify(c));
  mine.push(c[0]); return c[0]; };
try {
  const z0 = await settle(); log('开场 scale', JSON.stringify(z0)); out.z0 = z0;
  if (!z0.stable) throw new Error('缩放未静止');
  out.rows = [];
  // ① 只读复核既有节点
  for (const [id, rec] of Object.entries(BASE.nodes)) {
    if (!/视频|时间线/.test(rec.title || '')) continue;
    const zz = await settle(); if (!zz.stable) { log('⚠️', rec.title, 'VOID'); continue; }
    const r = await three(id, rec.title); out.rows.push({ id, source: '既有(只读)', ...r });
    log('【只读】', String(rec.title).padEnd(8), 'scale', String(zz.scale).padEnd(8),
      '矩形', JSON.stringify(r.nodeRect.canvas), '并集', JSON.stringify(r.union.canvas),
      '| 最大可见', r.biggestVisible ? `${r.biggestVisible.testid || r.biggestVisible.cls.slice(0, 22)} ${JSON.stringify(r.biggestVisible.canvas)}` : '—');
  }
  // ② 自建音频 / 主体 / 视频，各量一次
  for (const label of ['音频', '主体', '视频']) {
    const id = await mk(label);
    const zz = await settle(); if (!zz.stable) { log('⚠️', label, 'VOID'); continue; }
    const r = await three(id, label + '(自建)'); out.rows.push({ id, source: '自建', ...r });
    log('【自建】', label.padEnd(4), 'scale', String(zz.scale).padEnd(8),
      '矩形', JSON.stringify(r.nodeRect.canvas), '并集', JSON.stringify(r.union.canvas),
      '| 最大可见', r.biggestVisible ? `${r.biggestVisible.testid || r.biggestVisible.cls.slice(0, 22)} ${JSON.stringify(r.biggestVisible.canvas)}` : '—',
      '| attrs', JSON.stringify(r.attrs));
  }
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  for (const id of mine) {
    for (let a = 1; a <= 3 && (await ids()).includes(id); a++) {
      const pt = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
          const h = document.elementFromPoint(x, y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y }; } return null; }, id);
      if (!pt) break;
      await p.mouse.click(pt.x, pt.y, { button: 'right' }); await p.waitForTimeout(1000);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1500);
    }
    log('清理', id, (await ids()).includes(id) ? '🔴 仍在' : '✅');
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
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 79: [...new Set([...(led.per_batch?.['79'] || []), ...add])] };
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b79b.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
