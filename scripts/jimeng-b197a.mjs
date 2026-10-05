// 批次 197 a 轮：🔴 销一条明确标着「未测」的线索 —— 换视口后，搜索定位的落点 `474` 会不会跟着变？
//
// 手册 navigate-canvas.md:389 逐字写着：
//   「**上面这张表是实测值，不是公式**。视口尺寸本手册固定用 `1280×720`，
//     换视口后 `474` 会不会跟着变，**未测**。」
// 批次 192 钉出的是：26/26 条落点读数的**横向中心只有 `474.0` 这一个取值**
//   （而 1280 宽视口的中线是 `640`，横向上差了 166px）⇒ 它不是「中线」，是某个常数。
//
// 📌 方法（同 assets-and-upload.md:441-442 记的）：**开一个新页签**去换分辨率，
//    代价只是收尾要把共享窗口复位 —— 本轮用完立刻关掉新页签，共享页签**全程不动**。
//
// 🔴 假设：「474」是**画布视口的固定常数**（例如某个面板宽度减去一半），
//    而不是「视口中心」。若换视口后它仍逐字是 474 ⇒ 假设成立；
//    若它跟着视口宽变 ⇒ 474 其实是某个比值，下一轮去找公式。
import fs from 'node:fs';
import { chromium } from 'playwright';
import { pinViewport } from './jimeng-safe-keys.mjs';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 共享 = 'http://127.0.0.1:9444';
// 三档视口：基准 1280×720，另两档刻意不等比，看它跟「宽」走还是跟别的走
const 视口集 = [
  { 名: '基准 1280x720', w: 1280, h: 720, dsf: 2 },
  { 名: '窄 1000x720', w: 1000, h: 720, dsf: 2 },
  { 名: '宽 1600x900', w: 1600, h: 900, dsf: 2 },
];
const 搜索词 = '音频';
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b197a', 视口集: 视口集.map((v) => v.名), 搜索词, 假设: '474 是画布视口的固定常数' };

const b = await chromium.connectOverCDP(共享);
const ctx = b.contexts()[0];
const 共享页 = ctx.pages().find((x) => x.url().includes('ai-canvas'));
out.共享页签存在 = !!共享页;

// 记录共享页签的原始状态，收尾要确认它没被动过
const 共享前 = await 共享页.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return { 缩放: e ? e.getAttribute('aria-label') : null,
    状态行: (document.body.innerText.match(/[\d]+ nodes?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
    节点数: document.querySelectorAll('.react-flow__node').length,
    视口: [innerWidth, innerHeight] };
});
out.共享页_前 = 共享前;
log('共享页签（全程不动）：', JSON.stringify(共享前));

for (const v of 视口集) {
  log(`\n=== ${v.名} ===`);
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: v.w, height: v.h });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    // 不用 pinViewport：那会写死 1280×720。本轮要的就是真实设定尺寸
    const 实际 = await p.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);
    log('  实际视口 =', JSON.stringify(实际));
    out[v.名] = { 设定: [v.w, v.h], 实际: 实际 };

    // 读几个关键几何：画布视口容器、顶栏、结果行面板的预期位置
    out[v.名].容器 = await p.evaluate(() => {
      const g = (sel) => { const e = document.querySelector(sel); if (!e) return null;
        const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map((z) => Math.round(z * 100) / 100); };
      return { 画布主区: g('[data-testid="canvas-main-region"]'),
        缩放钮: g('[data-testid="canvas-zoom-percent"]'),
        底部坞: g('[data-testid="canvas-bottom-dock"]'),
        视口中线X: Math.round(innerWidth / 2 * 100) / 100 };
    });
    log('  容器：', JSON.stringify(out[v.名].容器));

    // 打开搜索 → 输词 → 点第一条结果行 → 读落点
    const 搜索钮 = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
        || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (!搜索钮) { log('  🔴 找不到搜索钮'); out[v.名].中止 = '找不到搜索钮'; continue; }
    await p.mouse.click(搜索钮[0], 搜索钮[1]); await p.waitForTimeout(1400);

    const 输入框 = await p.evaluate(() => {
      const e = document.querySelector('input[aria-label="搜索"],input[aria-label*="搜索"],input[type="text"]');
      if (!e) return null;
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, '');
      e.dispatchEvent(new Event('input', { bubbles: true }));
      return { 存在: true, 屏上: (() => { const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round); })() };
    });
    await p.keyboard.type(搜索词, { delay: 90 });
    await p.waitForTimeout(2000);
    out[v.名].输入框 = 输入框;
    out[v.名].结果行数 = await p.evaluate(() => document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length);
    log('  结果行数 =', out[v.名].结果行数);

    if (!out[v.名].结果行数) { log('  🔴 没有结果行'); continue; }

    // 先记录「点之前」缩放，再点第一行，读落点
    out[v.名].点之前 = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
      return { 缩放aria: e ? e.getAttribute('aria-label') : null };
    });
    const 行点 = await p.evaluate(() => {
      const e = document.querySelector('[data-testid^="canvas-search-result-node_"]');
      const r = e.getBoundingClientRect();
      return { id: e.getAttribute('data-testid'), 屏上: [r.x, r.y, r.width, r.height].map(Math.round),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    });
    out[v.名].第一行 = 行点;
    await p.mouse.click(行点.点[0], 行点.点[1]);
    await p.waitForTimeout(2600); // 等取景动画收敛（批次 191 量到约 400ms，这里给足）
    out[v.名].点之后 = await p.evaluate((rid) => {
      const id = rid.replace('canvas-search-result-node_', 'node_');
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return { 找不到节点: true };
      const r = n.getBoundingClientRect();
      const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
      return { 节点id: id, aria: n.getAttribute('aria-label'),
        落点屏上: [r.x, r.y, r.width, r.height].map((z2) => Math.round(z2 * 100) / 100),
        落点中心: [Math.round((r.x + r.width / 2) * 100) / 100, Math.round((r.y + r.height / 2) * 100) / 100],
        缩放aria: z ? z.getAttribute('aria-label') : null,
        选中数: document.querySelectorAll('.react-flow__node.selected').length,
        状态行: (document.body.innerText.match(/[\d]+ nodes?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0] };
    }, 行点.id);
    log('  落点 =', JSON.stringify(out[v.名].点之后));
  } catch (e) {
    out[v.名].出错 = e.message;
    log('  🔴 出错：', e.message);
  } finally {
    await p.close(); // 新页签用完即关，共享页签全程不受影响
  }
}

// 收尾：确认共享页签**没被动过**
out.共享页_后 = await 共享页.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return { 缩放: e ? e.getAttribute('aria-label') : null,
    状态行: (document.body.innerText.match(/[\d]+ nodes?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
    节点数: document.querySelectorAll('.react-flow__node').length,
    视口: [innerWidth, innerHeight] };
});
out.共享页未被动 = JSON.stringify(out.共享页_前) === JSON.stringify(out.共享页_后);
log('\n共享页签 后：', JSON.stringify(out.共享页_后), '| 未被动 =', out.共享页未被动);

fs.writeFileSync('/tmp/b197a.json', JSON.stringify(out, null, 1));
await b.close();
