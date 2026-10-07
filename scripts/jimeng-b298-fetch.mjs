/**
 * 批次 298 · 把两个构建产物拉下来，按字符偏移摘出关键函数。
 *
 * 📌 纯静态：只发 HTTPS GET 取 .js，**不执行页面代码、不开浏览器、不点任何东西**。
 * 📌 偏移是「字符偏移」不是行号（这两个 bundle 都是压缩过的单行文件）。
 *
 * 用法：node scripts/jimeng-b298-fetch.mjs [输出目录，默认 /tmp/b298]
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const OUT = process.argv[2] || '/tmp/b298';
const BASE = 'https://lf3-lv-buz.vlabstatic.com/obj/image-lvweb-buz/ies/lvweb/octo_web/static/js';
const 文件 = {
  'canvas-core.js': `${BASE}/canvas-core.1f223ad77e.js`,
  'canvas-view.js': `${BASE}/canvas-view.25249acfc0.js`,
};

// 关键偏移与说明（全部来自批次 286 当天那份构建）
const 摘录 = [
  ['canvas-core.js', 779698, 'function vs(', 'vs / vf：安全区按目标盒求缩放'],
  ['canvas-core.js', 779837, 'function vd(', 'vd：把目标居中到安全区'],
  ['canvas-core.js', 778424, '"locateContent"===e.mode', 'locateContent 分支'],
  ['canvas-core.js', 775997, 'function ve(', 've：安全区 = 视口矩形四边各减 inset'],
  ['canvas-core.js', 813405, 'function vO(', 'vO：compound = 盒 ⊕ (attached + chrome × g(zoom))'],
  ['canvas-core.js', 797570, 'target:i.compound', 'resolvePresentationValue 用的是 compound'],
  ['canvas-core.js', 799451, 'compound:vO(', 'resolveTargetBounds 组装 compound'],
  ['canvas-core.js', 796901, 'for(let r=0;r<24;r+=1)', '定点迭代：最多 24 轮'],
  ['canvas-core.js', 1212 * 0 + 775997, null, null], // 占位会被跳过
];

fs.mkdirSync(OUT, { recursive: true });
const 内容 = {};

// 🔴 用 curl 而不是 fetch：批次 298 实测 node 的 fetch 在这个 CDN 上会挂住（180s 超时、
//    一个字节都没落盘）⇒ 下载这步一律走 curl 子进程，并自己管超时。
for (const [名, url] of Object.entries(文件)) {
  const 目标 = path.join(OUT, 名);
  execFileSync('curl', ['-sS', '--max-time', '120', '-o', 目标, url], { stdio: ['ignore', 'pipe', 'pipe'] });
  const txt = fs.readFileSync(目标, 'utf8');
  if (txt.length < 1000) throw new Error(`${名} 取回来的内容只有 ${txt.length} 字符，像是失败页`);
  内容[名] = txt;
  console.log(`${名}｜${txt.length} 字符｜${url}`);
}

console.log('\n════ 摘录 ════');
for (const [名, off, 锚, 说明] of 摘录) {
  if (锚 === null) continue;
  const s = 内容[名];
  if (typeof off !== 'number' || off >= s.length) continue;
  const 实际 = s.indexOf(锚, Math.max(0, off - 2000));
  if (实际 < 0) { console.log(`🔴 ${名}｜${锚}｜没找到`); continue; }
  console.log(`\n── ${名} @${实际}｜${说明} ──`);
  console.log(s.slice(Math.max(0, 实际 - 120), 实际 + 340).replace(/\n/g, ' '));
}

// g(zoom) 的定义所在模块
const core = 内容['canvas-core.js'];
const m = core.indexOf('83399(e,t,i){');
if (m >= 0) {
  console.log(`\n── canvas-core.js @${m}｜模块 83399：g(zoom) 的定义 ──`);
  console.log(core.slice(m, m + 420).replace(/\n/g, ' '));
} else {
  console.log('\n🔴 模块 83399 的定义没找到');
}

// 字面量 1212 在 bundle 里出现几次（用来判断阈值是不是硬编码）
for (const [名, s] of Object.entries(内容)) {
  const c = (s.match(/1212/g) || []).length;
  console.log(`字面量 1212 在 ${名} 里出现 ${c} 次`);
}

console.log(`\n写入 ${OUT}/`);
process.exit(0);
