/**
 * 批次 286：去读应用代码 —— 把页面引用的 JS 拉下来，搜那条常量边距。
 *
 * 📌 起意（批次 283/285 依次排除后剩下的唯一一条路）：
 *   284 用独立测出的内容包围盒把「偏移」从拟合值变成观测量，确认：
 *   `s = (w − 边距) / 包围盒宽`，**包围盒宽 `4091.24`、高 `2520.49`（七档不变）**，
 *   而**边距在 `w = 373 → 374` 从 `32.0104` 跳到 `34.0104`（每边 `16.0052 → 17.0052`）**。
 *   随后依次排除：
 *     批次 283 —— 元素盒模型、文档级宽度量：`14` 个量全部 `+1`；
 *     批次 285 —— `658` 个 CSS 自定义属性：目标步变值的 `0` 个。
 *   ⇒ 🔴 **DOM 侧已经到底。** ⚠️ **机制仍未测，不编**（立规 113）。
 *
 * 📌 **本批做什么**：**把 bundle 拉下来搜**。
 *   目标不是「读懂整个应用」，而是**把那条边距的来源定位到一个具体的表达式**。
 *   搜索策略按「越具体越先命中」排序：
 *     ① **`fitView` / `getNodesBounds` / `getViewportForBounds`** ——
 *        react-flow 的适配入口，**这些是 prop/store 名，压缩后仍逐字保留**；
 *     ② **`canvas-search-results-viewport`** —— 批次 281/282 测到的 testid，
 *        它能定位搜索面板那块代码，顺带验证 testid 确实写在代码里（可作为「代码与运行态对得上」的证据）；
 *     ③ **`--octo-space-6` / `--octo-canvas-connection-stroke-world-width`** ——
 *        批次 285 读到的变量名，**能定位 octo 画布那块 chunk**；
 *     ④ **`4091` / `2520` / `16` / `17` / `32` / `34`** —— 最后才搜裸数字（噪声最大）。
 *
 * 📌 **三条前提**：
 *   ① **下载自检**：每个 bundle 下载后必须**校验字节数**与响应头一致
 *      （否则搜的是半个文件，结论无效）；
 *   ② **命中自检**：🔴 **「一个都没命中」与「文件根本没下全」长得一模一样**
 *      ⇒ 脚本必须同时报告「下了多少字节」与「搜了多少字节」，两者都非零才允许出判定；
 *   ③ 📌 **记录 bundle 的构建标识**：手册里凡引用代码，必须写清是**哪次构建**，
 *      否则下一批构建一变，这条结论就悄悄过期了（立规 147 的同型风险）。
 *
 * 📌 **纪律**：**只读网络资源**，不点任何东西、不改任何状态；
 *   不进扣费页、绝不点生成；末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b286.mjs      （落盘 /tmp/b286.json，bundle 落 /tmp/b286-bundles/）
 */
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const URL_页面 = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B286_OUT || '/tmp/b286.json';
const 目录 = '/tmp/b286-bundles';
const 最大单文件 = 24 * 1024 * 1024;
const 上下文长度 = 320;              // 命中处前后各取多少字符
const 每针最多片段 = 6;

const 针 = [
  'getViewportForBounds',
  'getNodesBounds',
  'fitView',
  'canvas-search-results-viewport',
  'octo-canvas-connection-stroke-world-width',
  'octo-space-6',
  '4091',
  '2520',
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b286',
  问: '那条常量边距（每边 16.0052→17.0052px）在 bundle 里能不能被定位到一个表达式？',
  搜索针: 针, bundle: [], 命中: {}, 末态: {},
};

fs.mkdirSync(目录, { recursive: true });
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

// ── 1. 页面状态 + 脚本清单 ──
const p = await ctx.newPage();
let 清单 = [];
try {
  await p.setViewportSize({ width: 1280, height: 720 });
  await p.goto(URL_页面, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6000);
  out.末态.节点数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.末态.状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
  out.末态.通过 = out.末态.节点数 === 76 && /0 selected/.test(out.末态.状态行 || '');

  清单 = await p.evaluate(() => Array.from(document.querySelectorAll('script[src]')).map((s) => s.src));
  // 构建标识：把带哈希的 chunk 名记下来，构建一变这些名字就变
  out.构建标识 = 清单.map((u) => (u.split('/').pop() || '').split('?')[0]).filter((n) => /[.-][0-9a-f]{6,}/i.test(n)).slice(0, 40);
  log(`脚本 ${清单.length} 个；带哈希的构建片段 ${out.构建标识.length} 个`);
} finally {
  try { await p.close(); } catch (e) { /* 忽略 */ }
}

