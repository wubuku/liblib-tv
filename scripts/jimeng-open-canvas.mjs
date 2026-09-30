// 把已打开的独立浏览器导航到手册使用的测试画布。
// 未登录时源站会跳登录页；用户完成登录后即落在画布内。
// 用法：node scripts/jimeng-open-canvas.mjs [url]
import { chromium } from 'playwright';

const url =
  process.argv[2] ||
  'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

const browser = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = browser.contexts()[0];
const page = ctx.pages()[0];

await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch((e) => {
  console.error('goto failed:', e.message);
});
await page.waitForTimeout(3000);

console.log('URL  ', page.url());
console.log('TITLE', await page.title());

const state = await page.evaluate(() => {
  const t = document.body.innerText || '';
  return {
    needsLogin: /扫码登录|验证码登录|登录\/注册|立即登录/.test(t),
    onCanvas: /nodes,|edges,|已保存|画布/.test(t),
    head: t.replace(/\s+/g, ' ').slice(0, 220),
  };
});
console.log('needsLogin:', state.needsLogin);
console.log('onCanvas  :', state.onCanvas);
console.log('text      :', state.head);

await browser.close();
