// 即梦画布手册 · 截图 alt 一致性审计
// 即梦画布手册 · 截图 alt 一致性审计（长期资产）
// 目的：截图的 alt 既是无障碍描述，也是「这张图证明了什么」的证据声明。
// 批次 15 修订了工具条事实后，存量 alt 可能仍在描述旧结论。本脚本逐张核对：
//   1) manifest 登记的 alt 与正文引用处是否逐字一致（构建器对一字之差即报 warn）
//   2) 是否有截图登记了却没被任何正文引用
//   3) alt 文案里是否残留与当前实测结论冲突的措辞
//
// 🔴 批次 154 修掉一个**假阳性源**：原来这里用 `y.split(/\n  - file: /)` 正则切块、
//    再用 `/^\s+alt: (.+)$/m` 取值，于是**单引号 YAML 标量的那对引号被当成了 alt 的一部分** ——
//    3 条带引号的条目（`subject-node.png` / `33-subject-imported.png` / `71-subject-source-menu.png`）
//    被判成「alt 不一致」，而真解析出来它们与正文**逐字相同**。
//    📌 与批次 154 修的 manifest 语法烂掉是**同一个根因**：**用正则代替解析器**。
//    ⇒ 现在改走真 YAML 解析（`jimeng_yaml_dump.py`），两道门对同一份数据给同一个答案。
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const DIR = 'docs/user-manual/jimeng-canvas';
const MAN = path.join(DIR, 'screenshots/manifest.yml');
const 条目 = JSON.parse(execFileSync('python3', [path.join('scripts', 'jimeng_yaml_dump.py'), MAN], { encoding: 'utf8' }));
const blocks = 条目.map((it) => ({ file: it.file, alt: it.alt }));

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
  const file = b.file;
  const abs = path.resolve(DIR, file);
  const refs = altByPath.get(abs) || [];
  const mAlt = b.alt;
  if (!refs.length) {
    unreferenced++;
    // 🔴 批次 168 新增的**自解释分支**：这个失败几乎总是「alt 里出现了 `]`」造成的 ——
    //   `/!\[([^\]]*)\]\(([^)]+)\)/` 撞上 alt 内第一个 `]` 就截断，于是整张图读不到。
    //   而正文里**无从看出**这个原因（正文确实有引用）⇒ 门只报「未被正文引用」会把人带偏。
    //   ⇒ 这里直接把最可能的原因写出来，并说明修法。
    const 疑因 = mAlt && mAlt.includes(']')
      ? '⚠️ 它的 alt 里含有 `]`（例如逐字引用类名 top-[60px]）⇒ **alt 里的 `]` 会截断 `![...](...)` 的匹配**；修法：alt 里避开方括号，或写成 `\\]`'
      : '（alt 里没有 `]`，那就是正文里确实没有引用）';
    issues.push(`未被正文引用  ${file}\n    ↳ ${疑因}`);
    continue;
  }
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
// 第三项可选：出现该子串时视为「已声明这是订正结论」，不报冲突
//
// 🔴 2026-10-01 批次 58 订正：这里曾有三条规则断言
//    「实测组工具条**仅三项，无下载**」—— 那是**批次 50 已经推翻的结论**。
//    批次 50 用控制变量（只改组内有无媒体节点）+ 复核两张旧截图证明
//    **组工具条恒为四项**（解除编组 / 布局 / 背景色 / **下载**），
//    与组内成分、与缩放都无关；唯一条件是「组里有没有成员」。
//    ⇒ 照着**正确**结论写下的 alt 反被这道审计判成「冲突」（实测命中 4 处）——
//       **审计自己停在了被推翻的信念上**，而因为它恒真，这 4 处从来没变成红灯。
//    现在改成反向规则：只报「把下载漏掉、写成三项」的 alt。
const SUBSTR_RULES = [
  ['不弹工具条', 'alt 写「不弹工具条」；实测空节点仍用 node-toolbar 容器（680×208）改放生成面板'],
  ['1 nodes', 'alt 用了复数 1 nodes；实测状态行为单数 1 node'],
  ['Add tags（图标）', 'alt 把 Add tags 写成工具条项；实测它是节点自身的 flow-node-selected-tag 按钮'],
  ['Add tags', 'alt 把 Add tags 写进工具条；实测多选工具条无此项（它是节点自身的标记按钮）', '没有 Add tags'],
];
console.log('\n=== alt 措辞与当前实测结论的冲突扫描 ===');
let hit = 0;
for (const b of blocks) {
  const file = b.file;
  const a = b.alt || '';
  for (const [needle, why, allow] of SUBSTR_RULES) {
    if (!a.includes(needle)) continue;
    if (allow && a.includes(allow)) continue;
    console.log(`  ${file}\n    ${why}\n    alt: ${a.slice(0, 120)}`); hit++;
  }
  // 反向规则：组工具条**少了「下载」**才是冲突（批次 50 后的正确结论是恒为四项）。
  // 标了「旧版本截图」的放行 —— 那类 alt 如实描述的是**历史画面**，
  // 不是对当前行为的断言（实测 `51-group-background-palette.png` 就是这种：
  // 画面里确实只有三项，缩放 74%、顶栏「节点 3」，都早于下载按钮出现）。
  if (a.includes('解除编组') && a.includes('背景色') && !a.includes('下载') && !a.includes('旧版本截图')) {
    console.log(`  ${file}\n    alt 把组工具条写成三项、漏了「下载」；2026-10-01 批次 50 控制变量实测**恒为四项**`
      + `（解除编组 / 布局 / 背景色 / 下载），与组内成分、与缩放都无关\n    alt: ${a.slice(0, 120)}`);
    hit++;
  }
}
console.log(hit === 0 ? '  无冲突' : `  命中 ${hit} 处`);

// 🔴 2026-10-01 批次 58：本脚本此前**只打印、从不设置非零退出码** ——
//    于是收尾门第 1 道「截图 alt 审计」是一道**恒真**的门：
//    alt 对不上、措辞冲突，它照样打 ✅，收尾门照样 8/8、退出码 0。
//    由 `jimeng-gate-selftest.mjs` 的阳性对照抓出：故意把正文一处 alt 改一个字，
//    期望第 1 道变红，实测仍然 ✅、收尾门退出码 0。
//    🔑 一道从不失败的检查等于没有这道检查 —— 而「8/8 通过」这句话本身也要被证明。
const problems = altMismatch + unreferenced + hit;
if (problems) {
  console.log(`\n⛔ 发现 ${problems} 个问题：alt 不一致 ${altMismatch}、未被引用 ${unreferenced}、措辞冲突 ${hit} —— 退出码 1`);
  process.exit(1);
}
console.log('\n✅ alt 逐字一致、全部被引用、无措辞冲突 —— 退出码 0');
