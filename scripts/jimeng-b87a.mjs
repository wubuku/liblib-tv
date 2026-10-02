// 批次 87 · A：审计 `organize-group-layout.md`（普查下一名，停在批次 65）。
//
// 🔴 页面第 55-58 行有一个**归因很可疑**的读数：
//
//   「工具条宽度不是固定值：同一天两次实测分别为 **511×40（缩放 74%）** 与
//     **1298×40（缩放 100%）**，**计数项也从 54×32 变成 256×40**。」
//
//   页面把宽度变化归因于**缩放**。但同一句里它也记了
//   **「计数项也变了」** —— 计数项的宽度**取决于选中集的大小/数字位数**。
//   ⇒ **「选中集不同」这个混淆变量被放过去了。**
//
// 🔑 先算一遍就知道两条解释差多远：
//   若「随缩放、canvas 恒定」：511 / 0.74 = **690.5**，而 1298 / 1 = **1298**。
//   **差 1.88 倍** ⇒ canvas 口径下这两条读数**根本不自洽**。
//   ⇒ 「同一元素随缩放」这个解释**在 canvas 口径下不成立**。
//   ⇒ 更可能：**1298×40 那次选中的节点更多**，宽度是**被选中集撑出来的**，
//     跟缩放没关系。
//
// 本轮做**受控对照**：**固定选中集（同样的节点、同样的个数）**，
// 只改缩放，量两次多选工具条。
//   · 宽度随缩放变 ⇒ 页面归因对；
//   · 宽度不变 ⇒ 页面把「选中集不同」误记成「缩放不同」。
//
// ⛔ 不点：**编组 / 解组 / 布局 / 下载**。本轮只做多选工具条的只读测量。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const selCount = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const zoomPct = async () => { const l = await p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]');
    return e ? e.getAttribute('aria-label') : null; }); return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
const readScale = async () => { const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd(); return { scale: a, stable: a !== null && a === c }; };
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return { ok: true, how: 'already' };
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
    await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
    if (a === c && a === t0) return { ok: true, how: 'input', pct: a }; }
  return { ok: false, pct: await zoomPct() }; };

/** 多选工具条：全列（`selection-context-toolbar*` 与可能的其它命名），屏上 + canvas。 */
const toolbars = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
  const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); const scale = m ? Number(m[1]) : null;
  const sels = ['[data-testid="selection-context-toolbar"]', '[data-testid^="selection-context-toolbar"]',
    '[data-testid*="selection-context"]', '[data-testid*="multiselect"]', '[data-testid*="batch"]'];
  const seen = new Set(); const out = [];
  for (const s of sels) for (const e of document.querySelectorAll(s)) {
    const r = e.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) continue;
    const k = `${e.tagName}|${e.getAttribute('data-testid')}|${Math.round(r.width)}x${Math.round(r.height)}`;
    if (seen.has(k)) continue; seen.add(k);
    out.push({ testid: e.getAttribute('data-testid'), tag: e.tagName,
      screen: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      canvas: scale ? `${Math.round(r.width / scale)}x${Math.round(r.height / scale)}` : null,
      scale, area: Math.round(r.width) * Math.round(r.height),
      text: (e.innerText || '').replace(/\n/g, ' ｜ ').slice(0, 90),
      btns: Array.from(e.querySelectorAll('button,[role="button"]')).map((x) => { const xr = x.getBoundingClientRect();
        return { t: (x.innerText || x.getAttribute('aria-label') || '').trim().replace(/\n/g, ' ').slice(0, 14),
          testid: x.getAttribute('data-testid'),
          box: `${Math.round(xr.width)}x${Math.round(xr.height)}@${Math.round(xr.x)},${Math.round(xr.y)}`,
          ariaDisabled: x.getAttribute('aria-disabled'), cursor: getComputedStyle(x).cursor }; }),
      parent: e.parentElement ? (e.parentElement.getAttribute('data-testid') || e.parentElement.className) : null }); }
  return out.sort((a, b) => b.area - a.area); });

