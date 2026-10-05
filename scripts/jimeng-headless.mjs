// 无头常驻浏览器（批次 201 起取代之前的有头实例）
//
// 🔴 为什么换：之前那个实例是 `Google Chrome for Testing` + `--user-data-dir` 但**没有
//    `--headless`** ⇒ 它是**有头**窗口；而批次 197~200 的脚本用 `ctx.newPage()` 逐档开新页，
//    于是在用户屏幕上**不停蹦标签页**。用户明确要求「此后请使用无头浏览器」。
//
// 📌 做法：**同一个 profile 目录**（`/tmp/jimeng-manual-profile`）＋ `headless: true`
//    ＋ 固定 `--remote-debugging-port=9444`，这样 `jimeng-b135-lib.mjs` 里那套
//    `connectOverCDP('http://127.0.0.1:9444')` 的脚本**一行都不用改**。
//
// 📌 登录态：profile 里的 Cookies 会带上，所以**不需要重新登录**。
//    （不读取任何凭证内容，只复用浏览器自己持久化的状态。）
//
// 用法：node scripts/jimeng-headless.mjs        —— 前台常驻（Ctrl-C 退出）
//      node scripts/jimeng-headless.mjs &      —— 后台常驻
import { chromium } from 'playwright';

const PROFILE = '/tmp/jimeng-manual-profile';
const PORT = 9444;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

const ctx = await chromium.launchPersistentContext(PROFILE, {
  headless: true,
  args: [
    `--remote-debugging-port=${PORT}`,
    '--remote-debugging-address=127.0.0.1',
    '--disable-background-networking',
    '--disable-features=Translate,MediaRouter',
    '--no-first-run',
    '--no-default-browser-check',
  ],
  viewport: { width: 1280, height: 720 },
});

// 打开画布页并等它真的加载出节点
let page = ctx.pages().find((p) => p.url().includes('ai-canvas'));
if (!page) {
  page = await ctx.newPage();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
}
await page.waitForSelector('.react-flow__node', { timeout: 45000 }).catch(() => {});
await page.waitForTimeout(3000);

const 状态 = await page.evaluate(() => {
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return {
    视口: [innerWidth, innerHeight, devicePixelRatio],
    缩放: z ? z.getAttribute('aria-label') : null,
    状态行: (document.body.innerText.match(/[\d]+ nodes?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
    节点数: document.querySelectorAll('.react-flow__node').length,
    积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    标题: document.title.slice(0, 40),
  };
});

console.log('✅ 无头浏览器已启动并监听 9444');
console.log('   profile =', PROFILE, '| headless = true');
console.log('   画布读数 =', JSON.stringify(状态, null, 1));
console.log('   （不读取任何凭证内容，只复用浏览器自己持久化的登录态）');

// 常驻：context 保持存活，进程不退出
const 保活 = setInterval(() => {}, 1 << 30);
const 收尾 = async () => { clearInterval(保活); try { await ctx.close(); } catch {} process.exit(0); };
process.on('SIGINT', 收尾);
process.on('SIGTERM', 收尾);
