// 批次 171 e 轮：修 d 轮的两个工具缺陷，重打边界。
//
// 🔴 缺陷 1（读数）：d 轮在 1280×300 读到 `116×23`，而 computed `width` 明明是 `224px`
//    —— 那是**入场动画的中间帧**（class 里有 `origin-center`，配的是
//    `octo-context-menu-transform-in` 一类的 scale 动画），`getBoundingClientRect` 取的是**变换后**的矩形。
//    ⇒ **量布局尺寸要用 `offsetWidth/offsetHeight`**，或者**等动画结束**（连续两次读数一致才算）。
// 🔴 缺陷 2（打不开）：窄视口下 `打开()` 找的是「第一个节点的标题」，
//    那个节点可能已被挤出视口 / 被别的浮层盖住 ⇒ 10 档里 7 档「没打开」。
//    ⇒ 改为**先找一个 elementFromPoint 确实命中标题的可见节点**，点完**验证选中数 > 0** 再找 Add tags。
//
// 预测（不变）：宽 = min(224, 100vw−32)，门槛 256；高恒 44；
//   夹到比内容还窄时 `overflow-x-auto` 出现横向滚动、末尾颜色被裁。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p: shared } = await openCanvas();
const p = shared;
const R = readers(p);
const rec = { 批次: '171e' };

const pin = async (page, w, h) => {
  await page.context().newCDPSession(page).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await page.waitForTimeout(900);
  const vp = await page.evaluate(() => [innerWidth, innerHeight]);
  if (vp[0] !== w || vp[1] !== h) throw new Error(`钉视口失败 ${JSON.stringify(vp)}`);
};

/** 找一个「点标题真能选中」的节点：先验 elementFromPoint，再点，再验选中数。 */
const 选出一个节点 = async (page) => {
  for (let round = 0; round < 3; round++) {
    const cands = await page.evaluate(() => {
      const out = [];
      for (const t of document.querySelectorAll('.react-flow__node [data-testid="flow-node-title"]')) {
        const r = t.getBoundingClientRect();
        const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
        if (cx < 4 || cy < 4 || cx > innerWidth - 4 || cy > innerHeight - 4) continue;
        const hit = document.elementFromPoint(cx, cy);
        if (!hit || !hit.closest('.react-flow__node')) continue;
        if (hit.closest('[data-testid="flow-node-target-handle"], [data-testid="flow-node-source-handle"]')) continue;
        out.push({ pt: [Math.round(cx), Math.round(cy)], 文字: (t.innerText || '').trim().slice(0, 12),
          命中: hit.tagName + '[' + (hit.getAttribute('data-testid') || '') + ']' });
      }
      return out;
    });
    for (const c of cands) {
      await page.mouse.click(c.pt[0], c.pt[1]);
      await page.waitForTimeout(700);
      const sel = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
      if (sel > 0) return { ...c, sel };
    }
    // 一轮都不中：先取消选中再试
    await page.keyboard.press('Escape'); await page.waitForTimeout(300);
  }
  return null;
};

const 打开标签条 = async (page) => {
  if (await page.evaluate(() => !!document.querySelector('.max-w-canvas-tag-selector'))) return { ok: true, 复用: true };
  const n = await 选出一个节点(page);
  if (!n) return { ok: false, 原因: '找不到能选中的可见节点' };
  const tag = await page.evaluate(() => {
    const e = document.querySelector('[data-testid="flow-node-selected-tag"]');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) return null;
    const hit = document.elementFromPoint(cx, cy);
    if (!hit || !hit.closest('[data-testid="flow-node-selected-tag"]')) return null;
    return [Math.round(cx), Math.round(cy)];
  });
  if (!tag) return { ok: false, 原因: 'Add tags 按钮不可点', 节点: n };
  await page.mouse.click(tag[0], tag[1]);
  // 等入场动画结束：连续两次 offsetWidth 相同
  let last = -1, stable = 0;
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(250);
    const w = await page.evaluate(() => {
      const e = document.querySelector('.max-w-canvas-tag-selector');
      return e ? e.offsetWidth : -1;
    });
    if (w > 0 && w === last) { stable++; if (stable >= 2) break; } else stable = 0;
    last = w;
  }
  return { ok: await page.evaluate(() => !!document.querySelector('.max-w-canvas-tag-selector')), 节点: n, 点了: tag };
};

const 读 = (page) => page.evaluate(() => {
  const e = document.querySelector('.max-w-canvas-tag-selector');
  if (!e) return null;
  const cs = getComputedStyle(e);
  const r = e.getBoundingClientRect();
  const btns = Array.from(e.querySelectorAll('button')).map((b) => {
    const q = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'),
      盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      完全在可视区内: q.left >= r.left - 0.5 && q.right <= r.right + 0.5 };
  });
  return {
    布局宽: e.offsetWidth, 布局高: e.offsetHeight,          // ← 不受动画 transform 影响
    变换后: [Math.round(r.width), Math.round(r.height)],
    computed: { w: cs.width, h: cs.height, maxW: cs.maxWidth, maxH: cs.maxHeight },
    overflowX: cs.overflowX, scrollW: e.scrollWidth, clientW: e.clientWidth,
    可横向滚动: e.scrollWidth > e.clientWidth + 0.5,
    内边距: cs.padding, 间隙: cs.gap,
    按钮数: btns.length, 按钮: btns, 被裁: btns.filter((x) => !x.完全在可视区内).map((x) => x.aria),
  };
});

const tab = await b.contexts()[0].newPage();
await tab.goto(shared.url(), { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);

rec.档位 = [];
const 档 = [[1280, 720], [400, 720], [300, 720], [256, 720], [250, 720], [220, 720], [200, 720], [180, 720], [160, 720], [1280, 300], [1280, 200]];
for (const [w, h] of 档) {
  await pin(tab, w, h);
  const op = await 打开标签条(tab);
  if (!op.ok) { rec.档位.push({ 视口: [w, h], 打开: false, 原因: op.原因 }); console.log(`  ${w}×${h}: ❌ ${op.原因}`); continue; }
  const d = await 读(tab);
  const 预测宽 = Math.min(224, Math.max(0, w - 32));
  rec.档位.push({ 视口: [w, h], 打开: true, 布局: [d.布局宽, d.布局高], 变换后: d.变换后,
    computed: d.computed, 滚动: d.可横向滚动, scrollW: d.scrollW, clientW: d.clientW,
    按钮数: d.按钮数, 被裁: d.被裁, 预测宽 });
  console.log(`  ${w}×${h}: 布局 ${d.布局宽}×${d.布局高}（预测宽 ${预测宽} ${d.布局宽 === 预测宽 ? '✅' : '❌'}）` +
    ` 变换后 ${d.变换后.join('×')} scrollW=${d.scrollW}/client=${d.clientW} 滚动=${d.可横向滚动} 被裁=${JSON.stringify(d.被裁)}`);
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
fs.writeFileSync(new URL('./_tmp-b171e.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();