// ── 2. 下载 ──
let 下了字节 = 0, 搜了字节 = 0;
for (const u of 清单) {
  const 记 = { url: u };
  try {
    const resp = await fetch(u, { headers: { accept: '*/*' } });
    记.status = resp.status;
    const buf = Buffer.from(await resp.arrayBuffer());
    记.字节 = buf.length;
    const 头 = resp.headers.get('content-length');
    记.contentLength = 头 ? Number(头) : null;
    // 前提①：下载自检
    记.自检 = 头 ? (Number(头) === buf.length ? '✅ 与 content-length 一致' : `🔴 不一致（头 ${头}）`) : '（无 content-length，按实收字节记）';
    if (buf.length > 最大单文件) { 记.跳过 = `超过 ${最大单文件} 字节上限`; out.bundle.push(记); continue; }
    const 名 = (u.split('/').pop() || `chunk-${out.bundle.length}`).split('?')[0].replace(/[^\w.-]/g, '_');
    const 文件 = path.join(目录, 名);
    fs.writeFileSync(文件, buf);
    记.文件 = 文件;
    记.文本 = buf.toString('utf8');
    下了字节 += buf.length;
    out.bundle.push(记);
    log(`↓ ${String(记.字节).padStart(9)} 字节  ${记.status}  ${名}  ${记.自检}`);
  } catch (e) {
    记.错误 = e.message;
    out.bundle.push(记);
    log(`↓ 🔴 ${e.message}｜${u}`);
  }
}
out.下载 = { 文件数: out.bundle.filter((x) => x.文件).length, 总字节: 下了字节, 失败: out.bundle.filter((x) => x.错误).map((x) => x.url) };

// ── 3. 搜 ──
for (const x of out.bundle) {
  if (!x.文件 || !x.文本) continue;
  搜了字节 += x.文本.length;
  for (const needle of 针) {
    let i = x.文本.indexOf(needle);
    if (i < 0) continue;
    const 片 = [];
    let n = 0;
    while (i >= 0 && n < 每针最多片段) {
      const s = Math.max(0, i - 上下文长度), e = Math.min(x.文本.length, i + needle.length + 上下文长度);
      片.push({ 位置: i, 片段: x.文本.slice(s, e) });
      i = x.文本.indexOf(needle, i + needle.length);
      n++;
    }
    const 全部 = x.文本.split(needle).length - 1;
    out.命中[needle] = out.命中[needle] || [];
    out.命中[needle].push({ 文件: x.文件, 出现次数: 全部, 片段: 片 });
  }
}
out.搜索 = { 搜了字节, 命中的针: Object.keys(out.命中) };

// 前提②：下载自检 —— 下了多少、搜了多少，两个都非零才允许出判定
if (下了字节 === 0 || 搜了字节 === 0) {
  out.判定 = { 结论: '🔴 一个字节都没下全 ⇒ 任何「都没命中」都无效，整组作废' };
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  log('\n════ 判定 ════\n' + out.判定.结论);
  process.exit(0);
}

log(`\n════ 搜索汇总 ════`);
log(`下了 ${out.下载.文件数} 个文件 / ${下了字节} 字节；搜了 ${搜了字节} 字符`);
for (const needle of 针) {
  const h = out.命中[needle];
  if (!h) { log(`  🔴 ${needle.padEnd(42)} 未命中`); continue; }
  const 总 = h.reduce((a, x) => a + x.出现次数, 0);
  log(`  ✅ ${needle.padEnd(42)} 命中 ${总} 次，分布在 ${h.length} 个文件：${h.map((x) => path.basename(x.文件)).join(', ')}`);
}

// ── 4. 把命中片段单独落盘，方便逐条读 ──
const 片段文件 = '/tmp/b286-hits.txt';
let buf = '';
for (const [needle, 组] of Object.entries(out.命中)) {
  for (const g of 组) {
    for (const [i, f] of g.片段.entries()) {
      buf += `\n\n########## 针：${needle}｜文件：${path.basename(g.文件)}｜第 ${i + 1}/${g.片段.length} 处（偏移 ${f.位置}）\n${f.片段}\n`;
    }
  }
}
fs.writeFileSync(片段文件, buf);
log(`\n命中片段落盘：${片段文件}（${(buf.length / 1024).toFixed(1)} KB，共 ${buf.split('##########').length - 1} 段）`);

// ── 5. 判定 ──
out.判定 = {
  下载字节: 下了字节, 搜了字符: 搜了字节,
  结论: Object.keys(out.命中).length
    ? `命中 ${Object.keys(out.命中).length}/${针.length} 根针；见 ${片段文件}`
    : '🔴 全部针都没命中 —— 但字节数非零，所以这**只是「这些字面量不在 bundle 里」**，不等于「那条边距不存在」',
};
log('\n════ 判定 ════\n' + out.判定.结论);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);