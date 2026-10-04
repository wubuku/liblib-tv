import fs from 'node:fs';
import path from 'node:path';

const DIR = 'docs/user-manual/jimeng-canvas';
const so = fs.readFileSync(path.join(DIR, 'SOURCE_OBSERVATIONS.md'), 'utf8');
const 头 = so.split('\n').findIndex((L) => L.startsWith('| 全灭项 | 缺的前置状态 |'));
if (头 < 0) { console.error('🔴 找不到分诊表'); process.exit(1); }
const 行 = so.split('\n').slice(头, 头 + 14);
const 提取 = (L) => [...L.matchAll(/`([a-z][a-z0-9-]{4,})`/g)].map((m) => m[1])
  .filter((x) => x.includes('-') && !x.startsWith('-'));
const 清单 = [];
for (const L of 行.slice(2)) {
  if (!L.startsWith('|')) break;
  清单.push({ 整行: L, 列: L.split('|').slice(1, -1).map((c) => c.trim()), testid: 提取(L) });
}
if (!清单.length) { console.error('🔴 提取到 0 行'); process.exit(1); }
console.log('=== §4.49 分诊表：' + 清单.length + ' 行 ===\n');

// 「这一行是否已声明验成」——🔴 必须读**整行**，不能截断：
//    第一版把行截到 90 字，于是看不到后半段的 `~~…~~` 与 `✅ 批次 1xx 验成`，把已更新的行误判成未验。
const 已声明验成 = (整行) => /~~[^|]*~~/.test(整行) && /验成|已验证|批次\s*1\d\d/.test(整行);

const 别处 = new Map();
(function walk(d) {
  for (const f of fs.readdirSync(d, { withFileTypes: true })) {
    if (['node_modules', 'screenshots'].includes(f.name) || f.name.startsWith('.')) continue;
    const p = path.join(d, f.name);
    if (f.isDirectory()) walk(p);
    else if (f.name.endsWith('.md') && f.name !== 'SOURCE_OBSERVATIONS.md') 别处.set(f.name, fs.readFileSync(p, 'utf8'));
  }
})(DIR);

const 表 = [];
for (const r of 清单) {
  const 别处命中 = [];
  for (const [f, t] of 别处) {
    const ls = t.split('\n');
    ls.forEach((L, i) => {
      if (!L.includes('`' + r.testid.join('`') + '`') && !r.testid.some((n) => L.includes('data-testid="' + n + '"'))) return;
      const 窗 = ls.slice(Math.max(0, i - 3), i + 4).join('\n');
      if (/实测|命中\s*\d|验成|已验证|逐字|屏上|\d+×\d+/.test(窗))
        别处命中.push({ 文件: f, 行: i + 1, 片段: L.replace(/\s+/g, ' ').trim().slice(0, 60) });
    });
  }
  const 正文 = [...别处.values()];
  const 任一有记录 = r.testid.some((n) =>
    正文.some((t) => t.split('\n').some((L) => L.includes('`' + n + '`') || L.includes('data-testid="' + n + '"'))));
  表.push({ ...r, 声明验成: 已声明验成(r.整行), 别处有记录: 任一有记录, 证据: 别处命中 });
}

console.log('行  状态        testid');
let 真冲突 = 0;
for (const r of 表) {
  const 状态 = r.声明验成 ? '✅表内已更新' : r.别处有记录 ? '🔴表外已验到' : '⚪两处都没有';
  if (状态.startsWith('🔴')) 真冲突++;
  console.log('  ' + 状态.padEnd(12) + r.testid.join(' '));
  for (const e of r.证据.slice(0, 2)) console.log('        ↳ ' + e.文件 + ':' + e.行 + '  ' + e.片段);
}
console.log('\n🔴 **真冲突（表里说没验、手册别处已经验到）**：' + 真冲突 + ' 行');
for (const r of 表.filter((x) => !x.声明验成 && x.别处有记录))
  console.log('  · ' + r.testid.join(' / ') + '\n      表内现写法：' + r.列.slice(1).join(' | ').slice(0, 80));
console.log('\n⚪ 两处都没有的：' + (表.filter((x) => !x.声明验成 && !x.别处有记录).map((r) => r.testid.join('/')).join('  ') || '（无）'));
