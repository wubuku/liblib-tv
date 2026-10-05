// 批次 199 a 轮：🔴 找「`1280` 宽是特殊档」的断点在哪。
//
// 批次 198 留下的三条线索，本轮攻第 ② 条（最有价值）：
//   ② 为什么 `1280` 宽那三档的 `ty` 与其他档**差约 100**？
//      （800/1000/1200×720 三者 ty 逐字相同 −44.5555，1600×900 是 −54.5555，
//        而 1280×600/720/840 是 −205.709 / −144.596 / −85.4611）
//   ① `1138.064` 为什么带三位小数（优先级低，下轮再查）
//
// 📌 假设：`1280` 附近存在一个**响应式断点**，跨过它时某个容器（右侧栏？Agent 侧栏？
//    顶栏？）出现或消失，导致画布可用区变了，于是**画布初始平移**变了。
//
// 📌 做法：在**一个新页签**里连续改宽度（省时间），每个宽度读
//    ① `.react-flow__viewport` 的 translate（不看搜索，直接量）
//    ② 画布根容器 / pane 的真实矩形
//    ③ 页面上所有「宽度 ≥ 150 且贴右边缘」的元素（找那个可能突然出现的栏）
//    ④ 顶栏与底部坞的矩形
//    每档都把读数存下来，最后找**不连续的那一档**。
// 收尾：关掉新页签，并用 pinViewport 复位共享页签。
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
// 在 1280 附近密集取点，专门找断点；两端各留两个对照
const 宽度集 = [1000, 1200, 1240, 1272, 1279, 1280, 1281, 1288, 1300, 1366, 1400, 1600];
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b199a', 宽度集, 假设: '1280 附近有响应式断点，跨过时某个容器出现/消失' };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const 共享页 = ctx.pages().find((x) => x.url().includes('ai-canvas'));
out.共享页_前 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);

const p = await ctx.newPage();
await p.setViewportSize({ width: 1280, height: 720 });
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForSelector('.react-flow__node', { timeout: 45000 });
await p.waitForTimeout(5000);
log('页面就绪，开始逐档量宽度');

out.档 = {};
for (const w of 宽度集) {
  await p.setViewportSize({ width: w, height: 720 });
  await p.waitForTimeout(2200);
  const r = await p.evaluate(() => {
    const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
    const g = (sel) => { const e = document.querySelector(sel); if (!e) return null;
      const b = e.getBoundingClientRect(); return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height) }; };
    // 贴右边缘、宽度 ≥150 的竖长元素（可能突然出现/消失的栏）
    const 右件 = [];
    for (const e of document.querySelectorAll('div,aside,section,nav')) {
      const b = e.getBoundingClientRect();
      if (b.width < 150 || b.height < 120) continue;
      if (b.right < innerWidth - 40) continue;
      右件.push({ tag: e.tagName, testid: e.getAttribute('data-testid'), aria: (e.getAttribute('aria-label') || '').slice(0, 20),
        x: Math.round(b.x), w: Math.round(b.width), h: Math.round(b.height) });
    }
    // 贴顶/贴底的横条
    const 顶底件 = [];
    for (const e of document.querySelectorAll('div,header,section')) {
      const b = e.getBoundingClientRect();
      if (b.width < innerWidth * 0.6 || b.height > 120) continue;
      if (b.top > 8 && b.bottom < innerHeight - 8) continue;
      顶底件.push({ tag: e.tagName, testid: e.getAttribute('data-testid'), y: Math.round(b.y), h: Math.round(b.height), w: Math.round(b.width) });
    }
    return { 实际: [innerWidth, innerHeight],
      vp: m ? { tx: Number(m[1]), ty: Number(m[2]), s: Number(m[3]) } : null,
      主区: g('[data-testid="canvas-main-region"]'), pane: g('.react-flow__pane'),
      顶栏: g('[data-testid="canvas-top-bar"],header'), 底部坞: g('[data-testid="canvas-bottom-dock"]'),
      右件: 右件.slice(0, 5), 顶底件: 顶底件.slice(0, 6) };
  });
  out.档[w] = r;
  log(`宽 ${String(w).padStart(4)} | vp=(${r.vp ? r.vp.tx : '?'}, ${r.vp ? r.vp.ty : '?'}) s=${r.vp ? r.vp.s : '?'}`
    + ` | 主区 ${JSON.stringify(r.主区)} | 右件 ${JSON.stringify(r.右件.map((z) => (z.testid || z.aria || z.tag) + ':' + z.x + '+' + z.w))}`);
}

fs.writeFileSync('/tmp/b199a.json', JSON.stringify(out, null, 1));
out.共享页_后 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);
log('\n共享页 前/后：', JSON.stringify(out.共享页_前), '→', JSON.stringify(out.共享页_后));
await p.close();
await b.close();
