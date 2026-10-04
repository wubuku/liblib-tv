// 批次 157：把现有页签导航到**本批复制出来的项目副本**，好做善后（删掉它）。
// 复用 156-goto 的思路：openCanvas() 只 pin 视口、不导航，所以要自己导航。
import { chromium } from 'playwright';
const 副本 = 'https://jimeng.jianying.com/ai-tool/ai-canvas/f43b795d-db00-4faa-9d9b-c899db06fb07';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
let p = ctx.pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { p = ctx.pages()[0] || (await ctx.newPage()); await p.goto(副本, { waitUntil: 'domcontentloaded', timeout: 90000 }); }
await p.waitForTimeout(9000);
console.log(JSON.stringify({
  URL: p.url(),
  标题: await p.evaluate(() => document.title),
  项目名: await p.evaluate(() => (document.querySelector('[data-testid="canvas-project-title-trigger"]') || {}).innerText || ''),
  状态行: await p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0] || null),
  节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length),
  积分: await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? (e.getAttribute('aria-label') || e.innerText) : null; }),
}, null, 1));
process.exit(0);
