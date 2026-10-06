// 即梦画布手册 · **收尾质量门自身的阳性对照自测**
//
// 🔴 为什么需要它（2026-10-01 批次 57 的来历）：
//   批次 57 发现第 8 道门的「位置比对」**恒真** —— 传错基线形状，
//   `Math.abs(x - undefined)` = `NaN`，而 `NaN > tol` 恒为 false，
//   于是「节点位置偏离 0 个」**无论节点偏了多少都照打**。
//   批次 48 正是靠这道门抓到过位置事故 —— 事故修好了，
//   **检查项本身却从此再也没被验证过**。
//
//   🔑 一道「从不失败」的检查 = 没有这道检查。
//      而「8/8 通过」这句话本身也需要被证明，而不只是被打印出来。
//
// 🔴🔴 **批次 250 修掉的这道自测自身的一个致命缺陷**（它一直是空转的）：
//   用例的判据写成了 `out.includes('❌ 3/9')` 这种**绑在门序号上**的形式，
//   而收尾门**早就从 9 项长到了 11 项**、打印的是 `❌ 3/11`
//   ⇒ **每个用例的 `expect()` 永远匹配不上** ⇒ `broken` 恒等于用例数
//   ⇒ 脚本最后 `process.exit(broken ? 3 : 0)`，**实际一直退出 3**，
//   可是**没人看退出码**（批次 249 我自己还把管道里 `tail` 的 `0` 当成了它的退出码，记进了手册）。
//   ⇒ 🔴 **教训：判据绑在「会变的编号」上，等于判据不存在。**
//   本版改为**按门的标签文字匹配**（`截图 alt 审计`、`死链扫描`…），
//   标签来自门自己的输出 ⇒ **门增删或改序号都不会再让这道自测失效。**
//
// 本脚本做什么：
//   对每一道**断言型**门，**故意注入一个缺陷**，跑整条收尾门，
//   **断言对应的那道门变成 ❌**，然后**逐字节还原**注入的文件。
//   任何一道门在注入缺陷后仍然 ✅，就说明它是恒真的 —— 退出码 3。
//
// 🔴 还原纪律：**用注入前读到的字节写回**，不用 `git checkout --` / `stash` ——
//   那两个在本仓库被明令禁用（会干扰其他开发者的暂存区）。
//   每次还原后都断言 `git diff --quiet HEAD -- <file>`，字节对不上就报错退出。
//   ⚠️ 批次 249 实测：还原失败时它**只报错、继续往下跑**，
//   于是把夹具留在正文里污染了工作区（本批当时手工清掉的）。
//   ⇒ 本版把 `还原失败` 升级成**立即中止**（`process.exit(4)`），
//   **宁可停在半路，也绝不留残局**。
//
// 注入目标：
//   默认 `10-tasks/connect-nodes.md`（本任务自有、已提交、对 HEAD 干净）；
//   个别用例可自带 `target`（例如往脚本里注入乱码，验批次 249 刚扩的那道覆盖面）。
//
// 用法：
//   node scripts/jimeng-gate-selftest.mjs            # 全量（跑 6 次整条门，约 4–6 分钟）
//   node scripts/jimeng-gate-selftest.mjs --list     # 只列出用例，不执行
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');
const TARGET = 'docs/user-manual/jimeng-canvas/10-tasks/connect-nodes.md';
const LIST_ONLY = process.argv.includes('--list');

const sha = (s) => createHash('sha256').update(s).digest('hex');

/**
 * 🔴 **按规则挑一个注入位置**，而不是手工挑一个「能过」的位置（批次 250 第三次修）。
 *
 * 背景：这个用例要把一条**不带订正标记**的已被推翻措辞塞进正文，期望回填门变红。
 * 第一版把它**追加到文件末尾** —— 结果门是绿的。查下去发现**两件事叠在一起**：
 *   ① 早期版本的回填门有一条「所在小节标题含『机制』等词 ⇒ 整节免检」的后门（已删，见那扇门）；
 *   ② 但**即使删掉后门**、窗口放宽到 ±40 行，末尾仍然绿 ——
 *      因为第 1042 行就有一个 `⚠️ **由此订正本页第 97 行**`，距注入点只有 25 行
 *      ⇒ **门判「已标记」是完全正确的**：那个邻域里确实有订正。
 * ⇒ 📌 **结论：阳性对照必须放在一个「附近确实没有订正」的邻域里，否则它测不出任何东西**
 *      —— 这是**用例设计**的问题，不是门的问题。
 *
 * 挑法（确定性，可复核）：取**第一个**满足两条的位置 ——
 *   ① 以它为中心的 `±40` 行窗口里**一个标记词都没有**（用与回填门同一套正则，避免两套标准）；
 *   ② 该行本身是**空行** ⇒ 插进去的是一个独立段落，不会插进表格中间或标题中间把结构搞坏。
 */
