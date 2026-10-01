// 订正回填门（批次 75）：**已被推翻的结论，其原始记录处必须带内联订正标记**。
//
// 为什么需要这道门：这一类错已经犯了**三次**，而且每次都是同一形状 ——
//   批次 64：改了「标题取文件名」的结论，忘了改引用它的那一处括注；
//   批次 70：同一个文件里两个尺寸数字打架（281×281 vs canvas 320×320）；
//   批次 74：批次 71 推翻了「时间线源标题是添加上下文」，**正文与新章节都订正了，
//            唯独原始记录（§3.78.3 与 AUDIT 那一行）没留内联标记**。
// 手法上每次都是「改了结论 ≠ 引用它的地方也被改了」，而**没有任何机械检查会抓到它**。
//
// 判据（三条，缺一不可）：
//   ① 每条 entry 的 pattern 在全册必须**至少命中一处** —— 否则是幽灵条目 ⇒ 红（防橡皮图章）；
//   ② 每一处命中的**上下文 ±N 行内必须有订正标记**（~~删除线~~ / 已被推翻 / 订正 / 已关闭…）
//      —— 没有就是「改了结论没回填」⇒ 红；
//   ③ 命中所在行**本身**含标记也算通过（订正与原文写在一行里是允许的）。
//
// 用法：node scripts/jimeng-backfill-gate.mjs [--selftest]
import fs from 'node:fs';
import path from 'node:path';

const DIR = 'docs/user-manual/jimeng-canvas';
const CLAIMS = 'scripts/jimeng-refuted-claims.json';
const WINDOW = 3;                 // 命中的上下文窗口（行）

/**
 * 什么算「订正标记」：
 *   ① 行内/窗口内的删除线或明说已被推翻、订正、漏了、原写…的措辞；
 *   ② **所在小节本身就是订正记录**（标题含 推翻/订正/口径/机制/已被/新契约）——
 *      这一条很关键：像 §3.93「找到机制了」这种**专门记录订正过程**的小节，
 *      它当然会逐字复述被推翻的说法，若只按窗口判定就会把它误判成「没回填」。
 */
const MARKER = /~~|已被[^。\n]{0,8}推翻|已被批次|已被第|推翻|订正|已关闭|不成立|已删除|过时|作废|口径|实为|漏了|原写|排除|机制|改成|历史记录|原文不改写|原文保留/;
const SECTION_OK = /推翻|订正|口径|机制|已被|新契约|取证|复现/;

/** 该行所属小节的标题（向上找最近的 markdown 标题行） */
function headingOf(lines, i) {
  for (let j = i; j >= 0 && j > i - 400; j--) {
    if (/^#{1,6}\s/.test(lines[j])) return lines[j];
  }
  return '';
}

const walk = (d, out = []) => {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.md')) out.push(p);
  }
  return out;
};

function scan(claims) {
  const files = walk(DIR);
  const hits = [];
  for (const c of claims.entries) {
    for (const f of files) {
      const lines = fs.readFileSync(f, 'utf8').split('\n');
      for (const pat of c.patterns) {
        const re = new RegExp(pat);
        lines.forEach((L, i) => {
          if (!re.test(L)) return;
          const lo = Math.max(0, i - WINDOW), hi = Math.min(lines.length, i + WINDOW + 1);
          const ctx = lines.slice(lo, hi);
          const head = headingOf(lines, i);
          hits.push({
            id: c.id, label: c.label, file: path.relative(DIR, f), line: i + 1,
            text: L.trim(), section: head.trim().slice(0, 60),
            marked: ctx.some((x) => MARKER.test(x)) || SECTION_OK.test(head),
          });
        });
      }
    }
  }
  return { files: files.length, hits };
}

function check({ hits }, claims) {
  const unmarked = hits.filter((h) => !h.marked);
  const ghost = claims.entries.filter((c) => !hits.some((h) => h.id === c.id));
  return { ok: !unmarked.length && !ghost.length, unmarked, ghost, total: hits.length };
}

