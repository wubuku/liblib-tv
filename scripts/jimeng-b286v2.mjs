/**
 * 批次 286 v2：给「搜不到」这件事装一个**阳性对照**。
 *
 * 📌 v1 的结果（2026-10-07，8.56 MB / 17 个文件）：
 *   命中 5/8 针 —— `getNodesBounds` `fitView` `octo-canvas-connection-stroke-world-width`
 *                （这三根是真的，见下）；`4091` `2520` **全是噪声**（SVG 路径数字里的子串）。
 *   未命中 3 针 —— `getViewportForBounds` `canvas-search-results-viewport` `octo-space-6`。
 *
 * 🔴 **但这三针「未命中」目前无法解释成「不在代码里」**，因为：
 *   `canvas-search-results-viewport` 是批次 281/282 在**运行态 DOM 里实测存在**的 testid，
 *   同一个字符串在 bundle 里搜不到 ⇒ 只有两种可能，**必须分开**：
 *     ① **下载集不全** —— 搜索面板那块代码在一个 v1 没下到的 chunk 里；
 *     ② **字符串不是逐字写的** —— 由拼接/模板生成（如 `canvas-search-result${a}-${b}`）。
 *   ⇒ 这正是立规 160：**「某件事没发生」有两种解释，不测就是不知道是哪种。**
 *
 * 📌 **本批只做一件事：把①排除掉。** 做法是**阳性对照**：
 *   先取两根**已知必然在**的字符串当对照：
 *     A. `react-flow__node`      —— 类名；批次 281 等反复实测在 DOM 里；react-flow 代码在 canvas-view（v1 已证 `fitView` 在）
 *     B. `canvas-search-result-node_` —— testid 前缀；批次 281 实测形如 `canvas-search-result-node_236ctpehgg`
 *   然后把脚本来源**换成两条通路求并集**：
 *     通路一：`document.querySelectorAll('script[src]')` —— v1 用的
 *     通路二：`performance.getEntriesByType('resource')` 里所有 `.js` —— 含**动态插入后又被移除**的 chunk
 *     通路三：`<link rel=stylesheet>` —— CSS 里才有的 `octo-space-6`
 *   **若 A 命中而 B 不命中 ⇒ 判定「①下载集不全」，v1 那三针的未命中全部作废。**
 *   若 A、B 都命中 ⇒ 判定「②字符串是拼的」，去搜它的组成部分。
 *
 * 📌 **三条前提**：
 *   ① **对照必须先于判定**：对照没响，任何「未命中」都不出结论（与立规 160 第 4 条同型）；
 *   ② **同时报告三条通路各自的长度与差集** —— 「并集比单路多出哪些文件」本身就是观测量；
 *   ③ **构建标识照记**：手册里引用代码必须写清是哪次构建（立规 147 的同型风险）。
 *
 * 📌 **纪律**：**只读网络资源**，不点任何东西、不改任何状态；
 *   不进扣费页、绝不点生成；末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b286v2.mjs   （落盘 /tmp/b286v2.json，命中片段 /tmp/b286v2-hits.txt）
 */
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const URL_页面 = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B286V2_OUT || '/tmp/b286v2.json';
const 目录 = '/tmp/b286v2-bundles';
const 最大单文件 = 32 * 1024 * 1024;
const 上下文长度 = 300;
const 每针最多片段 = 4;

const 对照针 = ['react-flow__node', 'canvas-search-result-node_'];
const 探针 = [
  'canvas-search-results-viewport',
  'canvas-search-panel',
  'canvas-search-result-',
  'octo-space-6',
  'getViewportForBounds',
  'getContentBounds',
  'getInternalNodesBounds',
  'octo-canvas-connection-stroke-world-width',
];
const 针 = [...对照针, ...探针];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b286v2',
  问: 'v1 那三针「未命中」是①下载集不全，还是②字符串是拼的？',
  对照针, 探针, 全部针: 针,
  通路: {}, bundle: [], 命中: {}, 末态: {},
};

fs.mkdirSync(目录, { recursive: true });
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

