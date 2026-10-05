// 批次 197 b 轮：解**纵向**落点公式（横向已被 a 轮三档钉死）。
//
// a 轮三档读数（同一个节点「音频 68」，搜索词「音频」，横向缩放都落到 50%）：
//   视口 1280×720 → 落点中心 (474, 258.47)   视口中线 X=640  高/2=360
//   视口 1000×720 → 落点中心 (334, 360)      视口中线 X=500  高/2=360
//   视口 1600×900 → 落点中心 (634, 350)      视口中线 X=800  高/2=450
//
// ⇒ 横向三档**逐字**满足 `落点X = 视口宽/2 − 166`（等价于 `(宽−332)/2`，即右侧常驻 332 宽）
//   1280→474 / 1000→334 / 1600→634，**三档全中**。
// ⇒ 纵向却**不成线性**：同为 720 高，1280 档落 258.47、1000 档落 360，差 101.5。
//   ⇒ 纵向偏移似乎**跟宽度也有关**，或者跟「画布可见区域」有关。
//
// 本轮：固定**宽度不变**、只改高度（隔离两个变量），再固定**高度不变**、只改宽度（做对照）。
// 🔴 每档都先读「画布可见区域」的真实几何（顶栏高、底部坞高、右侧栏宽），
//    用它去解释落点，而不是只报落点数字。
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 搜索词 = '音频';
// A 组：宽固定 1280，只改高（隔离「高」这一个变量）
// B 组：高固定 720，只改宽（隔离「宽」这一个变量）
const 视口集 = [
  { 名: 'A1 1280x600', w: 1280, h: 600 }, { 名: 'A2 1280x720', w: 1280, h: 720 },
  { 名: 'A3 1280x840', w: 1280, h: 840 },
  { 名: 'B1 800x720', w: 800, h: 720 }, { 名: 'B2 1000x720', w: 1000, h: 720 },
  { 名: 'B3 1200x720', w: 1200, h: 720 },
];
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b197b', 假设: '横向 =(宽−332)/2 已三档钉死；本轮隔离「高」与「宽」两个变量解纵向' };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const 共享页 = ctx.pages().find((x) => x.url().includes('ai-canvas'));
out.共享页_前 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);

out.档 = {};
for (const v of 视口集) {
  log(`\n=== ${v.名} ===`);
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: v.w, height: v.h });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    const 实际 = await p.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);

    // 🔴 先读「画布可见区域」的真实几何 —— 公式要落在这些量上
    const 区域 = await p.evaluate(() => {
      const g = (sel) => { const e = document.querySelector(sel); if (!e) return null;
        const r = e.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; };
      const pane = document.querySelector('.react-flow__pane');
      const pr = pane ? pane.getBoundingClientRect() : null;
      // 右侧常驻栏：扫一遍右边缘上所有几何非零、宽度在 200-500 之间的竖长元素
      const 右栏 = [];
      for (const e of document.querySelectorAll('div,aside,section')) {
        const r = e.getBoundingClientRect();
        if (r.width < 180 || r.width > 600) continue;
        if (r.right < innerWidth - 6) continue;          // 必须贴着右边缘
        if (r.height < innerHeight * 0.4) continue;      // 必须是竖长条
        右栏.push({ tag: e.tagName, testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
          x: Math.round(r.x), w: Math.round(r.width), h: Math.round(r.height) });
      }
      return { pane: pr ? { x: Math.round(pr.x), y: Math.round(pr.y), w: Math.round(pr.width), h: Math.round(pr.height) } : null,
        主区: g('[data-testid="canvas-main-region"]'), 顶栏: g('header,[data-testid*="top"],[data-testid*="header"]'),
        底部坞: g('[data-testid="canvas-bottom-dock"]'), 右栏: 右栏.slice(0, 6),
        视口: [innerWidth, innerHeight] };
    });
    log('  区域：', JSON.stringify(区域));

    const 搜索钮 = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
        || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (!搜索钮) { out.档[v.名] = { 中止: '找不到搜索钮' }; continue; }
    await p.mouse.click(搜索钮[0], 搜索钮[1]); await p.waitForTimeout(1400);
    await p.evaluate(() => { const e = document.querySelector('input[aria-label*="搜索"],input[type="text"]');
      if (e) { Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, '');
        e.dispatchEvent(new Event('input', { bubbles: true })); } });
    await p.keyboard.type(搜索词, { delay: 90 });
    await p.waitForTimeout(2100);
    const 行数 = await p.evaluate(() => document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length);
    if (!行数) { out.档[v.名] = { 中止: '没有结果行' }; log('  🔴 没有结果行'); continue; }

    const 行 = await p.evaluate(() => { const e = document.querySelector('[data-testid^="canvas-search-result-node_"]');
      const r = e.getBoundingClientRect(); return { id: e.getAttribute('data-testid'), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
    await p.mouse.click(行.点[0], 行.点[1]);
    await p.waitForTimeout(3000); // 取景动画收敛（批次 191：约 400ms；这里给 3s 保险）
    const 落点 = await p.evaluate((rid) => {
      const id = rid.replace('canvas-search-result-node_', 'node_');
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { 找不到: true };
      const r = n.getBoundingClientRect();
      const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
      return { 节点id: id, aria: n.getAttribute('aria-label'),
        屏上: [r.x, r.y, r.width, r.height].map((q) => Math.round(q * 100) / 100),
        中心: [Math.round((r.x + r.width / 2) * 100) / 100, Math.round((r.y + r.height / 2) * 100) / 100],
        缩放: z ? z.getAttribute('aria-label') : null, 选中: document.querySelectorAll('.react-flow__node.selected').length };
    }, 行.id);
    out.档[v.名] = { 设定: [v.w, v.h], 实际, 区域, 结果行数: 行数, 落点 };
    const [X, Y] = 落点.中心;
    log(`  落点 = (${X}, ${Y}) | 缩放 ${落点.缩放} | 视口中线X=${Math.round(v.w / 2)} | 假设值X=${Math.round((v.w - 332) / 2)} | 差X=${Math.round((X - v.w / 2) * 100) / 100} | 差Y=${Math.round((Y - v.h / 2) * 100) / 100}`);
  } catch (e) { out.档[v.名] = { 出错: e.message }; log('  🔴', e.message); }
  finally { await p.close(); }
}

fs.writeFileSync('/tmp/b197b.json', JSON.stringify(out, null, 1));
out.共享页_后 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);
log('\n共享页 前/后：', JSON.stringify(out.共享页_前), '→', JSON.stringify(out.共享页_后), '| 需复位 =', JSON.stringify(out.共享页_前) !== JSON.stringify(out.共享页_后));
await b.close();
