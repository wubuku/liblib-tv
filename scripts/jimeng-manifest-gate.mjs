// 即梦画布手册 —— 截图 manifest 真解析门（第 10 道门，批次 154 新增）
//
// 🔴 为什么必须有这道门：`screenshots/manifest.yml` **从 2026-10-01 起就不是合法 YAML**，
//    而**此前没有任何一道门发现它**，因为
//      · `jimeng-alt-audit.mjs` 用 `y.split(/\n  - file: /)` 正则切块；
//      · `build-site.sh`   用 `awk` 逐行取 `alt:`。
//    **两者都不解析 YAML。** 于是 10 条坏引号（闭合单引号后多一个 `"`、缺开引号、
//    内部裸单引号提前终止标量、未加引号的值里含 `: `）静静烂了一年。
//    📌 立规：**「这个文件语法合法吗」和「这个文件的字段齐不齐」是两个问题，
//    正则切块只能回答后者。** 要有真解析器在场。
//
// 这道门查 7 件事：
//   ① 用真 YAML 解析器解析（不过 = 红）
//   ② 每条 11 个必填字段都在且非空
//   ③ `file` 不重复
//   ④ 引用的图文件真实存在
//   ⑤ `sha256` 与磁盘上的文件逐字对上（图换了没换 manifest，一眼看出来）
//   ⑥ manifest 的 alt 与**正文引用处**的 alt 逐字一致
//   ⑦ alt 里没有 markdown 强调标记（`**` / `*`）—— 它们会进 `<img alt>` 当字面量
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';

const DIR = 'docs/user-manual/jimeng-canvas';
const MAN = path.join(DIR, 'screenshots/manifest.yml');
const PY = path.join('scripts', 'jimeng_yaml_check.py');
const 必填 = ['file', 'task_id', 'step', 'route', 'viewport', 'locale', 'captured_at', 'verified_locator', 'visible_text', 'alt', 'sha256'];

const 错 = [];
if (!fs.existsSync(PY)) {
  console.log('⛔ 缺 YAML 解析器脚本 ' + PY);
  process.exit(1);
}

// ---- ① 真解析 ----
let 条目 = null;
try {
  const r = JSON.parse(execFileSync('python3', [PY, MAN], { encoding: 'utf8' }));
  if (!r.ok) { 错.push(`① YAML 解析失败：${r.err}（行 ${r.line} 列 ${r.col}）`); }
  else 条目 = [];
} catch (e) { 错.push('① 解析器自身失败：' + e.message); }

if (条目 !== null) {
  // 真正取到列表（解析器只回计数，这里再取一次明细）
  // 🔑 必须走独立的 .py 文件且带 `default=str`：`captured_at` 会被 YAML 解析成
  //    **datetime 对象**，内联 json.dumps 会 TypeError。这条只有真解析器才看得见。
  const DUMP = path.join('scripts', 'jimeng_yaml_dump.py');
  try { 条目 = JSON.parse(execFileSync('python3', [DUMP, MAN], { encoding: 'utf8' })); }
  catch (e) { 错.push('① 取明细失败：' + e.message); 条目 = null; }
}

if (条目) {
  console.log(`manifest 解析成功：${条目.length} 条`);
  // ---- ② 必填字段 ----
  const 缺 = [];
  for (const it of 条目) {
    for (const k of 必填) if (!(k in it) || String(it[k]).trim() === '') 缺.push(`${it.file || '?'} 缺 ${k}`);
  }
  错.push(...缺.map((x) => '② ' + x));
  // ---- ③ 重复 ----
  const seen = new Map();
  for (const it of 条目) seen.set(it.file, (seen.get(it.file) || 0) + 1);
  for (const [f, n] of seen) if (n > 1) 错.push(`③ file 重复 ${n} 次：${f}`);
  // ---- ④⑤ 存在性与 sha256 ----
  let 缺图 = 0, 哈希不符 = 0;
  for (const it of 条目) {
    const p = path.join(DIR, it.file);
    if (!fs.existsSync(p)) { 缺图++; 错.push(`④ 图文件不存在：${it.file}`); continue; }
    const h = crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
    if (h !== it.sha256) { 哈希不符++; 错.push(`⑤ sha256 不符：${it.file}\n    manifest ${it.sha256}\n    磁盘    ${h}`); }
  }
  // ---- ⑥ 正文 alt 逐字一致 ----
  const 正文 = new Map();
  (function walk(d) {
    for (const f of fs.readdirSync(d)) {
      if (f === 'screenshots' || f.startsWith('.')) continue;
      const p = path.join(d, f);
      if (fs.statSync(p).isDirectory()) { walk(p); continue; }
      if (!f.endsWith('.md')) continue;
      for (const m of fs.readFileSync(p, 'utf8').matchAll(/!\[([^\]]*)\]\(([^)]+)\)/g)) {
        const t = path.resolve(path.dirname(p), m[2]);
        if (!正文.has(t)) 正文.set(t, []);
        正文.get(t).push({ file: path.relative(DIR, p), alt: m[1] });
      }
    }
  })(DIR);
  let alt错 = 0, 未引用 = 0;
  for (const it of 条目) {
    const abs = path.resolve(DIR, it.file);
    const hits = 正文.get(abs);
    if (!hits) { 未引用++; continue; }
    for (const h of hits) if (h.alt !== it.alt) { alt错++; 错.push(`⑥ alt 不一致 ${it.file}\n    manifest: ${it.alt.slice(0, 70)}\n    正文(${h.file}): ${h.alt.slice(0, 70)}`); }
  }
  // ---- ⑦ alt 里不该有 markdown 强调标记 ----
  for (const it of 条目) if (/\*\*/.test(it.alt)) 错.push(`⑦ alt 含 markdown 强调标记：${it.file}`);
  console.log(`存在性：缺图 ${缺图} ｜ sha256 不符 ${哈希不符} ｜ alt 不一致 ${alt错} ｜ manifest 有但正文未引用 ${未引用}`);
}

if (错.length) {
  console.log('\n🔴 manifest 门不通过：');
  for (const x of 错.slice(0, 12)) console.log('  ' + x);
  if (错.length > 12) console.log(`  …另有 ${错.length - 12} 条`);
  process.exit(1);
}
console.log('\n✅ manifest 门通过：真 YAML 解析 + 必填字段 + 不重复 + 文件存在 + sha256 + 正文 alt 逐字一致 + alt 无强调标记');
