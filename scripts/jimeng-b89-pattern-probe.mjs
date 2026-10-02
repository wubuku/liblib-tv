// 批次 89 探针：为 `jimeng-refuted-claims.json` 挑 pattern 时，先看每个候选串在全册
// 命中几处、每处是否已被订正标记覆盖。
//
// 为什么要有这道探针：那份清单的判据是「每条 pattern 的**每一处**命中，其上下文 ±3 行
// 内必须有订正标记」。也就是说 **pattern 越宽越危险** —— 像 `32px`、`192×40` 这种
// 到处都在写的数字，一旦当 pattern，会在几十处无害引用上判红。
// 「已被推翻」是要精确的：**逐字复述原结论、且那一处才是真被推翻的**才配当 pattern。
//
// 用法：node scripts/jimeng-b89-pattern-probe.mjs '候选正则' ['另一个' ...]
import fs from 'node:fs';
import path from 'node:path';

const DIR = 'docs/user-manual/jimeng-canvas';
const WINDOW = 3;
const MARKER = /~~|已被[^。\n]{0,8}推翻|已被批次|已被第|推翻|订正|已关闭|不成立|已改为|已删除|过时|作废|口径|实为|漏了|原写|排除|机制|改成|历史记录|原文不改写|原文保留/;
const SECTION_OK = /推翻|订正|口径|机制|已被|新契约|取证|复现|回填/;

const walk = (d, out = []) => {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.md')) out.push(p);
  }
  return out;
};

function headingChain(lines, i) {
  const out = [];
  for (let j = i; j >= 0 && j > i - 400 && out.length < 3; j--) {
    if (/^#{1,6}\s/.test(lines[j])) out.push(lines[j]);
  }
  return out;
}

const files = walk(DIR);
for (const pat of process.argv.slice(2)) {
  const re = new RegExp(pat);
  let total = 0, ok = 0;
  const bad = [];
  const good = [];
  for (const f of files) {
    const lines = fs.readFileSync(f, 'utf8').split('\n');
    lines.forEach((L, i) => {
      if (!re.test(L)) return;
      total++;
      const lo = Math.max(0, i - WINDOW), hi = Math.min(lines.length, i + WINDOW + 1);
      const heads = headingChain(lines, i);
      const marked = lines.slice(lo, hi).some((x) => MARKER.test(x)) || heads.some((h) => SECTION_OK.test(h));
      const rec = { where: `${path.relative(DIR, f)}:${i + 1}`, text: L.trim().slice(0, 96), head: (heads[0] || '').trim().slice(0, 46) };
      if (marked) { ok++; good.push(rec); } else { bad.push(rec); }
    });
  }
  console.log(`\n══ /${pat}/ → 命中 ${total} 处，已标记 ${ok}，未标记 ${bad.length}`);
  for (const r of bad.slice(0, 12)) console.log(`  🔴 [${r.where}] ${r.text}\n       ↑ 节: ${r.head}`);
  if (bad.length > 12) console.log(`  …另有 ${bad.length - 12} 处未标记`);
  if (!bad.length) for (const r of good.slice(0, 4)) console.log(`  ✅ [${r.where}] ${r.text}`);
}
