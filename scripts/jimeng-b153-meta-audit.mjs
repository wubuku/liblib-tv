import fs from 'node:fs';
import path from 'node:path';
const DIR = 'docs/user-manual/jimeng-canvas';
const 页 = [];
// 🔴 批次 153 修法：只扫**手册正文**（`10-tasks/` + 顶层 .md），
//    **排除 `node_modules/` 与 `screenshots/`** —— 第一版把这两处的几百个 README/LICENSE
//    也算了进来，「全册最大批次 = 218」就是被它们污染出来的。
const 跳过目录 = new Set(['screenshots', 'node_modules', '.git']);
(function walk(d, 顶层) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    if (跳过目录.has(e.name)) continue;
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p, false);
    else if (e.name.endsWith('.md') && !/^(SOURCE_OBSERVATIONS|AUDIT|PROGRESS)/.test(e.name) && (顶层 || d.endsWith('10-tasks'))) 页.push(p);
  }
})(DIR, true);
if (!页.length) { console.error('🔴 没扫到任何页面，walk 条件写错了'); process.exit(1); }
const 行 = 页.map((p) => {
  const t = fs.readFileSync(p, 'utf8');
  // ⚠️ 只认**本项目**的批次号（1..400 且出现在「批次 N」形式下）。
  //    手册里也会引用别的项目的批次号，一律排除，否则「最大批次」会被污染。
  const 批次 = [...t.matchAll(/(?<!源站 )(?<!原引自源站采样 )批次\s*(\d{1,3})(?!\d)/g)].map((m) => Number(m[1]));
  const 批 = [...t.matchAll(/(?<!采样 )batch\s*(\d{1,3})(?!\d)/g)].map((m) => Number(m[1]));
  // ⚠️ `media-playback.md` 里有一句「此条原引自**源站采样** batch 218」——
  //    那是**别的项目**的批次号。第一版没排除它，导致该页被误判成「最新鲜」（差距 0）。
  //    这类引用一律剔除，否则陈旧度排序会骗人。
  const all = [...批次, ...批].filter((x) => x > 0 && x <= 400);
  return {
    页: path.basename(p),
    路径: p,
    行数: t.split('\n').length,
    最大批次: all.length ? Math.max(...all) : 0,
    批次出现次数: all.length,
    待查标记: (t.match(/待查|未决|待确认|TODO|尚未/g) || []).length,
    存疑标记: (t.match(/存疑|疑似|不明|没解释|不下机制断言/g) || []).length,
    截图: (t.match(/!\[/g) || []).length,
  };
});
// 「陈旧度」= 与全册最大批次的差距；并列时待查多的排前
const 全册最大 = Math.max(...行.map((x) => x.最大批次));
console.log('全册最大批次 =', 全册最大, '| 页面数 =', 行.length);
console.log('\n排名（陈旧度 = 全册最大批次 − 该页最大批次）');
行.sort((a, b) => (b.全册最大 - b.最大批次) - (a.全册最大 - a.最大批次) || b.待查标记 - a.待查标记);
console.log('名次  差距  最大批次  行数  待查  存疑  截图  页面');
行.forEach((x, i) => console.log(
  String(i + 1).padEnd(5) + String(全册最大 - x.最大批次).padEnd(6) + String(x.最大批次).padEnd(9) +
  String(x.行数).padEnd(6) + String(x.待查标记).padEnd(6) + String(x.存疑标记).padEnd(6) + String(x.截图).padEnd(6) + x.页));
console.log('\n=== 候选 A：差距 ≥ 40 且待查标记 ≥ 1 ===');
行.filter((x) => 全册最大 - x.最大批次 >= 40 && x.待查标记 >= 1).forEach((x) => console.log('  ' + x.页 + '（差距 ' + (全册最大 - x.最大批次) + '，待查 ' + x.待查标记 + ' 处）'));
console.log('=== 候选 B：差距 ≥ 40（不管待查） ===');
行.filter((x) => 全册最大 - x.最大批次 >= 40).forEach((x) => console.log('  ' + x.页));
console.log('=== 候选 C：待查标记最多的 6 个（不分陈旧度） ===');
[...行].sort((a, b) => b.待查标记 - a.待查标记).slice(0, 6).forEach((x) => console.log('  ' + x.页 + ' 待查 ' + x.待查标记 + ' / 最大批次 ' + x.最大批次));
