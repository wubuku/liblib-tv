// 独立的有头 Chromium，供即梦画布手册取证使用。
// 与其他开发者已占用的 9222 端口完全隔离：独立 user-data-dir + 独立调试端口，
// 不 attach、不复用任何既有浏览器会话，也不读取他人 cookie。
// 用法：node scripts/jimeng-browser.mjs [url]
import { chromium } from 'playwright';

const PORT = 9444;               // 避开 9222（已被其他 Chrome 占用）
const PROFILE = '/tmp/jimeng-manual-profile';
const url = process.argv[2] || 'https://jimeng.jianying.com/';

const ctx = await chromium.launchPersistentContext(PROFILE, {
  headless: false,
  viewport: { width: 1280, height: 720 },
  locale: 'zh-CN',
  timezoneId: 'Asia/Shanghai',
  args: [`--remote-debugging-port=${PORT}`],
});

const page = ctx.pages()[0] || (await ctx.newPage());
await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch((e) => {
  console.error('goto failed:', e.message);
});

console.log('READY — CDP port', PORT);
console.log('URL', page.url());
console.log('TITLE', await page.title());

// 保持浏览器打开，等待用户手动登录；登录后由后续脚本接管。
await new Promise(() => {});
