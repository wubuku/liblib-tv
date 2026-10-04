// 批次 157：把共享浏览器的页签**归位到共享画布**（64b58cd5…）并读终态。
// 🔴 背景：157-shots 收尾时页签停在 `a8261de6…?from_page=create`（测试项目3）。
//    本批**只点过** `测试项目5的更多操作`（f43b795d），没点过任何项目名行；
//    而 `?from_page=create` 正是「从项目列表点进来」才有的 URL 形态
//    ⇒ 与本会话反复出现的（浏览器被别人关掉重启、冒出新节点、积分被扣）
//       是同一件事：**共享浏览器正被并行 session 使用**。这里只负责归位，不追责。
import { chromium } from 'playwright';
const 目标 = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = ctx.pages().find((x) => x.url().includes('ai-canvas')) || (await ctx.newPage());
const 前URL = p.url();
if (p.url().split('?')[0] !== 目标) { await p.goto(目标, { waitUntil: 'domcontentloaded', timeout: 90000 }); }
await p.waitForTimeout(9000);
const 读 = async () => ({
  URL: p.url(),
  项目名: await p.evaluate(() => (document.querySelector('[data-testid="canvas-project-title-trigger"]') || {}).innerText || ''),
  状态行: await p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0] || null),
  节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  选中: await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length),
  缩放: await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; }),
  积分: await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; }),
  小地图: await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); return e ? e.getAttribute('aria-pressed') : null; }),
});
console.log('归位前', 前URL.slice(-46));
console.log('归位后', JSON.stringify(await 读(), null, 1));
process.exit(0);
