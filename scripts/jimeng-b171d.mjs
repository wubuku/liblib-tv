// 批次 171 d 轮：标签选择器的**夹取边界**与「窄了会怎样」。
//
// 批次 171 c 轮落定的机制（逐字）：
//   `DIV[data-testid=canvas-node-tag-selector][role=toolbar][aria-label="Canvas tags"]`
//   class 逐字含 `fixed flex h-canvas-tag-selector-height w-canvas-tag-selector-width
//                  max-w-canvas-tag-selector … overflow-x-auto overflow-y-hidden … origin-center`
//   style 逐字 `left: …; top: …; visibility: visible; z-index: 200030;`
//   ⇒ **定尺类与夹取类在同一个元素上，不存在「包裹层 vs 面板本体」之分**（推翻本批 a 轮的设问）
//   1280×720 实测 `224×44`，computed `w=224px` / `max-w=1248px`（＝1280−32）
//
// 预测（先预测再打）：
//   P1 宽 = min(224, 100vw−32)，门槛 **256**：256→224 / 250→218 / 200→168
//   P2 高恒 **44**（`h-canvas-tag-selector-height` 里没有视口项）
//   P3 class 里有 **`overflow-x-auto`** ⇒ 夹到比内容还窄时会出现**横向滚动**，
//      最后几个颜色点不到 —— 内容宽度 = 7×28 + 6×间隙 + 2×内边距
//
// 🔴 纪律（165-a）：多视口测量在**新开页签**里做，收尾 `pinViewport` 复位共享页签。
// ⛔ 不点任何颜色按钮（会改节点标签）。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const DIR = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url).pathname;
const { b, p: shared } = await openCanvas();
const p = shared;
const R = readers(p);
const rec = { 批次: '171d' };

const pin = async (page, w, h) => {
  await page.context().newCDPSession(page).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await page.waitForTimeout(600);
  const vp = await page.evaluate(() => [innerWidth, innerHeight]);
  if (vp[0] !== w || vp[1] !== h) throw new Error(`钉视口失败 ${JSON.stringify(vp)}`);
};

const 读 = (page) => page.evaluate(() => {
  const e = document.querySelector('.max-w-canvas-tag-selector');
  if (!e) return null;
  const cs = getComputedStyle(e);
  const r = e.getBoundingClientRect();
  const btns = Array.from(e.querySelectorAll('button')).map((b) => {
    const q = b.getBoundingClientRect();
    const inView = q.left >= r.left - 0.5 && q.right <= r.right + 0.5;
    return { aria: b.getAttribute('aria-label'), 盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      完全在可视区内: inView };
  });
  return {
    盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    w: cs.width, h: cs.height, maxW: cs.maxWidth, maxH: cs.maxHeight,
    overflowX: cs.overflowX, scrollW: e.scrollWidth, clientW: e.clientWidth,
    可横向滚动: e.scrollWidth > e.clientWidth + 0.5,
    内边距: cs.padding, 间隙: cs.gap,
    按钮数: btns.length, 按钮: btns,
    被裁掉: btns.filter((x) => !x.完全在可视区内).map((x) => x.aria),
  };
});

