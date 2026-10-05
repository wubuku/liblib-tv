/**
 * 第 5 项「死链扫描」的自检：证明这道门**会红**，而不是恒绿。
 *
 * 为什么必须做：门 5 的判据是 `dead.length === 0`。一段扫描器代码只要写错成
 * 「正则一个链接都匹配不到」，`total` 就是 `0`、`dead` 就是 `0`，门永远绿
 * —— 而这正是本项目反复出现的失败模式（批次 57 的节点位置比对恒真、
 * 批次 105 的判据恒真）。**宣布「零死链」之前，必须先证明扫描器抓得到坏链。**
 *
 * 做法：在手册目录里**临时**放一个只含坏链的探针文件，用与门 5 **逐字相同**的
 * 扫描逻辑跑一遍，要求它**报出**那条坏链；然后 `finally` 里删掉探针。
 * 探针放在手册目录内（扫描器只走这个目录），文件名以 `.` 开头且用 try/finally 保证删掉，
 * 绝不碰任何真实手册文件。
 *
 * 用法：node scripts/jimeng-deadlink-selfcheck.mjs
 */
import { readdirSync, statSync, readFileSync, writeFileSync, unlinkSync } from 'node:fs';
import { join, dirname, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const MANUAL = join(ROOT, 'docs/user-manual/jimeng-canvas');
const PROBE = join(MANUAL, '.deadlink-selfcheck-probe.md');
const BAD = './这个文件不存在-selfcheck-probe.md';

// ⚠️ 下面这段必须与 jimeng-final-gate.mjs 第 96–120 行**逐字同源**；
//    两边分叉就等于自检了一个门没跑的逻辑。
function scan(mdFiles) {
  const re = /!?\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;
  let total = 0; const dead = [];
  for (const f of mdFiles) {
    const txt = readFileSync(f, 'utf8');
    for (const m of txt.matchAll(re)) {
      const u = m[1].trim();
      if (/^(https?:|mailto:|#)/.test(u)) continue;
      total++;
      const target = normalize(join(dirname(f), u.split('#')[0]));
      if (u.split('#')[0] && !statSync(target, { throwIfNoEntry: false })) dead.push(`${f} -> ${u}`);
    }
  }
  return { total, dead };
}

const SKIP = new Set(['node_modules', 'dist', 'site', '.git', '.vitepress']);
const collect = () => {
  const md = [];
  (function walk(dir) {
    for (const e of readdirSync(dir)) {
      if (SKIP.has(e)) continue;
      const p = join(dir, e);
      if (statSync(p).isDirectory()) walk(p);
      else if (e.endsWith('.md')) md.push(p);
    }
  })(MANUAL);
  return md;
};

let ok = false;
try {
  writeFileSync(PROBE, `# 死链扫描器自检探针\n\n见 [坏链](${BAD})。\n`);
  const r = scan(collect());
  const caught = r.dead.some((d) => d.includes('这个文件不存在-selfcheck-probe.md'));
  ok = caught && r.total > 0;
  console.log(`自检：链接总数 ${r.total}，死链 ${r.dead.length}`);
  r.dead.forEach((d) => console.log('  抓到 ' + d));
  console.log(ok
    ? '✅ 扫描器会红：坏链被抓到了 ⇒ 门 5 的「零死链」是真的零'
    : '⛔ 扫描器抓不到自己注入的坏链 ⇒ 门 5 的绿是恒绿，不能采信');
} finally {
  try { unlinkSync(PROBE); console.log('探针已删除：', PROBE); } catch (e) { console.log('⚠️ 探针删除失败', e.message); }
}
process.exit(ok ? 0 : 1);