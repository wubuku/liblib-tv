// 批次 90 · A：审计 `90-troubleshooting.md`（普查停在 **78**）。
//
// 排障页的特殊性：它的每一条都建立在「**这样就能确认你处在这个问题里**」之上。
// 所以这一页最该挨的审不是「数字对不对」，而是两个更结构性的问题：
//
// 🔍 **判据一（机械、可穷举）**：这页有没有把**已被推翻的结论**当成诊断依据？
//     `jimeng-refuted-claims.json` 现在有 **32 条**已被推翻的结论。
//     逐条 pattern 扫这一页，命中的地方如果**没有订正标记**，
//     读者照着它排障就会得到一个已被证伪的原因。
//     ⇒ 这是本页与回填门同一套机制，但**只针对这一页**。
//
// 🔍 **判据二（机械、可计数）**：每条排障建议**能不能被机械验证**？
//     「怎么确认你处在这个问题里」如果只写成「看起来像坏了」，
//     读者无法自查；如果写了 `data-testid` / `[aria-label=…]` / 逐字文案，
//     读者（和后续批次）可以复跑。
//     ⇒ 逐节统计：**含可机械核对的定位器** vs **不含**。
//
// 输出只报告，不下结论 —— 结论要等 B 轮上真画布验。
import fs from 'node:fs';
import path from 'node:path';

const DIR = 'docs/user-manual/jimeng-canvas';
const TARGET = '90-troubleshooting.md';
const WINDOW = 3;
const MARKER = /~~|已被[^。\n]{0,8}推翻|已被批次|已被第|推翻|订正|已关闭|不成立|已改为|已删除|过时|作废|口径|实为|漏了|原写|排除|机制|改成|历史记录|原文不改写|原文保留/;
const SECTION_OK = /推翻|订正|口径|机制|已被|新契约|取证|复现|回填/;
const claims = JSON.parse(fs.readFileSync('scripts/jimeng-refuted-claims.json', 'utf8'));
const file = path.join(DIR, TARGET);
const lines = fs.readFileSync(file, 'utf8').split('\n');

// ── 判据一：已被推翻的结论 ──
function headingChain(i) { const o = []; for (let j = i; j >= 0 && j > i - 400 && o.length < 3; j--) if (/^#{1,6}\s/.test(lines[j])) o.push(lines[j]); return o; }
console.log(`══ 判据一：${TARGET} 里逐条扫 ${claims.entries.length} 条已被推翻的结论`);
let hits = 0, unmarked = 0;
for (const c of claims.entries) for (const pat of c.patterns) {
  const re = new RegExp(pat);
  lines.forEach((L, i) => {
    if (!re.test(L)) return;
    hits++;
    const ctx = lines.slice(Math.max(0, i - WINDOW), Math.min(lines.length, i + WINDOW + 1));
    const heads = headingChain(i);
    const ok = ctx.some((x) => MARKER.test(x)) || heads.some((h) => SECTION_OK.test(h));
    if (!ok) unmarked++;
    console.log(`  ${ok ? '✅' : '🔴'} [${c.id}] ${TARGET}:${i + 1}  ${L.trim().slice(0, 92)}`);
  });
}
console.log(`  ⇒ 命中 ${hits} 处，其中未带订正标记 ${unmarked} 处\n`);

// ── 判据二：每条建议的判据能否机械验证 ──
console.log('══ 判据二：逐节统计「怎么确认你处在这个问题里」是否可机械核对');
const secs = [];
let cur = null;
// ⚠️ `##` 是**分类标题**（「画布操作」「媒体」…），不是排障条目 ——
//    混进统计会把「这一节没有判据」算成 6 条假的缺口。分开放。
const heads2 = [];
lines.forEach((L, i) => {
  if (/^##\s/.test(L)) { cur = null; heads2.push({ line: i + 1, title: L.replace(/^#+\s*/, '').trim() }); }
  else if (/^###\s/.test(L)) { cur = { line: i + 1, title: L.replace(/^#+\s*/, '').trim(), body: [] }; secs.push(cur); }
  else if (cur) cur.body.push(L);
});
console.log(`  （另有 ${heads2.length} 个 \`##\` 分类标题，不计入条目统计）`);
// ⚠️ **只报一档是不诚实的** —— 「含 testid」是最高的可复跑档，
//    但很多节其实**给了逐字 UI 文案或具体数字**，读者照样能自查，机器也能复跑。
// ⇒ 分三档报，别把「没有 testid」说成「无法自查」。
const T1 = /data-testid|aria-label|\[aria|\[data-|role="|逐字|class="|getAttribute|querySelector/;   // 定位器
const T2 = /「[^」]{2,}」|「[^」]+」|`[^`]{2,}`|[0-9]+×[0-9]+|[0-9]+ 个|[0-9]+ px/;                    // 逐字文案 / 数字契约
const t1 = [], t2only = [], t3 = [];
for (const s of secs) {
  const t = s.body.join('\n');
  (T1.test(t) ? t1 : T2.test(t) ? t2only : t3).push(s);
}
console.log(`  共 ${secs.length} 节`);
console.log(`  A 档（有 testid / aria / class 定位器，机器可直接复跑）：${t1.length}`);
console.log(`  B 档（有逐字文案或数字契约，人能自查、机器需转写）：${t2only.length}`);
console.log(`  C 档（两者都无，只剩自然语言描述）：${t3.length}`);
console.log('  ── C 档（读者无法自查，机器也无法复跑）：');
for (const s of t3) console.log(`     ${TARGET}:${s.line}  ${s.title.slice(0, 66)}`);

// ── 附加：每节是否有「实测/已验证」出处 ──
console.log('\n══ 附加：每节是否注明证据出处（实测日期 / 批次号）');
const PROV = /实测|已验证|2026-\d\d-\d\d|批次/;
const noProv = secs.filter((s) => !PROV.test(s.body.join('\n')));
console.log(`  无出处的 ${noProv.length} 节：`);
for (const s of noProv) console.log(`     ${TARGET}:${s.line}  ${s.title.slice(0, 66)}`);