const MARKER_SAME_AS_GATE = /~~|已被[^。\n]{0,8}推翻|已被批次|已被第|推翻|订正|已关闭|不成立|已改为|已删除|过时|作废|口径|实为|漏了|原写|排除|机制|改成|历史记录|原文不改写|原文保留/;
const BACKFILL_WINDOW = 40;          // 必须与 scripts/jimeng-backfill-gate.mjs 的 WINDOW 一致
const 插入到无订正邻域 = (t, 文本) => {
  const lines = t.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() !== '') continue;
    const ctx = lines.slice(Math.max(0, i - BACKFILL_WINDOW), i + BACKFILL_WINDOW + 1);
    if (ctx.some((x) => MARKER_SAME_AS_GATE.test(x))) continue;
    return [...lines.slice(0, i + 1), '', 文本, '', ...lines.slice(i + 1)].join('\n');
  }
  throw new Error(`整个文件里找不到「±${BACKFILL_WINDOW} 行内无订正标记」的空行 —— 用例无法构造`);
};

/**
 * 🔴🔴 **`mustMention`：断言「门红的原因必须是这个文件」，而不只是「某道门红了」**（批次 250）。
 *
 * 为什么必须加这一条：批次 250 的 `ufffd-in-script` 用例第一版**注入时漏掉了那个字符本身**，
 * 而运行当时收尾门**因为另一条陈旧白名单而本来就是红的**
 * ⇒ 门红了、断言通过、**用例显示 ✅ —— 但它是被一个无关的失败顶过的**，
 * 「注入 → 门红」这条链**一次都没被验证**。
 * ⚠️ **一个靠别人的失败而通过的用例，比没有用例更坏**：
 * 它会让人以为「这道门能抓到脚本里的乱码」，而实际上从来没验证过。
 * ⇒ 判据从「某道门是 ❌」收紧成「**那道门是 ❌，且它的明细里点名了这个文件**」。
 */
/** 从门输出里抽出每一道的判定：`[{序号, 标签, 红}]` —— 序号只用来显示，判据不看它 */
const parseGates = (out) => {
  const rs = [];
  for (const m of out.matchAll(/^([✅❌])\s+(\d+\/\d+)\s+(.+)$/gm)) {
    rs.push({ 红: m[1] === '❌', 序号: m[2], 标签: m[3].trim() });
  }
  return rs;
};

