// 站点产物渲染体检 —— 构建脚本说 ok 不等于页面好看，这一轮专门用眼睛看。
//
// 用无头浏览器打开本地静态服务，逐页截图，抓四类「构建层看不见、渲染后才暴露」的问题：
//   1. 图片裂了（alt 会显示出来）
//   2. 表格被劈开 / 渲染成一团竖线
//   3. 加粗失效留下字面量 **
//   4. 侧边栏/目录没出来
//
// 截图落在 .evidence/site/，不混进 screenshots/ —— 那些是要进手册的正配图。
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { extname, join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const DIST = resolve(HERE, '../.vitepress/dist');
const SHOT = resolve(HERE, '.evidence/site');
if (!existsSync(DIST)) { console.error('找不到 dist，先跑 ./build-site.sh'); process.exit(1); }
await mkdir(SHOT, { recursive: true });

const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.json': 'application/json', '.woff2': 'font/woff2', '.ico': 'image/x-icon' };

const server = createServer(async (req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  const file = join(DIST, p);
  if (!existsSync(file)) { res.writeHead(404); res.end('not found'); return; }
  res.writeHead(200, { 'Content-Type': MIME[extname(file)] || 'application/octet-stream' });
  res.end(await readFile(file));
});
await new Promise((r) => server.listen(4178, r));
const BASE = 'http://localhost:4178';

const PAGES = [
  ['index', '/'],
  ['00-quickstart', '/00-quickstart.html'],
  ['10-tasks-create-nodes', '/10-tasks/create-nodes.html'],
  ['10-tasks-shortcuts', '/10-tasks/shortcuts.html'],
  ['10-tasks-organize-canvas', '/10-tasks/organize-canvas.html'],
  ['20-reference', '/20-reference.html'],
  ['90-troubleshooting', '/90-troubleshooting.html'],
];

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, locale: 'zh-CN' });
const report = [];
try {
  for (const [name, path] of PAGES) {
    const page = await ctx.newPage();
    const consoleErrs = [];
    page.on('console', (m) => { if (m.type() === 'error') consoleErrs.push(m.text().slice(0, 160)); });
    page.on('pageerror', (e) => consoleErrs.push(`pageerror: ${String(e).slice(0, 160)}`));
    await page.goto(BASE + path, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);

    const diag = await page.evaluate(() => {
      const imgs = [...document.querySelectorAll('img')];
      const broken = imgs.filter((i) => i.complete && i.naturalWidth === 0).map((i) => i.getAttribute('src'));
      const tables = [...document.querySelectorAll('table')];
      // 表格行里的单元格数是否一致（列数被劈开时会不一致）
      const ragged = tables.filter((t) => {
        const rows = [...t.querySelectorAll('tr')].map((r) => r.children.length);
        return rows.length > 1 && new Set(rows).size > 1;
      }).length;
      const main = document.querySelector('main') || document.body;
      const text = main.innerText || '';
      return {
        title: document.title,
        h1: document.querySelector('h1')?.innerText?.trim() || null,
        imgs: imgs.length, brokenImgs: broken,
        tables: tables.length, raggedTables: ragged,
        literalAsterisks: (text.match(/\*\*/g) || []).length,
        rawPipes: (text.match(/\|\s*-{3,}\s*\|/g) || []).length,
        hasSidebar: !!document.querySelector('.VPSidebar, .vp-sidebar, aside'),
        mainChars: text.replace(/\s+/g, '').length,
        outlineItems: document.querySelectorAll('.VPDocOutlineItem a, .outline-link').length,
      };
    });
    await page.screenshot({ path: join(SHOT, `${name}.png`), fullPage: false });
    report.push({ name, path, ...diag, consoleErrs });
    console.log(`\n### ${name}`);
    console.log('  h1:', JSON.stringify(diag.h1), '| 正文字数', diag.mainChars);
    console.log('  图', diag.imgs, '裂图', diag.brokenImgs.length ? diag.brokenImgs : '无');
    console.log('  表', diag.tables, '列数不齐', diag.raggedTables ? diag.raggedTables : '无');
    console.log('  字面量 **', diag.literalAsterisks, '| 裸管道表格', diag.rawPipes);
    console.log('  侧边栏', diag.hasSidebar ? '有' : '无', '| 本页目录', diag.outlineItems, '项');
    if (consoleErrs.length) console.log('  控制台错误:', consoleErrs);
    await page.close();
  }

  // 侧边栏展开状态：单独截一张全高页面
  const page = await ctx.newPage();
  await page.goto(`${BASE}/10-tasks/shortcuts.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(500);
  await page.screenshot({ path: join(SHOT, '_full-shortcuts.png'), fullPage: true });
  await page.close();
} finally {
  await browser.close();
  server.close();
}
await writeFile(resolve(HERE, '.evidence/site-report.json'), JSON.stringify(report, null, 2));

const bad = report.filter((r) => r.brokenImgs.length || r.raggedTables || r.literalAsterisks || !r.hasSidebar || r.consoleErrs.length);
console.log(`\n${'='.repeat(60)}`);
console.log(bad.length ? `⚠️ ${bad.length} 页有问题：${bad.map((b) => b.name).join(', ')}` : '✅ 7 页全部干净');
console.log(`截图目录: ${SHOT}`);
