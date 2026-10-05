// 批次 171 f 轮：把 ≤256 宽那几档补上。
//
// e 轮结果：300 及以上都能打开，布局恒 `224×44`、不变形、不滚动；
//   **256 及以下报「Add tags 按钮不可点」** —— 左侧栏 `ASIDE[canvas-fixed-toolbar-left-rail]` 宽 160，
//   可用区只剩 96 像素，节点的 Add tags 按钮（24×24，在节点右上角）落在栏底下。
//
// 本轮换入口：**平移视口**把选中节点挪到可用区再点。
//   📌 平移只改 react-flow 的 viewport transform（**视图态**），不改任何节点数据；
//      收尾按「适配画布」把视图复原（批次 41/131 的既有做法）。
//
// 预测（接 e 轮）：宽 = min(224, 100vw−32)，门槛 **256** ⇒
//   256→224 ✅、250→**218**、220→**188**、200→**168**、180→**148**、160→**128**；
//   高恒 **44**；`scrollW > clientW` ⇒ 横向滚动条出现，末尾颜色被裁。
//   内容宽度 ≈ 7 按钮×28 + 间隙 + 内边距 ⇒ 约 224；故 **vw < 256 就一定会滚动**。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p: shared } = await openCanvas();
const p = shared;
const R = readers(p);
const rec = { 批次: '171f' };

const pin = async (page, w, h) => {
  await page.context().newCDPSession(page).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await page.waitForTimeout(900);
  const vp = await page.evaluate(() => [innerWidth, innerHeight]);
  if (vp[0] !== w || vp[1] !== h) throw new Error(`钉视口失败 ${JSON.stringify(vp)}`);
};

/** 拖动画布空白，把 dx/dy 的位移做掉（只动 viewport transform）。 */
const 平移 = async (page, dx, dy) => {
  const start = await page.evaluate(() => {
    for (let y = 60; y < innerHeight - 40; y += 12)
      for (let x = Math.min(innerWidth - 40, 200); x < innerWidth - 40; x += 12) {
        const e = document.elementFromPoint(x, y);
        if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')
            && !e.closest('aside') && !e.closest('[role=menu]')) return [x, y];
      }
    return null;
  });
  if (!start) return false;
  await page.mouse.move(start[0], start[1]);
  await page.mouse.down();
  for (let i = 1; i <= 6; i++) { await page.mouse.move(start[0] + (dx * i) / 6, start[1] + (dy * i) / 6); await page.waitForTimeout(40); }
  await page.mouse.up();
  await page.waitForTimeout(500);
  return true;
};

const 选节点并定位到可用区 = async (page, w) => {
  // 1) 找一个可点的标题
  const cands = await page.evaluate(() => {
    const out = [];
    for (const t of document.querySelectorAll('.react-flow__node [data-testid="flow-node-title"]')) {
      const r = t.getBoundingClientRect();
      const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
      if (cx < 4 || cy < 4 || cx > innerWidth - 4 || cy > innerHeight - 4) continue;
      const hit = document.elementFromPoint(cx, cy);
      if (hit && hit.closest('.react-flow__node')
          && !hit.closest('[data-testid="flow-node-target-handle"],[data-testid="flow-node-source-handle"]')) {
        out.push([Math.round(cx), Math.round(cy)]);
      }
    }
    return out;
  });
  if (!cands.length) return null;
  await page.mouse.click(cands[0][0], cands[0][1]);
  await page.waitForTimeout(800);
  if (!(await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length))) return null;
  // 2) 目标：把 Add tags 按钮挪到可用区中心（避开左栏 160 与右栏）
  const 目标x = w > 400 ? w / 2 : (160 + w) / 2;
  for (let k = 0; k < 4; k++) {
    const pos = await page.evaluate(() => {
      const e = document.querySelector('[data-testid="flow-node-selected-tag"]');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [r.x + r.width / 2, r.y + r.height / 2];
    });
    if (!pos) return null;
    const dx = 目标x - pos[0];
    if (Math.abs(dx) < 24) break;
    const ok = await 平移(page, dx, 0);
    if (!ok) return null;
  }
  return page.evaluate(() => {
    const e = document.querySelector('[data-testid="flow-node-selected-tag"]');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) return null;
    const hit = document.elementFromPoint(cx, cy);
    if (!hit || !hit.closest('[data-testid="flow-node-selected-tag"]')) return null;
    return [Math.round(cx), Math.round(cy)];
  });
};