// ---- 缺陷用例：每个都只改**一个**文件；`gates` 写的是**标签**，不是序号 ----
const CASES = [
  {
    id: 'alt-mismatch',
    gates: ['截图 alt 审计'],
    why: '把正文里 99 号截图的 alt 改一个字，与 manifest.yml 登记的 alt 不再逐字一致',
    expect: (gs) => gs.find((g) => g.标签.includes('截图 alt 审计'))?.红 === true,
    inject: (t) => t.replace('文本节点是 7 种类型里唯一不与卡片顶边齐平的', '文本节点是 7 种类型里唯一不与卡片顶边齐平'),
  },
  {
    id: 'dead-link',
    gates: ['gate-a', 'final', '死链扫描'],
    why: '插一条指向不存在文件的死链（批次 57 真实发生过一次，属实的意外阳性对照）',
    expect: (gs) => ['gate-a', 'final', '死链扫描'].every((k) => gs.find((g) => g.标签.includes(k))?.红 === true),
    inject: (t) => `${t}\n\n<!-- 门自测注入 -->\n[指向不存在](__gate_selftest_no_such__.md)\n`,
  },
  {
    id: 'ufffd-in-md',
    gates: ['乱码扫描'],
    why: '往**正文 Markdown** 里注入一个 U+FFFD 替换字符（批次 57 我自己手误打进过一处）',
    expect: (gs) => gs.find((g) => g.标签.includes('乱码扫描'))?.红 === true,
    inject: (t) => `${t}\n\n<!-- 门自测注入：乱码 -->\n替换字符：\uFFFD\n`,
  },
  {
    id: 'ufffd-in-script',
    target: 'scripts/jimeng-b246.mjs',
    gates: ['乱码扫描'],
    why: '往**探针脚本**里注入一个 U+FFFD —— 正是批次 249 补上的那个覆盖空洞（批次 248 就是这样带着 3 个乱码过了 11 道门）',
    mustMention: 'jimeng-b246.mjs',
    expect: (gs) => gs.find((g) => g.标签.includes('乱码扫描'))?.红 === true,
    // 🔴 批次 250 自省：**第一版这里漏掉了那个字符本身**（只写了「脚本里的乱码」这几个字），
    //   而当时收尾门**因为另一条陈旧白名单而恰好是红的** ⇒ 这个用例**被一个无关的失败顶过了**。
    //   ⇒ 「注入 → 门红」这条链**根本没被验证**，却是绿的。
    //   所以下面补上真字符，并且配 `mustMention`（见文件头）做**指名道姓**的断言。
    inject: (t) => `// 门自测注入：脚本里的乱码 \uFFFD\n${t}`,
  },
  {
    id: 'missing-shot',
    gates: ['站点构建'],
    why: '引用一张不存在的截图，构建器的「截图数与源一致」应当报不一致',
    expect: (gs) => gs.find((g) => g.标签.includes('站点构建'))?.红 === true,
    inject: (t) => `${t}\n\n![门自测注入的不存在截图](../screenshots/__gate_selftest_no_such__.png)\n`,
  },
  {
    id: 'backfill-unmarked',
    gates: ['订正回填门'],
    why: '在正文里**附近确实没有订正**的位置，复述一条已被推翻的措辞且不带任何订正标记 —— 正是批次 74 抓到的那一类',
    expect: (gs) => gs.find((g) => g.标签.includes('订正回填门'))?.红 === true,
    // ⚠️ 注入文本里绝不能出现标记词（订正/推翻/已被/口径/机制…），否则门会判它「已标记」
    // 🔴 位置由 `插入到无订正邻域` **按规则**挑，不是手工挑一个能过的位置
    inject: (t) => 插入到无订正邻域(t, '- 时间线/主体可连'),
  },
];

const runGate = () => {
  const r = spawnSync(process.execPath, [join('scripts', 'jimeng-final-gate.mjs')],
    { cwd: ROOT, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, timeout: 300000 });
  return { code: r.status, out: `${r.stdout || ''}${r.stderr || ''}` };
};

const restore = (rel, bytes, digest) => {
  writeFileSync(join(ROOT, rel), bytes);
  const now = readFileSync(join(ROOT, rel), 'utf8');
  if (sha(now) !== digest) throw new Error(`还原后 sha256 不一致：${rel}`);
  const q = spawnSync('git', ['diff', '--quiet', 'HEAD', '--', rel], { cwd: ROOT });
  if (q.status !== 0) throw new Error(`还原后该文件与 HEAD 不一致（请人工检查）：${rel}`);
};

if (LIST_ONLY) {
  console.log(`收尾门阳性对照自测 —— 共 ${CASES.length} 个用例（默认注入目标：${TARGET}）\n`);
  for (const c of CASES) {
    console.log(`  ${c.id.padEnd(16)} 期望这几道门变红: ${c.gates.join(' / ')}`);
    console.log(`      注入目标: ${c.target || TARGET}`);
    console.log(`      ${c.why}\n`);
  }
  process.exit(0);
}

console.log('=== 收尾门 · 阳性对照自测 ===');
console.log('原则：一道从不失败的检查等于没有这道检查。');
console.log('判据按**门的标签**匹配，不按序号 —— 门从 9 项长到 11 项后，旧写法让本脚本一直空转（批次 250）。\n');

