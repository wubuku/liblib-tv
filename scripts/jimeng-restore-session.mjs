/**
 * 把落盘的 storageState 注入常驻无头浏览器（只注入 cookie，不打印任何凭证值）。
 * 起因：/tmp/jimeng-manual-profile 的登录态过期，画布页退化成
 * 「登录以打开您的画布」（节点数 0）。~/.jimeng-automation/state.json 经
 * /passport/account/info 判据验活仍然有效（user_id > 0）。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const st = JSON.parse(fs.readFileSync(STATE, 'utf8'));

// 只注入 jimeng 主域的 cookie；**不打印 value**
const 域 = st.cookies.filter((c) => (c.domain || '').includes('jimeng.jianying.com'));
console.log('待注入 cookie 条数 =', 域.length, '（只报条数，不报内容）');

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
await ctx.addCookies(域);

const p = await ctx.newPage();
await p.setViewportSize({ width: 1280, height: 720 });
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForSelector('.react-flow__node', { timeout: 60000 });
await p.waitForTimeout(6000);
const 态 = await p.evaluate(() => ({
  节点数: document.querySelectorAll('.react-flow__node').length,
  状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
  积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || {}).textContent || null,
  用户菜单: (document.querySelector('[data-testid="canvas-user-menu-trigger"]') || {}).getAttribute?.('aria-label') || null,
}));
console.log('恢复后读数 =', JSON.stringify(态));
await p.close();
process.exit(0);