const 读 = (page) => page.evaluate(() => {
  const e = document.querySelector('.max-w-canvas-tag-selector');
  if (!e) return null;
  const cs = getComputedStyle(e);
  const r = e.getBoundingClientRect();
  const btns = Array.from(e.querySelectorAll('button')).map((b) => {
    const q = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), 盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      完全在可视区内: q.left >= r.left - 0.5 && q.right <= r.right + 0.5 };
  });
  return { 布局宽: e.offsetWidth, 布局高: e.offsetHeight, 变换后: [Math.round(r.width), Math.round(r.height)],
    computed: { w: cs.width, h: cs.height, maxW: cs.maxWidth },
    scrollW: e.scrollWidth, clientW: e.clientWidth, 可横向滚动: e.scrollWidth > e.clientWidth + 0.5,
    按钮数: btns.length, 被裁: btns.filter((x) => !x.完全在可视区内).map((x) => x.aria) };
});

const tab = await b.contexts()[0].newPage();
await tab.goto(shared.url(), { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);

rec.档位 = [];
for (const [w, h] of [[256, 720], [250, 720], [220, 720], [200, 720], [180, 720], [160, 720], [1280, 720]]) {
  await pin(tab, w, h);
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(250);
  const pt = await 选节点并定位到可用区(tab, w);
  if (!pt) { rec.档位.push({ 视口: [w, h], 打开: false }); console.log(`  ${w}×${h}: ❌ 找不到可点的 Add tags`); continue; }
  await tab.mouse.click(pt[0], pt[1]);
  let last = -1, stable = 0;
  for (let i = 0; i < 20; i++) {
    await tab.waitForTimeout(220);
    const ww = await tab.evaluate(() => { const e = document.querySelector('.max-w-canvas-tag-selector'); return e ? e.offsetWidth : -1; });
    if (ww > 0 && ww === last) { stable++; if (stable >= 2) break; } else stable = 0;
    last = ww;
  }
  const d = await 读(tab);
  if (!d) { rec.档位.push({ 视口: [w, h], 打开: false }); console.log(`  ${w}×${h}: ❌ 点了但没开`); continue; }
  const 预测宽 = Math.min(224, Math.max(0, w - 32));
  rec.档位.push({ 视口: [w, h], 打开: true, 布局: [d.布局宽, d.布局高], computed: d.computed,
    滚动: d.可横向滚动, scrollW: d.scrollW, clientW: d.clientW, 按钮数: d.按钮数, 被裁: d.被裁, 预测宽 });
  console.log(`  ${w}×${h}: 布局 ${d.布局宽}×${d.布局高}（预测宽 ${预测宽} ${d.布局宽 === 预测宽 ? '✅' : '❌'}）` +
    ` scrollW=${d.scrollW}/client=${d.clientW} 滚动=${d.可横向滚动} 按钮数=${d.按钮数} 被裁=${JSON.stringify(d.被裁)}`);
  if (w === 200) {
    await tab.evaluate(() => {
      const e = document.querySelector('.max-w-canvas-tag-selector');
      const r = e.getBoundingClientRect();
      const d2 = document.createElement('div');
      d2.style.cssText = `position:fixed;left:${r.x - 4}px;top:${r.y - 4}px;width:${r.width + 8}px;height:${r.height + 8}px;` +
        `border:3px solid #ff8c00;border-radius:10px;pointer-events:none;z-index:2147483646`;
      document.body.appendChild(d2);
    });
    await tab.waitForTimeout(300);
    await tab.screenshot({ path: new URL('../docs/user-manual/jimeng-canvas/screenshots/134-node-tag-selector-clamped-200px.png', import.meta.url).pathname });
    rec.图 = 'screenshots/134-node-tag-selector-clamped-200px.png';
    await tab.evaluate(() => document.querySelectorAll('div[style*="2147483646"]').forEach((e) => e.remove()));
  }
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
}
await tab.close();
console.log('\n共享页签复位:', JSON.stringify(await pinViewport(shared)));
rec.收尾 = { status: await R.status(), sel: await R.selCount(), credits: await R.credits() };
console.log('收尾:', JSON.stringify(rec.收尾));
fs.writeFileSync(new URL('./_tmp-b171f.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();