// 🔴 收尾前先确认所有注入目标都对 HEAD 干净，脏了就不该动手（避免把别人的 WIP 搅进来）
const 脏目标 = [];
for (const c of CASES) {
  const rel = c.target || TARGET;
  const q = spawnSync('git', ['diff', '--quiet', 'HEAD', '--', rel], { cwd: ROOT });
  if (q.status !== 0) 脏目标.push(rel);
}
if (脏目标.length) {
  console.log(`⛔ 注入目标对 HEAD 不干净，先处理掉再跑（本次不会改任何文件）：\n  ${脏目标.join('\n  ')}`);
  process.exit(4);
}

const 原始 = new Map();
for (const c of CASES) {
  const rel = c.target || TARGET;
  if (!原始.has(rel)) 原始.set(rel, readFileSync(join(ROOT, rel), 'utf8'));
}
console.log(`注入目标 ${[...原始.keys()].join('、')}`);
console.log(`原始 sha256 ${[...原始.keys()].map((k) => `${k.split('/').pop()}=${sha(原始.get(k)).slice(0, 12)}`).join(' ')}\n`);

const results = [];
let broken = 0;
for (const c of CASES) {
  const rel = c.target || TARGET;
  const pristine = 原始.get(rel);
  try {
    const injected = c.inject(pristine);
    if (injected === pristine) throw new Error('注入没有改变文件内容 —— 用例本身写错了');
    writeFileSync(join(ROOT, rel), injected);
    console.log(`▶ ${c.id}：${c.why}`);
    const { code, out } = runGate();
    const gs = parseGates(out);
    const okExpect = c.expect(gs);
    // 🔴 「门红的原因必须点名这个文件」—— 否则可能是被**另一条无关的失败**顶过的
    const okMention = !c.mustMention || out.includes(c.mustMention);
    const ok = okExpect && okMention;
    const failed = code !== 0;
    console.log(`  收尾门退出码 ${code}（${failed ? '非 0，符合预期' : '**是 0** —— 门没拦住'}）`);
    console.log(`  门上共解析出 ${gs.length} 道判定`);
    if (c.mustMention) {
      console.log(`  ${okMention ? '✅' : '⛔'} 门的明细点名了 \`${c.mustMention}\`${okMention ? '' : ' —— **门红的原因不是这个文件，本用例无效**'}`);
    }
    if (!ok) {
      broken++;
      console.log(`  ⛔ 期望的门没有变红 —— 这道门可能是恒真的。实际各门：`);
      for (const g of gs) console.log(`     ${g.红 ? '❌' : '✅'} ${g.序号} ${g.标签}`);
    } else console.log(`  ✅ 期望的门如期变红：${c.gates.join(' / ')}`);
    results.push({ id: c.id, ok, code, gates: c.gates });
  } catch (e) {
    broken++;
    console.log(`  ⛔ 用例执行出错：${e.message}`);
    results.push({ id: c.id, ok: false, err: e.message, gates: c.gates });
  } finally {
    // 🔴 还原失败 = 立即中止。批次 249 那版只报错然后继续跑，
    //    结果把夹具留在正文里、污染了工作区，只能手工清理。
    try {
      restore(rel, pristine, sha(pristine));
      console.log('  ↩︎ 已逐字节还原并断言与 HEAD 一致\n');
    } catch (e) {
      console.error(`\n⛔ 还原失败：${e.message}`);
      console.error('⛔ **已立即中止**：继续跑只会把更多夹具留在工作区里。');
      console.error(`⛔ 请手工核对 \`git status -- ${rel}\`。`);
      process.exit(4);
    }
  }
}

console.log('================ 结论 ================');
for (const r of results) console.log(`  ${r.ok ? '✅' : '⛔'} ${r.id.padEnd(16)} 期望变红: ${r.gates.join(' / ')}`);
console.log(`\n${broken ? `⛔ ${broken} 个用例未达预期 —— 有恒真的门，或用例写错了` : '✅ 全部用例达预期：被测的每一道门都会失败，因此它们的 ✅ 有意义'}`);
console.log('ℹ️ 第 2 道「交叉一致性」不在本自测内：它是**扫读器**不是断言门');
console.log('   （只报「可疑命中 N 处」、退出码恒 0，✅ 只表示脚本跑通了）。');
process.exit(broken ? 3 : 0);