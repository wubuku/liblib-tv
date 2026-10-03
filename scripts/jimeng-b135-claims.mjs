// 批次 135：向订正台账追加第 54 条，并修复一条**既有**的 U+FFFD 损坏。
//
// 🔴 为什么必须顺手修那个损坏：`history-tabs-four` 条目的 reason 里
//   「面板另有<U+FFFD><U+FFFD><U+FFFD>级页签两个」—— 三个替换字符连在一起。
//   本轮要改这个文件，而「本任务所有改动文件 U+FFFD 必须为 0」是硬门
//   ⇒ 不修就会被自己的门拦下。原文按上下文应为「一级」（该条目自身引用的正是批次 11 的原说法）。
//   **只在确知原字符时替换，不做「删掉替换字符」式的和稀泥。**
import fs from 'node:fs';

const P = 'scripts/jimeng-refuted-claims.json';
const raw = fs.readFileSync(P, 'utf8');

// ---- ① 既有损坏：三个连在一起的 U+FFFD → 「一」
// ⚠️ 损坏样本**不能直接写成字面量** —— 那会让本脚本自己带 9 个 U+FFFD，
//    撞上「本任务所有改动文件 U+FFFD 必须为 0」这条硬门。改用转义构造。
const count = (s) => (s.match(/\uFFFD/g) || []).length;
const BAD = new RegExp('面板另有' + '\\uFFFD'.repeat(3) + '级页签两个');
const before = count(raw);
// 幂等：损坏已修过时如实报告并继续（不盲改），只有「既没损坏也没修过」才停下
let fixed = raw;
if (BAD.test(raw)) {
  fixed = raw.replace(BAD, '面板另有一级页签两个');
  console.log(`① 修复既有损坏：U+FFFD ${before} → ${count(fixed)}`);
} else if (before === 0) {
  console.log(`① 既有损坏已在本批修过（U+FFFD = 0），跳过`);
} else {
  console.error('⛔ U+FFFD 非零但找不到预期的损坏片段 —— 停下人工确认，不要盲改');
  process.exit(2);
}

const d = JSON.parse(fixed);
const n0 = d.entries.length;
if (d.entries.some((e) => e.id === 'multi-select-toolbar-does-not-follow-zoom')) {
  console.log('② 第 54 条已存在，跳过追加');
} else {
  d.entries.push({
    id: 'multi-select-toolbar-does-not-follow-zoom',
    label: '「多选工具条挂在画布 viewport 之外 ⇒ 不随画布缩放」—— 原写在 SOURCE_OBSERVATIONS.md §4.52「e 轮顺带钉死：工具条不在画布坐标系里」与 PROGRESS.md「顺带：工具条不在画布坐标系里」；批次 87 对「宽度由选中集撑开」的归因也只对了一半',
    patterns: [
      '工具条不在画布坐标系里，不随画布缩放',
      '不在画布坐标系、不随缩放',
    ],
    pattern_note: '（不可用裸的 `不随缩放`：`20-reference.md` / `prepare-generation.md` / `director-node.md` 里「**生成面板**不随缩放」是**正确**记录，拿它当 pattern 会把正确结论判成「改了结论没回填」。⇒ 与 `search-panel-size-is-not-320x211`、`multi-selection-toolbar-has-no-add-tags` 同源：**pattern 要能区分「同一串字的不同归属」**，必须绑上「工具条 + viewport 之外」这个具体语境。）',
    refuted_in: '批次 135（SOURCE_OBSERVATIONS.md §4.56）',
    reason: '**「`css` 尺寸 = 屏上尺寸」证明的是「没人替它乘 scale」，不等于「没人乘 scale」—— 它可以自己乘。** 2026-10-03 批次 135 做**受控两臂**（此前从未有人做过单自变量实验：批次 87 自述「只改缩放，**选中集跟着变**」，74% 选 7 个 / 60% 选 8 个；批次 131 只取了 60% **单档**）。**第一臂**锁定同一 6 个选中节点、只改缩放四档（40/60/100/200%），外层 `node-toolbar` 屏上宽 = `400 / 600 / 1000 / 2000` = **`1000 × scale`（正比，不是反比）**；**第二臂**锁定 60%、只改选中数（2/3/6 个），外层 canvas 宽 `600/960/1000` 与包围盒 canvas 宽 `520/880/920` **差恒为 `80`**。🔑 **完整公式：屏上宽 = (选中集包围盒 canvas 宽 + 80) × 当前缩放** ⇒ 它**同时**依赖两个变量且**串联**：既随选中集变，**也随缩放变**。祖先链 `react-flow__node-toolbar → react-flow__renderer`（**不含** `.react-flow__viewport`）证实它确实在画布坐标系之外 ⇒ 组件是**自己按 canvas 尺寸算完再手工乘 scale**。📌 因此「viewport 之外」这半句**是硬的**（保留），错的只是从它推出的「不随缩放」；批次 87「511 与 1298 在 canvas 口径下差 1.88 倍所以不自洽」的自查**也不成立** —— 差异来自**那两次选中集不同**。📌 同批附带一条**量纲陷阱**：`20-reference.md` 记的 `flow-node-multi-selection-source-handle` = `60×120` 是「**屏上恒**」（四档 40/60/100/200% 屏上与 `offsetWidth` 逐字相同），而 `AUDIT.md`/`PROGRESS.md` 里被反复确认的「**canvas 恒** `60×120`」指的是 `flow-node-{target,source}-handle`；两者 `offsetWidth` **都是** `60×120`，但前者不在 viewport 内（不被乘，60% 下屏上 `60×120`）、后者在 viewport 内（被乘，60% 下屏上 `36×72`）。📌 **立规：判「某元素跟不跟缩放」要分两问** —— ① 它在不在 `.react-flow__viewport` 里（决定**谁**给它乘）；② 它屏上尺寸随不随 scale 变（决定**结果**）。**两问都要实测，不能从前一步推后一步。**',
  });
  console.log(`② 台账条目：${n0} → ${d.entries.length}`);
}

fs.writeFileSync(P, JSON.stringify(d, null, 1));
const end = fs.readFileSync(P, 'utf8');
console.log('③ 写回后 U+FFFD =', count(end), '｜字节', Buffer.byteLength(end));
JSON.parse(end);
console.log('④ JSON 可解析 ✅');
