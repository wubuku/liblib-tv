// 通过 CDP 读取当前即梦页面的登录/画布状态（只读，不点击任何扣费按钮）。
// 用法：node scripts/jimeng-probe.mjs
import { chromium } from 'playwright';

const browser = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = browser.contexts()[0];
const pages = ctx.pages();
const page = pages.find((p) => p.url().includes('jimeng.jianying.com')) || pages[0];

console.log('URL  ', page.url());
console.log('TITLE', await page.title());

// 登录态线索：右上角用户菜单 / 登录按钮
const probe = await page.evaluate(() => {
  const txt = (el) => (el?.textContent || '').trim();
  const all = Array.from(document.querySelectorAll('button,a,[role="button"]'));
  const labels = all.map(txt).filter((t) => t && t.length < 24);
  return {
    hasLoginText: /登录|立即登录|免费登录/.test(document.body.innerText),
    hasCanvasText: /ai-canvas|画布/.test(document.body.innerText),
    buttons: Array.from(new Set(labels)).slice(0, 40),
  };
});

console.log('loginPromptVisible:', probe.hasLoginText);
console.log('mentionsCanvas     :', probe.hasCanvasText);
console.log('buttons            :', probe.buttons.join(' | '));

await browser.close();
