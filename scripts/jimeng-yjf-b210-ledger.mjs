// 会话 mvs_fb62b78 · 批次 210：往订正台账追加 2 条。
//
// 纪律（批次 158 立下的）：
//   ① 改台账前先证明**原文件逐字等于 `JSON.stringify(j,null,1)+'\n'`** ——
//      否则 `git diff` 里会混进整文件重排，后面谁也审不动；
//   ② 改完**逐条比对前 N 条没变**，证明我只追加、没顺手重写别人的条目。
import fs from 'node:fs';

const P = 'scripts/jimeng-refuted-claims.json';
const raw = fs.readFileSync(P, 'utf8');
const j = JSON.parse(raw);

// ① 格式证明
const 规范 = JSON.stringify(j, null, 1) + '\n';
if (raw !== 规范) {
  console.error('⛔ 原文件不是 JSON.stringify(j,null,1)+\'\\n\' 的逐字形态 —— 拒绝改写');
  process.exit(1);
}
const 前 = JSON.stringify(j.entries);
const 前条数 = j.entries.length;
console.log(`✅ 格式逐字吻合（${raw.length} 字符，${前条数} 条）`);

j.entries.push({
  id: 'initial-translate-not-recomputed',
  label: '「视口宽度根本不改变画布初始平移」被批次 210 推翻：它只在「同一页签只 resize」时成立；新开页加载时初始 tx 随宽度走',
  patterns: ['视口宽度根本不改变画布初始平移'],
  pattern_note: 'pattern 取自 `10-tasks/navigate-canvas.md` 里批次 199 那句结论的原话（去掉了包裹它的 `**`）。全册命中 1 处，且**命中行本身**已带内联订正标记「🔴 **已被批次 210 推翻**」⇒ 满足回填门。串里没有 `* + ? [ ] { } | ^ $ \\ .` 任何 regex 元字符。',
  refuted_in: '批次 210（10-tasks/navigate-canvas.md 批次 199 那句结论内联订正 + 新增「批次 210」块第 ③ 条；SOURCE_OBSERVATIONS.md §4.97；30-concepts 新增立规 88）',
  reason: '批次 199 在一个新页签里把宽度从 1000 扫到 1600 共 12 档，读 `.react-flow__viewport` 的初始 transform，12 档**逐字相同**（`translate(97.1509px, -30.4641px) scale(0.260267)`），于是写下「⇒ 视口宽度根本不改变画布初始平移」，并据此排除「初始平移随宽度变」这条路径。🔴 批次 210 每档**新开页加载**后读同一个量，9 档 `tx` 逐字命中 **`tx = 视口宽/2 − 542.8491`**（`1200→57.1509` / `1210→62.1509` / `1215→64.6509` / `1220→67.1509` / `1225→69.6509` / `1230→72.1509` / `1240→77.1509` / `1260→87.1509` / `1280→97.1509`，9/9 命中）⇒ **初始平移确实随宽度变**。📌 批次 199 那 12 档之所以逐字相同，是因为它**只 resize、不重算**：页面加载时算出的初始平移不会因为窗口变宽变窄而重算（机制：复用页 resize 后取景落点与初始平移都带着上一状态的残值，见本批另一条 `reused-tab-carryover-invalidates-absolute-constant`）。⇒ 这正是立规 79 的一个**正向反例**：批次 199 的否证在**它自己测的量与它自己用的方法**上完全正确，结论却不可用 —— 因为「12 档相同」测的是「resize 不触发重算」，不是「宽度不影响平移」。📌 订正后两条并存且互不矛盾：**初始平移随宽度变**（新开页加载时的量）与批次 200/210 说的**取景后 ty 分支**（取景后的量）是两个不同的量，b 轮分别读过。',
});

j.entries.push({
  id: 'reused-tab-carryover-invalidates-absolute-constant',
  label: '批次 210 自己 a 轮的「C = −519.435」作废：复用同一个页签只 resize，取景落点会带着上一档残值',
  patterns: ['519.435'],
  pattern_note: 'pattern 取批次 210 a 轮那个被否掉的常数（去掉了前面的 Unicode 减号 U+2212，只留数字部分，避免同类字符写法不一致导致漏匹配）。命中处**下方 2 行**即有订正标记词「机制」⇒ 满足回填门「命中行 ±3 行内含订正标记」。',
  refuted_in: '批次 210 同批 b/c 轮（10-tasks/navigate-canvas.md 批次 210 块第 ④ 条；SOURCE_OBSERVATIONS.md §4.97；30-concepts 新增立规 88）',
  reason: '批次 210 a 轮用**一个页签复用 + `setViewportSize`** 扫 11 档宽度（1190~1290），在 `1230` 及以上各档都读到 `ty = −156.555`，据此写下 `C = −519.435`，与批次 200 的 `−508` 差约 11。🔴 同批 b 轮**只打开「复用页 vs 新开页」这一个变量**就否掉了它：`1200` 两条件**逐字相同**（`−44.5555`），而 `1280` 复用页给 `−156.555`、新开页给 `−144.773`（差 `11.782`）；批次 200 的 `−145.169` 与批次 198 的 `−144.596` 都落在新开页那一族 ⇒ **批次 200 的 `C ≈ −508` 是对的，a 轮的 `−519.435` 是 carryover 污染**。📌 机制：复用页 resize 之后**取景落点不会立刻按新宽度重算**，会带着上一档的残值 —— b 轮复用页@`1280` 的 6 帧里**同时出现** `−44.5556` 与 `−156.555` 两个值（前者正是上一档 `1200` 的落点）。c 轮改成每档新开页后，`1280` 三次独立读数 `−144.773 / −144.836 / −144.734`（臂间极差 `0.103`），与批次 200 的 `−508` 同族。⇒ 立规 88：**读绝对常数时每档都要换一个干净状态；一页复用只适合读相对关系**。📌 这条同时解释了批次 199 那次「12 档逐字相同」—— 同一个「复用太多」的病根，换了个地方发作。',
});

// ② 证明只追加
const out = JSON.stringify(j, null, 1) + '\n';
const 前条 = JSON.parse(前);
const 后条 = j.entries.slice(0, 前条数);
if (JSON.stringify(前条) !== JSON.stringify(后条)) {
  console.error('⛔ 前 ' + 前条数 + ' 条被改动了 —— 拒绝写出');
  process.exit(1);
}
console.log(`✅ 前 ${前条数} 条逐条未变`);
fs.writeFileSync(P, out);
console.log(`✅ 已追加 ${j.entries.length - 前条数} 条 → 共 ${j.entries.length} 条`);
console.log('新增 id：', j.entries.slice(前条数).map((e) => e.id).join(', '));