// ── 1. 页面状态 + 三条通路的清单（清单已落盘则复用，避免每次重新导航）──
const URLS = '/tmp/b286v2-urls.json';
let 通路一 = [], 通路二 = [], 通路三 = [];
if (fs.existsSync(URLS)) {
  const c = JSON.parse(fs.readFileSync(URLS, 'utf8'));
  通路一 = c.通路一; 通路二 = c.通路二; 通路三 = c.通路三; out.末态 = c.末态; out.构建标识 = c.构建标识;
  out.通路 = c.通路;
  log(`复用已落盘清单（${new Date(fs.statSync(URLS).mtime * 1000).toLocaleTimeString()}）：` +
      `通路一 ${通路一.length}｜通路二 ${通路二.length}｜通路三 ${通路三.length}`);
} else {
const p = await ctx.newPage();
try {
  await p.setViewportSize({ width: 1280, height: 720 });
  await p.goto(URL_页面, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(8000);

  out.末态.节点数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.末态.状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
  out.末态.积分 = await p.evaluate(() => (document.body.innerText.match(/(\d[\d,]*)\s*\n?积分/) || [])[1] || null);
  out.末态.通过 = out.末态.节点数 === 76 && /0 selected/.test(out.末态.状态行 || '');

  const 三 = await p.evaluate(() => {
    const 去 = (u) => u.split('?')[0];
    return {
      脚本: Array.from(document.querySelectorAll('script[src]')).map((s) => s.src),
      资源: performance.getEntriesByType('resource').map((e) => e.name).filter((u) => /\.js(\?|$)/.test(u)).map(去),
      样式: Array.from(document.querySelectorAll('link[rel="stylesheet"], link[rel="modulepreload"]'))
        .map((l) => l.href).filter((u) => /\.css(\?|$)/.test(u)).map(去),
      资源全: performance.getEntriesByType('resource').length,
    };
  });
  通路一 = [...new Set(三.脚本)];
  通路二 = [...new Set(三.资源)];
  通路三 = [...new Set(三.样式)];
  out.末态.资源条目总数 = 三.资源全;

  const 短 = (u) => (u.split('/').pop() || '').split('?')[0];
  out.通路 = {
    通路一_脚本标签: 通路一.length,
    通路二_性能资源: 通路二.length,
    通路三_样式表: 通路三.length,
    二减一: 通路二.filter((u) => !通路一.includes(u)).map(短),
    一减二: 通路一.filter((u) => !通路二.includes(u)).map(短),
    交集: 通路一.filter((u) => 通路二.includes(u)).length,
  };
  out.构建标识 = [...通路一, ...通路二, ...通路三]
    .map(短).filter((n) => /[.-][0-9a-f]{6,}/i.test(n)).slice(0, 60);
  log(`通路一 脚本标签 ${通路一.length}｜通路二 性能资源 ${通路二.length}｜通路三 样式 ${通路三.length}`);
  log(`二−一（只有性能资源里有）${out.通路.二减一.length} 个：${out.通路.二减一.join(', ') || '（无）'}`);
  log(`一−二（只有脚本标签里有）${out.通路.一减二.length} 个：${out.通路.一减二.join(', ') || '（无）'}`);
  log(`构建片段 ${out.构建标识.length} 个：${out.构建标识.slice(0, 12).join(', ')}`);
  fs.writeFileSync(URLS, JSON.stringify({ 通路一, 通路二, 通路三, 末态: out.末态, 通路: out.通路, 构建标识: out.构建标识 }, null, 1));
  log(`清单落盘 ${URLS}`);
} finally {
  try { await p.close(); } catch (e) { /* 忽略 */ }
}
}

// ── 2. 下载（三条通路并集，去重；并行 12 路） ──
const 全部 = [...new Set([...通路一, ...通路二, ...通路三])];
let 下了字节 = 0, 搜了字节 = 0;
const 并发 = 12;
for (let i = 0; i < 全部.length; i += 并发) {
  const 批 = 全部.slice(i, i + 并发);
  const 记组 = await Promise.all(批.map(async (u) => {
    const 记 = { url: u, 来源: [通路一.includes(u) ? '标签' : null, 通路二.includes(u) ? '资源' : null, 通路三.includes(u) ? '样式' : null].filter(Boolean).join('+') };
    try {
      const resp = await fetch(u, { headers: { accept: '*/*' } });
      记.status = resp.status;
      const buf = Buffer.from(await resp.arrayBuffer());
      记.字节 = buf.length;
      if (buf.length > 最大单文件) { 记.跳过 = '超过单文件上限'; return 记; }
      const 名 = (u.split('/').pop() || `f-${i}`).split('?')[0].replace(/[^\w.-]/g, '_');
      const 文件 = path.join(目录, 名);
      fs.writeFileSync(文件, buf);
      记.文件 = 文件; 记.文本 = buf.toString('utf8');
      return 记;
    } catch (e) {
      记.错误 = e.message;
      return 记;
    }
  }));
  out.bundle.push(...记组);
  下了字节 += 记组.reduce((a, x) => a + (x.字节 || 0), 0);
  if (Math.floor(i / 并发) % 10 === 0) log(`  … ${Math.min(i + 并发, 全部.length)}/${全部.length}，累计 ${(下了字节 / 1048576).toFixed(2)} MB`);
}
for (const x of out.bundle) if (x.错误) log(`↓ 🔴 ${x.错误}｜${x.url}`);
out.下载 = {
  文件数: out.bundle.filter((x) => x.文件).length,
  总字节: 下了字节,
  失败: out.bundle.filter((x) => x.错误).map((x) => x.url),
  各文件: out.bundle.filter((x) => x.文件).map((x) => `${path.basename(x.文件)} ${x.字节}`),
};
log(`\n↓ 共 ${out.下载.文件数} 个文件 / ${下了字节} 字节`);

// ── 3. 搜 ──
for (const x of out.bundle) {
  if (!x.文件 || !x.文本) continue;
  搜了字节 += x.文本.length;
  for (const needle of 针) {
    const 全部次 = x.文本.split(needle).length - 1;
    if (!全部次) continue;
    const 片 = [];
    let i = x.文本.indexOf(needle), n = 0;
    while (i >= 0 && n < 每针最多片段) {
      const s = Math.max(0, i - 上下文长度), e = Math.min(x.文本.length, i + needle.length + 上下文长度);
      片.push({ 位置: i, 片段: x.文本.slice(s, e) });
      i = x.文本.indexOf(needle, i + needle.length); n++;
    }
    (out.命中[needle] = out.命中[needle] || []).push({ 文件: x.文件, 出现次数: 全部次, 片段: 片 });
  }
}
out.搜索 = { 搜了字符: 搜了字节, 命中的针: Object.keys(out.命中) };

// ── 4. 前提①：阳性对照必须先响 ──
const 报告 = [];
for (const n of 对照针) {
  const h = out.命中[n];
  报告.push(`${n}：${h ? `✅ 命中 ${h.reduce((a, x) => a + x.出现次数, 0)} 次（${h.map((x) => path.basename(x.文件)).join(', ')}）` : '🔴 未命中'}`);
}
log('\n════ 阳性对照 ════\n' + 报告.join('\n'));

const 对照A = !!out.命中['react-flow__node'];
const 对照B = !!out.命中['canvas-search-result-node_'];
let 判定;
if (下了字节 === 0 || 搜了字节 === 0) {
  判定 = '🔴 一个字节都没下全 ⇒ 整组作废';
} else if (对照A && !对照B) {
  判定 = '① **下载集不全**：已知在 DOM 里的 `canvas-search-result-node_` 前缀搜不到 ⇒ v1/v2 的三针未命中全部作废，搜索面板那块代码在没下到的资源里';
} else if (对照A && 对照B) {
  判定 = '② **字符串不是逐字写的**：对照全响，`canvas-search-results-viewport` 却搜不到 ⇒ 该 testid 由拼接生成，去搜它的组成部分（见 `canvas-search-result-` 一针）';
} else if (!对照A) {
  判定 = '🔴 连类名对照 `react-flow__node` 都没命中 ⇒ 通路本身有问题（可能下到的全是未执行的壳，或编码/解码错了），本批全部读数作废';
} else {
  判定 = '（两个对照都未命中但有字节 ⇒ 同上，作废）';
}

// ── 5. 片段落盘 ──
const 片段文件 = '/tmp/b286v2-hits.txt';
let buf = '';
for (const [needle, 组] of Object.entries(out.命中)) {
  const 标 = 对照针.includes(needle) ? '【对照】' : '【探针】';
  for (const g of 组) {
    for (const [i, f] of g.片段.entries()) {
      buf += `\n\n########## ${标}针：${needle}｜文件：${path.basename(g.文件)}｜第 ${i + 1}/${g.片段.length} 处（偏移 ${f.位置}）\n${f.片段}\n`;
    }
  }
}
fs.writeFileSync(片段文件, buf);
log(`\n命中片段落盘：${片段文件}（${(buf.length / 1024).toFixed(1)} KB，共 ${buf.split('##########').length - 1} 段）`);

log('\n════ 各针汇总 ════');
for (const needle of 针) {
  const h = out.命中[needle];
  if (!h) { log(`  🔴 ${needle.padEnd(42)} 未命中`); continue; }
  const 总 = h.reduce((a, x) => a + x.出现次数, 0);
  log(`  ✅ ${needle.padEnd(42)} ${总} 次，${h.length} 个文件：${h.map((x) => path.basename(x.文件)).join(', ')}`);
}

log('\n════ 判定 ════\n' + 判定);
out.判定 = 判定;
out.对照 = 报告;
out.末态复查 = { ...out.末态 };
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`\n写入 ${OUT}｜末态 ${JSON.stringify(out.末态)}`);
process.exit(0);

function 短名(u) { return (u.split('/').pop() || '').split('?')[0]; }