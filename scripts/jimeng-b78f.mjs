// 批次 78 · F：先把「缩放百分比 → viewport matrix scale」的换算钉死。
// 起因：b78e 读到缩放控件写「60%」，而 .react-flow__viewport 的 computed transform 是
//       matrix(0.568085, …)。此前手册里所有「canvas 像素」都是拿屏上读数 ÷ 0.6 算的
//       ——如果真值是 0.568，那是一串 5.6% 的系统性误差。
// 三件事一起问（老规矩：范围对吗 / 时机对吗 / 判据对吗）：
//   ① inline style 写的到底是 scale(0.6) 还是 scale(0.568085)？（computed ≠ inline 说明有人覆盖）
//   ② 50% / 60% / 100% 三个点上，percent → scale 是不是线性的？截距是不是 0？
//   ③ 用一个**已知 canvas 尺寸**的元素反查，验证换算式。
// 只动视图缩放（不动任何节点/连线），量完归位 60%。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const readZoom = () => p.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const btn = document.querySelector('button[aria-label^="Zoom options"]');
  const sl = document.querySelector('input[data-testid=canvas-zoom-percent-input]');
  const cs = getComputedStyle(v);
  const m = /matrix\(([-\d.]+),\s*[-\d.]+,\s*[-\d.]+,\s*([-\d.]+)/.exec(cs.transform);
  return { aria: btn ? btn.getAttribute('aria-label') : null, inputValue: sl ? sl.value : null,
    inlineTransform: v.style.transform, computedTransform: cs.transform,
    scaleX: m ? +(+m[1]).toFixed(6) : null, scaleY: m ? +(+m[2]).toFixed(6) : null,
    dpr: devicePixelRatio, innerWidth, innerHeight };
});
const setZoom = async (pct) => {
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const sl = 'input[data-testid=canvas-zoom-percent-input]';
  if (!(await p.$(sl))) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); return null; }
  await p.fill(sl, String(pct)); await p.keyboard.press('Enter'); await p.waitForTimeout(1200);
  return readZoom();
};
try {
  log('原始', JSON.stringify(await readZoom()));
  out.p60 = await readZoom();
  const pts = [{ pct: 100 }, { pct: 50 }, { pct: 60 }];
  out.series = [];
  for (const { pct } of pts) {
    const r = await setZoom(pct);
    out.series.push(r); log('设为', pct, '→', JSON.stringify(r));
  }
  // 线性回归 scale = k * (pct/100)
  const xs = out.series.map((r) => +((r.inputValue || 0) / 100)), ys = out.series.map((r) => r.scaleX);
  const n = xs.length, sx = xs.reduce((a, x) => a + x, 0), sy = ys.reduce((a, y) => a + y, 0);
  const sxy = xs.reduce((a, x, i) => a + x * ys[i], 0), sxx = xs.reduce((a, x) => a + x * x, 0);
  const k = (n * sxy - sx * sy) / (n * sxx - sx * sx), c = (sy - k * sx) / n;
  out.fit = { k: +k.toFixed(6), intercept: +c.toFixed(6), points: out.series.map((r) => [r.inputValue, r.scaleX]) };
  log('拟合 scale = k*(pct/100) + c ⇒', JSON.stringify(out.fit));

  // ① 已知 canvas 尺寸反查：用节点 inline transform（canvas 空间，与缩放无关）× scale 与屏上读数对照
  const v1 = Object.entries(BASE.nodes).find(([, v]) => /视频/.test(v.title || ''))[0];
  out.verify = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    if (!n) return { missing: true };
    const vp = document.querySelector('.react-flow__viewport');
    const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(vp).transform);
    const s = m ? +m[1] : null;
    const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
    const canvasPos = t ? [+t[1], +t[2]] : null;
    const r = n.getBoundingClientRect();
    const surf = n.querySelector('[data-testid=video-flow-node-surface]');
    const sr = surf ? surf.getBoundingClientRect() : null;
    return { scale: s, canvasPos, screenTopLeft: [Math.round(r.x), Math.round(r.y)],
      screenSize: [+r.width.toFixed(2), +r.height.toFixed(2)],
      // 用 translate 反推：canvasPos*scale + pan 应等于 screenTopLeft
      vpMatrix: getComputedStyle(vp).transform,
      surfaceScreen: sr ? [+sr.width.toFixed(2), +sr.height.toFixed(2)] : null };
  }, v1);
  log('反查', JSON.stringify(out.verify));
  out.verifyImpliedScale = out.verify.canvasPos && out.verify.screenTopLeft
    ? +(((out.verify.screenTopLeft[0] - out.verify.canvasPos[0] * out.verify.scale) === 0) ? 0 : 0).toFixed(6) : null;
  // ①2 标题行相对节点矩形的位置（上一版才发现它在矩形外）
  out.titleGeo = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return { missing: true };
    const r = n.getBoundingClientRect();
    const rel = (sel) => { const e = n.querySelector(sel); if (!e) return null; const b = e.getBoundingClientRect();
      return { sel, screen: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
        relTop: Math.round(b.y - r.y), relLeft: Math.round(b.x - r.x) }; };
    // 节点自身**可见**后代的并集（排除 1x1 的 sr-only）
    const all = Array.from(n.querySelectorAll('*')).filter((e) => { const b = e.getBoundingClientRect();
      return b.width > 1 && b.height > 1 && getComputedStyle(e).display !== 'none'; })
      .map((e) => e.getBoundingClientRect());
    const u = all.reduce((a, b) => ({ x0: Math.min(a.x0, b.x), y0: Math.min(a.y0, b.y), x1: Math.max(a.x1, b.right), y1: Math.max(a.y1, b.bottom) }),
      { x0: r.x, y0: r.y, x1: r.right, y1: r.bottom });
    return { node: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      title: rel('[data-testid=flow-node-title]'),
      rename: rel('[data-testid=flow-node-rename-button]'),
      beforeBtn: rel('[data-testid=flow-node-target-connection-menu-button]'),
      afterBtn: rel('[data-testid=flow-node-source-connection-menu-button]'),
      empty: rel('[data-testid=video-node-empty]'),
      union: [Math.round(u.x0), Math.round(u.y0), Math.round(u.x1 - u.x0), Math.round(u.y1 - u.y0)] };
  }, v1);
  log('几何', JSON.stringify(out.titleGeo, null, 1));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let t = 0; t < 3; t++) { const r = await readZoom(); if (r.aria && r.aria.includes('60%')) break; await setZoom(60); }
  const f = await readZoom(); out.final = f; log('归位', JSON.stringify(f));
  writeFileSync(new URL('./_tmp-b78f.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
