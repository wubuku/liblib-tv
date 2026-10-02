// 批次 78 · L：把「canvas 60×120 是常量」从**单点吻合**升级为**双点证明**，
// 并测 ⊕ 按钮是不是「屏上恒定 36×36」（若是，反向缩放变量就有了解释）。
// 背景：`docs/research/jimeng-canvas/README.md:7668` 独立记着「热区走 inline style
// （left:-30 / width:60），与 zoom 无关 ⇒ 恒为 −30..+30」，而我在 S=0.568085 下量到
// 34.09/0.568085 = 60.00 —— 机制预测与实测逐位吻合。但那只是**一个缩放档位**。
// 方法：同一节点、同一会话，显式设 50% / 100% 两档，各自读**真实 scale**再换算。
// 显式设缩放时不会再被「新建节点自动缩放」干扰（那个效应只在建节点那一刻发生一次）。
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
const out = { at: new Date().toISOString(), points: [] };
let mine = null;
const scaleOf = () => p.evaluate(() => { const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(v).transform); return m ? +(+m[1]).toFixed(6) : null; });
const settle = async () => { for (let i = 0; i < 15; i++) { const a = await scaleOf(); await p.waitForTimeout(200); const c = await scaleOf();
  if (a === c) return c; } return null; };
const setZoom = async (pct) => { await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const sl = 'input[data-testid=canvas-zoom-percent-input]';
  if (!(await p.$(sl))) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); return; }
  await p.fill(sl, String(pct)); await p.keyboard.press('Enter'); await p.waitForTimeout(1500); };
const read = (id) => p.evaluate((v) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
  if (!n) return { missing: true };
  if (!/(^|\s)selected(\s|$)/.test(n.className)) return { notSelected: true };
  const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform);
  const S = m ? +(+m[1]).toFixed(6) : null;
  // ⚠️ 自伤修正：上一版把 `w` 写成只接选择器字符串，却调用了 `w(n)`（传的是元素）
  //    ⇒ querySelector(HTMLDivElement) 直接 SyntaxError。现在两种都接。
  const w = (sel) => { const el = typeof sel === 'string' ? n.querySelector(sel) : sel; if (!el) return null;
    const b = el.getBoundingClientRect();
    return { screen: [+b.width.toFixed(2), +b.height.toFixed(2)], canvas: [+(b.width / S).toFixed(2), +(b.height / S).toFixed(2)] }; };
  const inline = (sel) => { const el = n.querySelector(sel); if (!el) return null; const cs = getComputedStyle(el);
    return { left: cs.left, width: cs.width, height: cs.height, inlineStyle: el.getAttribute('style') || '' }; };
  return { S, label: (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'),
    counterVar: getComputedStyle(n).getPropertyValue('--octo-canvas-node-chrome-counter-scale').trim(),
    node: w(n), handleBefore: w('[data-testid=flow-node-target-handle]'), handleAfter: w('[data-testid=flow-node-source-handle]'),
    plusBefore: w('[data-testid=flow-node-target-connection-menu-button]'), plusAfter: w('[data-testid=flow-node-source-connection-menu-button]'),
    handleInline: inline('[data-testid=flow-node-target-handle]') };
}, id);
try {
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^视频$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const c = (await ids()).filter((x) => !pre.includes(x));
  if (c.length !== 1) throw new Error('新建异常');
  mine = c[0]; log('新建', mine);
  for (const pct of [50, 100, 60]) {
    await setZoom(pct);
    const S = await settle(); if (S === null) throw new Error('缩放未静止 @' + pct);
    const r = await read(mine);
    if (r.notSelected) throw new Error('未选中 ⇒ VOID @' + pct);
    out.points.push({ asked: pct, ...r });
    log(`设 ${pct}% →`, JSON.stringify({ S: r.S, label: r.label, counterVar: r.counterVar,
      handle: r.handleBefore, plus: r.plusBefore, node: r.node, handleInline: r.handleInline }));
  }
  const hs = out.points.map((p) => p.handleBefore && p.handleBefore.canvas);
  const ps = out.points.map((p) => p.plusBefore && p.plusBefore.screen);
  out.verdict = {
    handleCanvasAll: hs, handleCanvasConstant: hs.every((x) => x && x[0] === hs[0][0] && x[1] === hs[0][1]),
    plusScreenAll: ps, plusScreenConstant: ps.every((x) => x && x[0] === ps[0][0] && x[1] === ps[0][1]),
    plusCanvasAll: out.points.map((p) => p.plusBefore && p.plusBefore.canvas),
    counterIsReciprocalAll: out.points.every((p) => Math.abs(+p.counterVar - 1 / p.S) < 1e-6),
  };
  log('判决', JSON.stringify(out.verdict, null, 1));
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
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  for (let t = 0; t < 3; t++) { const z = await labelOf(); if (z && z.includes('60%')) break; await setZoom(60); }
  const zf = await settle();
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c2 = cp[id]; const d = c2 && b2.canvas ? [Math.round((c2[0] - b2.canvas[0]) * 100) / 100, Math.round((c2[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  out.end = { status: await p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]),
    zoomLabel: await labelOf(), scale: zf, deviation: dev };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); if (mine && !led.ids.includes(mine)) {
    led.ids = [...new Set([...led.ids, mine])].sort();
    led.per_batch = { ...(led.per_batch || {}), 78: [...new Set([...(led.per_batch?.['78'] || []), mine])] };
    writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b78l.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
