// 从已在运行的外部 Chromium（CDP 9222）提取 liblib.tv 登录态，落盘为 storageState。
//
// 用途：后续所有取证脚本都用 **无头** 浏览器 + 这份 storageState 启动，
// 既不打扰用户正在使用的有头窗口，也不需要重新登录。
//
// 只导出 www.liblib.tv / liblib.tv / www.liblib.art 三个 origin 的 cookie 与
// localStorage。文件写入 tools/.auth/ 且已在 .gitignore 中，绝不进版本库。
//
// 用法：node tools/extract-auth.mjs
import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, '.auth/libtv-storage-state.json');
const CDP = 'http://127.0.0.1:9222';
const ORIGIN = 'https://www.liblib.tv';

const browser = await chromium.connectOverCDP(CDP);
const ctx = browser.contexts()[0];
if (!ctx) throw new Error('no browser context on CDP endpoint');

// 找到 LibTV 画布页，没有就新开一个（同一 context，共用登录态）。
let page = ctx.pages().find((p) => p.url().includes('liblib.tv'));
if (!page) {
  page = await ctx.newPage();
  await page.goto(`${ORIGIN}/canvas`, { waitUntil: 'domcontentloaded', timeout: 60000 });
}

const cookies = await ctx.cookies();
const origin = new URL(page.url()).origin;

// Playwright 的 storageState 格式：cookies + origins[{origin, localStorage}]。
const kept = cookies.filter(
  (c) => /(^|\.)liblib\.(tv|art)$/.test(new URL('https://' + c.domain.replace(/^\./, '')).hostname),
);

const localStorage = await page.evaluate(() => {
  const out = [];
  for (let i = 0; i < localStorage.length; i += 1) {
    const k = localStorage.key(i);
    out.push({ name: k, value: localStorage.getItem(k) ?? '' });
  }
  return out;
});

// 只打印元信息，不打印任何 token/cookie 值。
console.log('page url      :', page.url());
console.log('page title    :', await page.title());
console.log('cookie count  :', kept.length, '(domains:', [...new Set(kept.map((c) => c.domain))].join(', '), ')');
console.log('localStorage  :', localStorage.length, 'keys:', localStorage.map((e) => e.name).join(', ').slice(0, 300));

await mkdir(dirname(OUT), { recursive: true });
await writeFile(
  OUT,
  JSON.stringify({ cookies: kept, origins: [{ origin, localStorage }] }, null, 2),
  'utf8',
);
console.log('written       :', OUT);

// 断开 CDP 但不关闭用户的浏览器。
await browser.close();
