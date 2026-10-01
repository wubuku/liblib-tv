// 批次 72 · D：手柄热区「因类型而异」还是「入场动画没结束」？
// 对照组 = **既有节点**（同一时刻量），实验组 = **刚建的新节点**，重复量三次时间点。
import { chromium } from 'playwright';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const read = (id) => p.evaluate((v) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
  const h = n.querySelector('.react-flow__handle-right'); const r = h.getBoundingClientRect();
  const nr = n.getBoundingClientRect();
  return { h: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
    node: [Math.round(nr.width * 10) / 10, Math.round(nr.height * 10) / 10],
    ratio: Math.round((r.width / nr.width) * 1000) / 1000,
    cs: getComputedStyle(n).getPropertyValue('--octo-canvas-node-chrome-counter-scale') || null,
    zoomVar: getComputedStyle(n).getPropertyValue('--octo-canvas-node-zoom') || null,
    clsScale: String(n.className).match(/scale-\S+/g)?.join(',') || null };
}, id);
const ctrlId = (await ids())[0];
const pre = await ids();
const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
  .find((x) => /^视频$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
  const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
await p.mouse.click(rail.x, rail.y);
const t0 = Date.now();
const mine = (await ids()).filter((x) => !pre.includes(x))[0];
for (const wait of [2400, 3000, 4000]) {
  await p.waitForTimeout(wait);
  console.log(`t=+${Date.now() - t0}ms  新节点 ${JSON.stringify(await read(mine))}\n            对照(既有) ${JSON.stringify(await read(ctrlId))}`);
}
// 删掉
const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) }; }, mine);
await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(900);
await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
  const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
await p.waitForTimeout(1400);
console.log('清理', mine, (await ids()).includes(mine) ? '🔴 仍在' : '✅');
await b.close();
