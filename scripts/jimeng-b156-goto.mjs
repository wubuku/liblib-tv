// 批次 156：把独立浏览器导航到共享画布（第 9 道门「画布焦点守卫」需要画布页在位）。
//
// 🔴 为什么会写这个：`jimeng-b135-lib.mjs` 的 `openCanvas()` **只 pin 视口、不导航**
//    （注释里写得很清楚：「接上已有的独立 Chrome，只 pin 视口，不导航」）。
//    本批的脚本每轮末尾都 `b.close()`，最后一次把 9444 整个关掉了；
//    重启后浏览器停在 `https://jimeng.jianying.com/ai-tool/home/`，
//    于是 `openCanvas()` 抛「找不到画布页」⇒ **第 9 道门红**。
//    📌 现象与真因隔了三层：一道门红 → 浏览器没了 → 浏览器在新 profile 上 → 页签不是画布。
//       **顺着「最后一个报错的函数」往上翻，比从报错本身猜要快。**
//
// ⚠️ 本脚本**刻意不 close()**：连的是长期开着的用户浏览器，探针不该把它关掉。
import { chromium } from 'playwright';

const PORT = 9444;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

const b = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`);
const ctx = b.contexts()[0];
let p = ctx.pages().find((x) => x.url().includes('ai-canvas'));
if (!p) {
  p = ctx.pages()[0] || (await ctx.newPage());
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
}
await p.waitForTimeout(9000);

const 读 = async (page) => ({
  URL: page.url(),
  状态行: await page.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0] || null),
  节点数: await page.evaluate(() => document.querySelectorAll('.react-flow__node').length),
  选中: await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length),
  边数: await page.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  zoom: await page.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; }),
  积分: await page.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? (e.innerText || '').replace(/\s+/g, ' ').trim() : null; }),
  transform: await page.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; }),
});

console.log(JSON.stringify(await 读(p), null, 1));
process.exit(0);