// ---------- 阳性对照：证明这道门真的会红 ----------
function selftest() {
  const claimsRaw = fs.readFileSync(CLAIMS, 'utf8');
  const claims = JSON.parse(claimsRaw);
  const victim = path.join(DIR, '10-tasks/_backfill-gate-selftest.md');
  // 夹具：放一条**已知被推翻**的措辞，且**故意不带任何订正标记**
  const bare = (id) => claims.entries.find((c) => c.id === id).patterns[0];
  // ⚠️ 夹具自身**绝不能含任何标记词**（否则门会判它「已标记」——
  //    第一版夹具里写了「故意不带订正标记」，「订正」二字本身就是标记词，用例 ① 因此翻车）。
  const markerFree = [
    '# 夹具页',
    '',
    `这一行含「${claims.entries[0].patterns[0].replace(/[()]/g, '')}」的字样。`,
  ].join('\n');
  const cleanup = () => { try { fs.unlinkSync(victim); } catch {} };

  if (fs.existsSync(victim)) { console.error('夹具已存在，先清理'); process.exit(9); }
  const baseScan = scan(claims);
  const base = check(baseScan, claims);
  const results = [];

  // 用例 1：植入无标记的已推翻措辞 ⇒ 必须 FAIL
  fs.writeFileSync(victim, markerFree);
  try {
    const r1 = check(scan(claims), claims);
    results.push(['① 出现「已推翻措辞但没有订正标记」→ 门必须红',
      !r1.ok && r1.unmarked.some((h) => h.file.endsWith('_backfill-gate-selftest.md'))]);
  } finally { fs.unlinkSync(victim); }

  // 用例 2：给同一行加上订正标记 ⇒ 必须转绿（证明门不是一律红）
  fs.writeFileSync(victim, markerFree + '\n（🔴 已被批次 75 推翻，原文保留）\n');
  try {
    const r2 = check(scan(claims), claims);
    results.push(['② 同一处补上订正标记 → 门必须绿',
      r2.ok && r2.unmarked.length === base.unmarked.length]);
  } finally { fs.unlinkSync(victim); }

  // 用例 3：entry 的 pattern 改成匹配不到任何东西 ⇒ 幽灵条目必须红（防橡皮图章）
  const ghosted = { ...claims, entries: [{ ...claims.entries[0], patterns: ['这句话在全册根本不存在-zzz'] }, ...claims.entries.slice(1)] };
  const r3 = check(scan(ghosted), ghosted);
  results.push(['③ 某条 entry 匹配不到任何命中（幽灵条目）→ 门必须红', !r3.ok && r3.ghost.length === 1]);

  // 用例 4：原样 ⇒ 必须绿
  const r4 = check(scan(claims), claims);
  results.push(['④ 未改动 ⇒ 门必须绿', r4.ok === base.ok]);

  console.log('订正回填门阳性对照自测：');
  let ok = base.ok;
  for (const [name, pass] of results) { console.log(`  ${pass ? '✅' : '🔴'} ${name}`); if (!pass) ok = false; }
  cleanup();
  const after = check(scan(claims), claims);
  console.log(`  自测后复跑：${after.ok === base.ok ? '✅ 与自测前一致（未留痕）' : '🔴 被自测污染'}`);
  console.log(ok && after.ok === base.ok ? '✅ 自测通过：这道门两个方向都会红' : '❌ 自测不通过 —— 门不可信');
  return ok && after.ok === base.ok;
}

const claims = JSON.parse(fs.readFileSync(CLAIMS, 'utf8'));
if (process.argv.includes('--selftest')) process.exit(selftest() ? 0 : 1);

const s = scan(claims);
const r = check(s, claims);
console.log(`扫描 ${s.files} 个 Markdown × ${claims.entries.length} 条已被推翻的结论 → 命中 ${s.hits.length} 处`);

if (r.unmarked.length) {
  console.log(`\n⛔ ${r.unmarked.length} 处**改了结论却没回填订正标记**（读者只翻台账就会读到旧结论）：`);
  for (const h of r.unmarked) console.log(`  [${h.id}] ${h.label}\n      ${h.file}:${h.line}  ${h.text.slice(0, 110)}`);
}
if (r.ghost.length) {
  console.log(`\n⛔ ${r.ghost.length} 条 entry 匹配不到任何命中（幽灵条目，防橡皮图章）：`);
  for (const c of r.ghost) console.log(`  [${c.id}] ${c.label}`);
}
if (r.ok) {
  console.log(`\n✅ 订正回填门通过：${s.hits.length} 处命中全部带内联订正标记，${claims.entries.length} 条 entry 均对得上真实命中`);
} else {
  console.log('\n🔴 订正回填门不通过 —— 退出码 1');
  process.exit(1);
}