/** 框选：找 N 个在视口内、且彼此不重叠太多��基线节点，从它们的联合包围盒外起框。 */
const marqueeN = async (N) => {
  const geo = await p.evaluate((n) => {
    const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((e) => { const r = e.getBoundingClientRect();
      return { id: e.getAttribute('data-id'), x: r.x, y: r.y, w: r.width, h: r.height,
        vis: r.x > 120 && r.y > 60 && r.x + r.width < 1240 && r.y + r.height < 700 }; }).filter((r) => r.vis);
    if (ns.length < n) return { err: `视口内只有 ${ns.length} 个节点，不够 ${n}` };
    ns.sort((a, b) => a.x - b.x);
    const pick = ns.slice(0, n);
    const x0 = Math.min(...pick.map((r) => r.x)), y0 = Math.min(...pick.map((r) => r.y));
    const x1 = Math.max(...pick.map((r) => r.x + r.w)), y1 = Math.max(...pick.map((r) => r.y + r.h));
    const pad = 24;
    const sx = Math.round(x0 - pad), sy = Math.round(y0 - pad);
    const onPane = (() => { const h = document.elementFromPoint(sx, sy); return !!(pane && h && pane.contains(h)); })();
    return { ids: pick.map((r) => r.id), from: [sx, sy], to: [Math.round(x1 + pad), Math.round(y1 + pad)], onPane, nodeBox: `${Math.round(x1 - x0)}x${Math.round(y1 - y0)}` };
  }, N);
  if (!geo || geo.err || !geo.onPane) return geo;
  await p.mouse.move(geo.from[0], geo.from[1]); await p.mouse.down();
  for (let k = 1; k <= 6; k++) { await p.mouse.move(Math.round(geo.from[0] + (geo.to[0] - geo.from[0]) * k / 6), Math.round(geo.from[1] + (geo.to[1] - geo.from[1]) * k / 6)); await p.waitForTimeout(70); }
  await p.mouse.up(); await p.waitForTimeout(1000);
  geo.selAfter = await selCount();
  return geo;
};

try {
  out.canvas = { status: await status(), zoom: await zoomPct() };
  log('进场', JSON.stringify(out.canvas));
  out.grids = [];

  // ══════ 受控对照：**固定 N=2 个节点**，只改缩放 ══════
  for (const z of [74, 100, 60, 100]) {
    const zz = await setZoom(z);
    await p.waitForTimeout(900);
    const m = await marqueeN(2);
    const bars = await toolbars();
    const rec = { zoom: await zoomPct(), setZoom: zz, marquee: m, sel: await selCount(), scale: await readScale(), bars };
    out.grids.push(rec);
    log(`── ${z}% ──`, m?.err ? m.err : `框选 ${m.selAfter} 个，工具条 ${bars.length} 个`);
    bars.slice(0, 2).forEach((t, i) => { log(`   [${i}] ${t.testid} 屏上 ${t.screen}  canvas ${t.canvas}  父 ${t.parent}`);
      log(`       文本: ${t.text}`);
      log(`       按钮: ${t.btns.map((x) => `${x.t}(${x.testid || '-'}) ${x.box}${x.ariaDisabled ? ' aria-disabled=' + x.ariaDisabled : ''}`).join(' / ')}`); });
    await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  }

  // ══════ 第二个变量：固定缩放，**变选中数**（1 / 2 / 3） ══════
  await setZoom(100); await p.waitForTimeout(900);
  out.byCount = [];
  for (const n of [1, 2, 3]) {
    const m = await marqueeN(n);
    const bars = await toolbars();
    const rec = { n, marquee: m, sel: await selCount(), zoom: await zoomPct(), bars: bars.slice(0, 1) };
    out.byCount.push(rec);
    log(`── 100% 选 ${n} 个 ──`, `sel=${rec.sel}`, bars[0] ? `工具条 屏上 ${bars[0].screen} canvas ${bars[0].canvas}｜${bars[0].text}` : '无工具条');
    await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  }

  // ══════ 判读 ══════
  const at = (z) => out.grids.find((g) => g.zoom === z && g.bars.length);
  const a74 = at(74), a100 = at(100);
  out.verdict = {};
  if (a74 && a100) {
    out.verdict.sameCount_fixedZoomCheck = { a74: a74.bars[0].screen, a100: a100.bars[0].screen,
      a74Canvas: a74.bars[0].canvas, a100Canvas: a100.bars[0].canvas,
      screenSame: a74.bars[0].screen === a100.bars[0].screen,
      screenW: [a74.bars[0].w || null, a100.bars[0].w || null] };
    log('固定 2 选中，74% vs 100%：', JSON.stringify(out.verdict.sameCount_fixedZoomCheck));
  }
  out.zoomFinal = await setZoom(60);
  out.end = { status: await status(), zoom: await zoomPct(), leftover: (await ids()).length };
  log('终态', JSON.stringify(out.end));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
writeFileSync(new URL('./_tmp-b87a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
