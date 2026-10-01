// 即梦画布手册 · 截图 alt 一致性审计
// 即梦画布手册 · 截图 alt 一致性审计（长期资产）
// 目的：截图的 alt 既是无障碍描述，也是「这张图证明了什么」的证据声明。
// 批次 15 修订了工具条事实后，存量 alt 可能仍在描述旧结论。本脚本逐张核对：
//   1) manifest 登记的 alt 与正文引用处是否逐字一致（构建器对一字之差即报 warn）
//   2) 是否有截图登记了却没被任何正文引用
//   3) alt 文案里是否残留与当前实测结论冲突的措辞
import fs from 'node:fs';
import path from 'node:path';

const DIR = 'docs/user-manual/jimeng-canvas';
const y = fs.readFileSync(path.join(DIR, 'screenshots/manifest.yml'), 'utf8');
const blocks = y.split(/\n  - file: /).slice(1);

const altByPath = new Map();
const walk = (d) => {
  for (const f of fs.readdirSync(d)) {
    const p = path.join(d, f);
    if (fs.statSync(p).isDirectory()) { if (f !== 'screenshots' && !f.startsWith('.')) walk(p); continue; }
    if (!f.endsWith('.md')) continue;
    for (const m of fs.readFileSync(p, 'utf8').matchAll(/!\[([^\]]*)\]\(([^)]+)\)/g)) {
      const target = path.resolve(path.dirname(p), m[2]);
      if (!altByPath.has(target)) altByPath.set(target, []);
      altByPath.get(target).push({ file: path.relative(DIR, p), alt: m[1] });
    }
  }
};
walk(DIR);

let ok = 0, altMismatch = 0, unreferenced = 0;
const issues = [];
for (const b of blocks) {
  const file = b.split('\n')[0].trim();
  const abs = path.resolve(DIR, file);
  const refs = altByPath.get(abs) || [];
  const mAlt = (b.match(/^\s+alt: (.+)$/m) || [])[1];
  if (!refs.length) { unreferenced++; issues.push(`未被正文引用  ${file}`); continue; }
  if (!mAlt) { issues.push(`manifest 缺 alt  ${file}`); continue; }
  const bad = refs.filter((r) => r.alt !== mAlt);
  if (bad.length) {
    altMismatch++;
    issues.push(`alt 不一致  ${file}\n    manifest: ${mAlt.slice(0, 90)}\n    正文(${bad[0].file}): ${bad[0].alt.slice(0, 90)}`);
  } else ok++;
}
console.log(`截图总数 ${blocks.length}：逐字一致 ${ok} / 不一致 ${altMismatch} / 未被引用 ${unreferenced}\n`);
if (issues.length) console.log(issues.join('\n')); else console.log('引用与 alt 一致性：无问题');

// alt 文案与当前实测结论的冲突（用子串匹配，避开正则的全角标点坑）
const SUBSTR_RULES = [
  ['不弹工具条', 'alt 写「不弹工具条」；实测空节点仍用 node-toolbar 容器（680×208）改放生成面板'],
  ['背景色 / 下载', 'alt 把「下载」写进组工具条；2026-10-01 复核实测组工具条仅三项，无下载'],
  ['背景色/下载', 'alt 把「下载」写进组工具条；2026-10-01 复核实测组工具条仅三项，无下载'],
  ['1 nodes', 'alt 用了复数 1 nodes；实测状态行为单数 1 node'],
  ['Add tags（图标）', 'alt 把 Add tags 写成工具条项；实测它是节点自身的 flow-node-selected-tag 按钮'],
];
console.log('\n=== alt 措辞与当前实测结论的冲突扫描 ===');
let hit = 0;
for (const b of blocks) {
  const file = b.split('\n')[0].trim();
  const a = (b.match(/^\s+alt: (.+)$/m) || [])[1] || '';
  for (const [needle, why] of SUBSTR_RULES) {
    if (a.includes(needle)) { console.log(`  ${file}\n    ${why}\n    alt: ${a.slice(0, 120)}`); hit++; }
  }
}
console.log(hit === 0 ? '  无冲突' : `  命中 ${hit} 处`);
