// 无头常驻浏览器 v2 —— 用落盘 storageState 启动，并仍然监听 9444，
// 这样 scripts/jimeng-b*.mjs 里那套 connectOverCDP('http://127.0.0.1:9444') 一行都不用改。
//
// 🔴 为什么换掉 v1（/tmp/jimeng-manual-profile 那套）：
//    批次 295 复跑时画布页退化成「登录以打开您的画布」，节点数 0 ——
//    那个 profile 的登录态过期了。📌 只 addCookies 注入**不够**，
//    因为这份 storageState 里除 cookie 外还有 localStorage / IndexedDB。
//    ⇒ 改成 **launch() + newContext({ storageState })**，
//    这条路径已实测可用（账户判据 user_id>0、画布 76 节点、积分 813）。
//
// 📌 凭证处理：只从 ~/.jimeng-automation/state.json 读入内存并交给 Playwright，
//    **不打印、不复制、不写进仓库**。state.json 本身 chmod 600 且在仓库之外。
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const PORT = 9444;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

if (!fs.existsSync(STATE)) throw new Error(`缺少登录态文件：${STATE}`);

const browser = await chromium.launch({
  headless: true,
  args: [
    `--remote-debugging-port=${PORT}`,
    '--remote-debugging-address=127.0.0.1',
    '--disable-background-networking',
    '--disable-features=Translate,MediaRouter',
    '--no-first-run',
    '--no-default-browser-check',
  ],
});
const ctx = await browser.newContext({ storageState: STATE, viewport: { width: 1280, height: 720 } });

const page = await ctx.newPage();
await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
await page.waitForSelector('.react-flow__node', { timeout: 90000 });
await page.waitForTimeout(4000);

const 状态 = await page.evaluate(() => ({
  视口: [innerWidth, innerHeight],
  节点数: document.querySelectorAll('.react-flow__node').length,
  状态行: (document.body.innerText.match(/[\d]+ nodes?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
  积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { textContent: null }).textContent,
}));
console.log('✅ 无头浏览器 v2 已启动并监听', PORT);
console.log('   登录态来源 = ~/.jimeng-automation/state.json（只读入内存，不打印内容）');
console.log('   画布读数 =', JSON.stringify(状态));

const 保活 = setInterval(() => {}, 1 << 30);
const 收尾 = async () => { clearInterval(保活); try { await browser.close(); } catch { /* 忽略 */ } process.exit(0); };
process.on('SIGINT', 收尾);
process.on('SIGTERM', 收尾);