// 打开标签选择器（在共享页签上复现已成功：选节点 → 点 Add tags）
const 打开 = async (page) => {
  await page.keyboard.press('Escape'); await page.waitForTimeout(250);
  const has = await page.evaluate(() => !!document.querySelector('.max-w-canvas-tag-selector'));
  if (has) return true;
  const t = await page.evaluate(() => {
    const n = document.querySelector('.react-flow__node [data-testid="flow-node-title"]');
    n.closest('.react-flow__node').scrollIntoView({ block: 'center', inline: 'center' });
    return null;
  });
  await page.waitForTimeout(700);
  const title = await page.evaluate(() => {
    const n = document.querySelector('.react-flow__node [data-testid="flow-node-title"]');
    const r = n.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  await page.mouse.click(title[0], title[1]);
  await page.waitForTimeout(1000);
  const tag = await page.evaluate(() => {
    const e = document.querySelector('[data-testid="flow-node-selected-tag"]');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (!tag) return false;
  await page.mouse.click(tag[0], tag[1]);
  await page.waitForTimeout(1500);
  return await page.evaluate(() => !!document.querySelector('.max-w-canvas-tag-selector'));
};

// —— 共享页签：先取基线 + 拍图 ——
console.log('共享页签打开标签选择器 =', await 打开(p));
rec.基线1280 = await 读(p);
console.log('1280×720:', JSON.stringify({ 盒: rec.基线1280.盒, w: rec.基线1280.w, maxW: rec.基线1280.maxW,
  按钮数: rec.基线1280.按钮数, 内边距: rec.基线1280.内边距, 间隙: rec.基线1280.间隙,
  scrollW: rec.基线1280.scrollW, clientW: rec.基线1280.clientW, 被裁: rec.基线1280.被裁掉 }));
await p.evaluate(() => {
  const e = document.querySelector('.max-w-canvas-tag-selector');
  const r = e.getBoundingClientRect();
  const d = document.createElement('div');
  d.style.cssText = `position:fixed;left:${r.x - 4}px;top:${r.y - 4}px;width:${r.width + 8}px;height:${r.height + 8}px;` +
    `border:3px solid #ff8c00;border-radius:10px;pointer-events:none;z-index:2147483646`;
  document.body.appendChild(d);
});
await p.waitForTimeout(300);
await p.screenshot({ path: DIR + '133-node-tag-selector-224x44.png' });
rec.图 = 'screenshots/133-node-tag-selector-224x44.png';
await p.evaluate(() => document.querySelectorAll('div[style*="2147483646"]').forEach((e) => e.remove()));
await p.keyboard.press('Escape'); await p.waitForTimeout(400);

// —— 新页签：多视口边界 ——
const tab = await b.contexts()[0].newPage();
await tab.goto(shared.url(), { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);

rec.档位 = [];
for (const [w, h] of [[1280, 720], [300, 720], [256, 720], [250, 720], [220, 720], [200, 720], [180, 720], [1280, 300]]) {
  await pin(tab, w, h);
  const ok = await 打开(tab);
  const d = ok ? await 读(tab) : null;
  const 预测宽 = Math.min(224, Math.max(0, w - 32));
  rec.档位.push({ 视口: [w, h], 打开: ok, 盒: d && d.盒, 可横向滚动: d && d.可横向滚动,
    scrollW: d && d.scrollW, clientW: d && d.clientW, 被裁: d && d.被裁掉, 预测宽 });
  console.log(`  ${w}×${h}: ${ok ? `宽=${d.盒[2]} 预测=${预测宽} ${d.盒[2] === 预测宽 ? '✅' : '❌'} 高=${d.盒[3]} ` +
    `scrollW=${d.scrollW}/client=${d.clientW} 滚动=${d.可横向滚动} 被裁=${JSON.stringify(d.被裁掉)}` : '❌ 没打开'}`);
  if (w === 200 && ok && d.可横向滚动) {
    await tab.evaluate(() => {
      const e = document.querySelector('.max-w-canvas-tag-selector');
      const r = e.getBoundingClientRect();
      const d2 = document.createElement('div');
      d2.style.cssText = `position:fixed;left:${r.x - 4}px;top:${r.y - 4}px;width:${r.width + 8}px;height:${r.height + 8}px;` +
        `border:3px solid #ff8c00;border-radius:10px;pointer-events:none;z-index:2147483646`;
      document.body.appendChild(d2);
    });
    await tab.waitForTimeout(300);
    await tab.screenshot({ path: DIR + '134-node-tag-selector-clamped-200px.png' });
    rec.图2 = 'screenshots/134-node-tag-selector-clamped-200px.png';
    await tab.evaluate(() => document.querySelectorAll('div[style*="2147483646"]').forEach((e) => e.remove()));
  }
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
}
await tab.close();

console.log('\n共享页签复位:', JSON.stringify(await pinViewport(shared)));
rec.收尾 = { status: await R.status(), sel: await R.selCount(), credits: await R.credits() };
console.log('收尾:', JSON.stringify(rec.收尾));
fs.writeFileSync(new URL('./_tmp-b171d.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();
