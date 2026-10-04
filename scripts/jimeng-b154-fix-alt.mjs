// 批次 154 —— 两处 alt 修复
//
// 🔴 修复 1（本批自己造成的）：`jimeng-b154-insert.mjs` 的 `取alt()` 用 python `print()` 取值，
//    **print 会多带一个换行** ⇒ 插进正文的 `![...]` 里多了一个 `\n`，
//    于是 3 张新图的正文 alt 比 manifest 多了 1 个字符。
//    📌 **自检两边都取自同一个 `取alt()`，所以它验自己、验不出这个错。**
//    ⇒ 立规：**自检的期望值不能与被检值来自同一次有副作用的调用**；
//    从外部程序取值一律用 `sys.stdout.write` 而不是 `print`。
//
// 🔴 修复 2（8 条历史遗留）：`57` / `65` / `99` / `100` / `101` / `102` / `71`×2 这 8 条的
//    alt 里带 markdown 强调标记 `**`。它们会**原样**进 `<img alt>`，
//    读屏软件会念出「星号星号」。🔑 之所以一直没人管：新门 `jimeng-manifest-gate.mjs`
//    第一次把这条查出来 —— **正因为它会红，才必须一次修干净**，
//    否则就是批次 66 说的「一道长期红的门等于没有门」。
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const DIR = 'docs/user-manual/jimeng-canvas';
const MAN = path.join(DIR, 'screenshots/manifest.yml');
const DUMP = path.join('scripts', '_tmp-b154-yamldump.py');
const 条目 = JSON.parse(execFileSync('python3', [DUMP, MAN], { encoding: 'utf8' }));

// ---------- 修复 1：把正文里 alt 内部的换行去掉 ----------
let md改动 = 0;
for (const it of 条目) {
  if (!it.file.endsWith('.png')) continue;
  const rel = '../' + it.file;
  for (const f of fs.readdirSync(path.join(DIR, '10-tasks'))) {
    const p = path.join(DIR, '10-tasks', f);
    if (!f.endsWith('.md')) continue;
    let s = fs.readFileSync(p, 'utf8');
    if (s.indexOf(rel) < 0) continue;
    const 坏 = '![' + it.alt + '\n](' + rel + ')';
    const 好 = '![' + it.alt + '](' + rel + ')';
    if (s.indexOf(坏) >= 0) { s = s.split(坏).join(好); fs.writeFileSync(p, s); md改动++; console.log('✅ 去掉 alt 内换行：' + it.file + ' @ 10-tasks/' + f); }
  }
}

// ---------- 修复 2：8 条 alt 里的 `**` ----------
const 有星 = 条目.filter((it) => /\*\*/.test(it.alt));
console.log('\nalt 含 `**` 的条目 =', 有星.length);
let man = fs.readFileSync(MAN, 'utf8');
const 记录 = [];
// 🔑 8 条里有 1 条（`71-subject-source-menu.png`）的 alt 是**单引号 YAML 标量**，
//    行锚必须同时覆盖「裸值」和「'…'」两种形态 —— 这正是本批刚修的那类引号问题。
const 行锚2 = (alt) => ['    alt: ' + alt + '\n', "    alt: '" + alt.replace(/'/g, "''") + "'\n"];
for (const it of 有星) {
  const 新alt = it.alt.replace(/\*\*/g, '');
  let 命中 = false;
  for (const a of 行锚2(it.alt)) {
    if (man.indexOf(a) >= 0) {
      man = man.replace(a, a.startsWith("    alt: '") ? "    alt: '" + 新alt.replace(/'/g, "''") + "'\n" : '    alt: ' + 新alt + '\n');
      命中 = true; break;
    }
  }
  if (!命中) { console.log('⛔ manifest 里找不到 alt 行（两种形态都没匹配上）：' + it.file); process.exit(1); }
  记录.push({ file: it.file, 旧: it.alt, 新: 新alt });
  console.log('  · ' + it.file + '  ' + JSON.stringify(it.alt.slice(0, 40)) + ' → ' + JSON.stringify(新alt.slice(0, 40)));
}
fs.writeFileSync(MAN, man);

// 正文侧同步（必须逐字等于新 alt）
let 正文改动 = 0;
for (const r of 记录) {
  const rel = '../' + r.file;
  for (const f of fs.readdirSync(path.join(DIR, '10-tasks'))) {
    const p = path.join(DIR, '10-tasks', f);
    if (!f.endsWith('.md')) continue;
    let s = fs.readFileSync(p, 'utf8');
    const 坏 = '![' + r.旧 + '](' + rel + ')';
    if (s.indexOf(坏) >= 0) { s = s.split(坏).join('![' + r.新 + '](' + rel + ')'); fs.writeFileSync(p, s); 正文改动++; console.log('  · 正文同步：10-tasks/' + f + ' ← ' + r.file); }
  }
}
console.log('\n正文改动 =', md改动 + 正文改动, '处');
