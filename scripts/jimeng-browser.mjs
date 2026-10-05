// 独立的 Chromium，供即梦画布手册取证使用。
// 与其他开发者已占用的 9222 端口完全隔离：独立 user-data-dir + 独立调试端口，
// 不 attach、不复用任何既有浏览器会话，也不读取他人 cookie。
//
// 🔴🔴 **批次 201 改为无头（2026-10-05，用户明确要求）**：
//   原来这里是 `headless: false`，注释还写着「保持浏览器打开，等待用户手动登录」。
//   ⇒ 后果是：① 用户屏幕上长期挂着一个真实浏览器窗口；
//            ② 批次 197~200 的探针用 `ctx.newPage()` 逐档开新页，**每档都在那个窗口里蹦标签**；
//            ③ 更糟的是 `jimeng-browser-keepalive.mjs` 会在 9444 掉线时**自动重拉本脚本**
//               ⇒ 我手动关掉有头窗口，守护 6 秒内又给它拉起一个新的。
//   ⇒ 现在统一 `headless: true`。登录态由 profile 目录里的 Cookies 持久化，
//      **不需要「等待用户手动登录」这一步**，实测重启后标题仍是「测试项目 - 即梦AI」。
//
// 用法：node scripts/jimeng-browser.mjs [url]
import { chromium } from 'playwright';

const PORT = 9444;               // 避开 9222（已被其他 Chrome 占用）
const PROFILE = '/tmp/jimeng-manual-profile';
const url = process.argv[2] || 'https://jimeng.jianying.com/';

const ctx = await chromium.launchPersistentContext(PROFILE, {
  headless: true,                 // 🔴 批次 201：必须无头，否则会在用户屏幕上弹窗口
  viewport: { width: 1280, height: 720 },
  locale: 'zh-CN',
  timezoneId: 'Asia/Shanghai',
  args: [`--remote-debugging-port=${PORT}`],
});

const page = ctx.pages()[0] || (await ctx.newPage());
await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch((e) => {
  console.error('goto failed:', e.message);
});

console.log('READY — CDP port', PORT, '(headless)');
console.log('URL', page.url());
console.log('TITLE', await page.title());

// 保持浏览器存活，等探针通过 `connectOverCDP(9444)` 接管。
await new Promise(() => {});
