/**
 * 批次 255 · 第二步：**把「样式表读不到」这个覆盖缺口补上**，否则那个负结论不成立。
 *
 * 📌 `jimeng-b255.mjs` 的结论是「`412`/`532` 在 `54789` 条几何/CSS 读量里 `0` 命中」，
 *   🔴 但它自己报出来：**8 张样式表里 6 张跨域、`cssRules` 抛错、根本没读到**。
 *   ⇒ 立规 126：**门全绿只说明它看过的地方没问题。** 没看过的那 6 张必须补，
 *   否则「CSS 里没有 `412`」这句话只覆盖了 2/8。
 *
 * 📌 补法（**绕开 CORS 而不是绕过判据**）：
 *   页面里把每张样式表的 `href` 列出来 → **Node 侧直接 `fetch` 文本**（服务端无 CORS 限制）
 *   → 对 CSS 全文做字面量扫描。
 *   ⚠️ **同时必须报出抓不到的**，抓不到就还是覆盖缺口（立规 126）。
 *
 * 📌 扫描口径（**与 b255 保持一致**，否则两批不可比）：
 *   只认 `(^|[^0-9.])412([^0-9.]|$)` 这种「完整数值」匹配，
 *   避免 `1412` / `0.532` / `var(--x-4123)` 这类误报。
 *
 * 🔴 纪律：只读、只抓公开静态资源；一个控件都不点；不建不删不上传不生成不扣费不分享。
 *
 * 用法：node scripts/jimeng-b255b.mjs      （读数落盘 /tmp/b255b.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B255B_OUT || '/tmp/b255b.json';
const 高 = 720, 宽 = 500;
const 目标 = [412, 532];

const log = (...a) => console.log(a.join(' '));

const out = { 轮次: 'b255b', 宽, 高, 目标, 表: [], 统计: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
try {
  await p.setViewportSize({ width: 宽, height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(5500);

  // 📌 页面里只做一件事：把每张样式表的 href / 内联标记列出来
  const 表 = await p.evaluate(() => Array.from(document.styleSheets).map((sh, i) => ({
    i,
    href: sh.href || null,
    内联: !sh.href,
    ownerNode: sh.ownerNode ? sh.ownerNode.tagName.toLowerCase() : null,
    内联长度: !sh.href && sh.ownerNode ? (sh.ownerNode.textContent || '').length : null,
  })));
  log(`页面声明样式表 ${表.length} 张：内联 ${表.filter((x) => x.内联).length} / 外链 ${表.filter((x) => !x.内联).length}`);
  out.表 = 表;
} catch (e) {
  log('🔴 列样式表失败 ' + e.message);
  out.错误 = e.message;
} finally {
  try { await p.close(); } catch (e) { /* 忽略 */ }
}

// 📌 Node 侧抓文本：服务端请求没有 CORS 限制；抓不到就**如实记成覆盖缺口**
const 正则 = (v) => new RegExp(`(^|[^0-9.])${v}([^0-9.]|$)`);
let 抓到 = 0, 抓不到 = 0, 字节 = 0, 命中 = 0;
for (const sh of out.表) {
  const 记 = { i: sh.i, href: sh.href, 内联: sh.内联 };
  let 文本 = null;
  if (sh.内联) {
    log(`  #${sh.i} 内联样式（${sh.内联长度} 字符）—— 本步只扫外链，内联另由 b255 覆盖`);
    记.状态 = '内联，另由 b255 覆盖';
    out.表[sh.i].记 = 记;
    continue;
  }
  try {
    const resp = await fetch(sh.href, { headers: { 'User-Agent': 'Mozilla/5.0' } });
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    文本 = await resp.text();
    抓到++; 字节 += 文本.length;
  } catch (e) {
    抓不到++;
    记.状态 = '抓取失败';
    记.错误 = e.message;
    log(`  🔴 #${sh.i} 抓取失败 ${e.message} —— ${(sh.href || '').slice(-70)}`);
    out.表[sh.i].记 = 记;
    continue;
  }
  const 命中项 = [];
  for (const v of 目标) {
    const re = 正则(v);
    let m, n = 0;
    while ((m = re.exec(文本)) !== null && n < 6) {
      const 起 = Math.max(0, m.index - 90), 止 = Math.min(文本.length, m.index + 90);
      命中项.push({ 值: v, 片段: 文本.slice(起, 止).replace(/\s+/g, ' ') });
      n++;
    }
    if (n === 6) 命中项.push({ 值: v, 片段: '（命中 ≥6 次，已截断）' });
  }
  记.状态 = '已抓';
  记.字符数 = 文本.length;
  记.命中 = 命中项;
  命中 += 命中项.length;
  log(`  #${sh.i} ✅ ${文本.length} 字符，命中 ${命中项.length} 条  ${(sh.href || '').slice(-70)}`);
  for (const h of 命中项) log(`      🎯 ${h.值} … ${h.片段} …`);
  out.表[sh.i].记 = 记;
}

out.统计 = { 表总数: out.表.length, 抓到, 抓不到, 扫过字符: 字节, 命中 };
log('=== 汇总 ===');
log(`外链 ${抓到 + 抓不到} 张：抓到 ${抓到} / 抓不到 ${抓不到}；扫过 ${字节} 字符；命中 ${命中} 条`);
if (抓不到) log(`⚠️ **仍有 ${抓不到} 张没扫到 ⇒ 覆盖缺口如实留档**（立规 126）`);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);