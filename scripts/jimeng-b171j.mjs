// 批次 171 j 轮：换打法 —— **先把面板打开，再改视口**。
//
// 🔴 i 轮及其前面几轮连续失败（f/g/h/i �� 30+ 档），根因是同一个：
//    **直接 `setAttribute` 改 `.react-flow__viewport` 的 transform 会被 react-flow 覆盖**
//    （它的内部状态还是旧值，下一次渲染就把 transform 写回去）
//    ⇒ 点下去时元素已经回到原处，`elementFromPoint` 命中 null / 点了没选中。
//    📌 要改视图必须走**应用自己的入口**（缩放控件 / 适配画布 / 拖画布），
//      直接改 DOM style 这条路在 react-flow 上不通 —— 立规 43。
//
// 本轮的做法完全绕开这个问题：
//   ① 在 **1280×720** 下把标签选择器**打开**（这一步已复现成功，c/d 轮都成过）
//   ② 然后**只改视口**，不碰画布、不做任何交互
//   ③ 读 `offsetWidth`
//   ④ 这测的**正是 CSS**：`max-width:calc(100vw - 32px)` 会随视口重算 ——
//      批次 170 的 k 轮已经证明过夹取是纯 CSS 行为（`setDeviceMetricsOverride` 后无需交互即生效）。
//
// 预测：宽 = min(224, 100vw−32)，门槛 256 ⇒ 256→224 / 250→218 / 220→188 / 200→168 / 180→148 / 160→128；
//   高恒 44；vw<256 时 `scrollWidth > clientWidth` ⇒ 横向滚动、末尾颜色被裁。
//
// ⛔ 不点任何颜色按钮。收尾 pinViewport 复位共享页签。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const DIR = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url).pathname;
const { b, p: shared } = await openCanvas();
const p = shared;
const R = readers(p);
const rec = { 批次: '171j' };

const pin = async (w, h) => {
  await p.context().newCDPSession(p).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await p.waitForTimeout(700);
  const vp = await p.evaluate(() => [innerWidth, innerHeight]);
  if (vp[0] !== w || vp[1] !== h) throw new Error(`钉视口失败 ${JSON.stringify(vp)}`);
};

const 读 = () => p.evaluate(() => {
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
    内边距: cs.padding, 间隙: cs.gap, 按钮数: btns.length, 按钮: btns,
    被裁: btns.filter((x) => !x.完全在可视区内).map((x) => x.aria) };
});

// ① 复原起点 + 打开标签选择器
await pinViewport(p);
await p.keyboard.press('Escape'); await p.waitForTimeout(300);
let bp = await p.evaluate(() => {
  for (let y = 30; y < innerHeight - 30; y += 10)
    for (let x = 30; x < innerWidth - 30; x += 10) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  return null;
});
if (bp) { await p.mouse.click(bp[0], bp[1]); await p.waitForTimeout(600); }
rec.起点 = { status: await R.status(), sel: await R.selCount() };
console.log('起点:', JSON.stringify(rec.起点));

// 选节点 → 点 Add tags（c 轮复现过的路径）
const sel = await p.evaluate(() => {
  for (const t of document.querySelectorAll('.react-flow__node [data-testid="flow-node-title"]')) {
    const r = t.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    if (cx < 4 || cy < 4 || cx > innerWidth - 4 || cy > innerHeight - 4) continue;
    const hit = document.elementFromPoint(cx, cy);
    if (hit && hit.closest('.react-flow__node') && !hit.closest('[data-testid^=flow-node-target],[data-testid^=flow-node-source]')) {
      return { pt: [Math.round(cx), Math.round(cy)], 文字: (t.innerText || '').trim().slice(0, 10) };
    }
  }
  return null;
});
if (!sel) { console.log('选不中节点，放弃'); await b.close(); process.exit(0); }
await p.mouse.click(sel.pt[0], sel.pt[1]);
await p.waitForTimeout(900);
rec.选中 = { ...sel, sel: await R.selCount() };
const tag = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="flow-node-selected-tag"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});
if (!tag) { console.log('没有 Add tags'); await b.close(); process.exit(0); }
await p.mouse.click(tag[0], tag[1]);
await p.waitForTimeout(1600);
const opened = await p.evaluate(() => !!document.querySelector('.max-w-canvas-tag-selector'));
console.log('标签条已打开 =', opened, '｜ 选中 =', JSON.stringify(rec.选中));
if (!opened) { console.log('没打开，放弃'); await b.close(); process.exit(0); }

// ② 只改视口，逐档读
rec.档位 = [];
for (const [w, h] of [[1280, 720], [400, 720], [300, 720], [256, 720], [250, 720], [240, 720], [220, 720], [200, 720], [180, 720], [160, 720], [1280, 300], [1280, 200]]) {
  await pin(w, h);
  const d = await 读();
  if (!d) { rec.档位.push({ 视口: [w, h], 还在: false }); console.log(`  ${w}×${h}: 面板没了`); continue; }
  const 预测宽 = Math.min(224, Math.max(0, w - 32));
  rec.档位.push({ 视口: [w, h], 布局: [d.布局宽, d.布局高], computed: d.computed,
    滚动: d.可横向滚动, scrollW: d.scrollW, clientW: d.clientW, 按钮数: d.按钮数, 被裁: d.被裁, 预测宽 });
  console.log(`  ${w}×${h}: 布局 ${d.布局宽}×${d.布局高}（预测宽 ${预测宽} ${d.布局宽 === 预测宽 ? '✅' : '❌'}）` +
    ` scrollW=${d.scrollW}/client=${d.clientW} 滚动=${d.可横向滚动} 按钮数=${d.按钮数} 被裁=${JSON.stringify(d.被裁)}`);

  if (w === 200) {
    await p.evaluate(() => {
      const e = document.querySelector('.max-w-canvas-tag-selector');
      const r = e.getBoundingClientRect();
      const d2 = document.createElement('div');
      d2.style.cssText = `position:fixed;left:${r.x - 4}px;top:${r.y - 4}px;width:${r.width + 8}px;height:${r.height + 8}px;` +
        `border:3px solid #ff8c00;border-radius:10px;pointer-events:none;z-index:2147483646`;
      document.body.appendChild(d2);
    });
    await p.waitForTimeout(300);
    await p.screenshot({ path: DIR + '134-node-tag-selector-clamped-200px.png' });
    rec.图 = 'screenshots/134-node-tag-selector-clamped-200px.png';
    await p.evaluate(() => document.querySelectorAll('div[style*="2147483646"]').forEach((e) => e.remove()));
  }
}

// ③ 复原
await p.evaluate(() => document.querySelectorAll('div[style*="2147483646"]').forEach((e) => e.remove()));
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
const bp2 = await p.evaluate(() => {
  for (let y = 30; y < innerHeight - 30; y += 10)
    for (let x = 30; x < innerWidth - 30; x += 10) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  return null;
});
if (bp2) { await p.mouse.click(bp2[0], bp2[1]); await p.waitForTimeout(500); }
await p.keyboard.press('Escape'); await p.waitForTimeout(300);
console.log('\n共享页签复位:', JSON.stringify(await pinViewport(p)));
rec.收尾 = { status: await R.status(), sel: await R.selCount(), credits: await R.credits(),
  残留标签条: await p.evaluate(() => document.querySelectorAll('.max-w-canvas-tag-selector').length) };
console.log('收尾:', JSON.stringify(rec.收尾));
fs.writeFileSync(new URL('./_tmp-b171j.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();
