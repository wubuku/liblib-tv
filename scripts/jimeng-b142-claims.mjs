// 批次 142：把本批的**两条订正**写进订正台账。
//   ① 批次 141「所有族都是 max(canvas×scale, 屏上常量)」这条立规被推翻（节点侧是 min）；
//   ② 批次 141 写在手册里的 `max(48×缩放,24)` / `max(20×缩放,10)` 两条公式是错的。
import fs from 'node:fs';

const F = 'scripts/jimeng-refuted-claims.json';
const j = JSON.parse(fs.readFileSync(F, 'utf8'));
const 新 = [
  {
    id: 'all-ui-clamped-elements-share-one-max-template',
    label: '「所有 UI 元件都是同一个模板 `屏上值 = max(canvas常量 × 缩放, 屏上常量)`；低缩放随画布缩、高缩放给一个人类可点的下限」—— 原写在 SOURCE_OBSERVATIONS.md §4.62.2 与 §4.62 的「立规（可复用）」、PROGRESS.md 批次 141「🔑 公式」小节、AUDIT.md 批次 141 行',
    patterns: [
      '所有族都是.*`max',
      '所有 UI 元件都是',
      '同一个 `max\\(`模板',
    ],
    pattern_note: '（不可用裸的 `max\\(` 或 `钳位`：批次 139 的**组工具条**公式 `max(卡片宽×scale, 296)` 是**正确**且**至今成立**的，拿它当 pattern 会把正确记录判成「改了结论没回填」。⇒ 与 `multi-select-toolbar-does-not-follow-zoom`、`group-toolbar-width-blame-card-width` 同源：**pattern 必须绑上「所有族 / 所有 UI 元件 / 同一个模板」这个具体断言**，即只抓那条**过度归纳的立规**本身。）',
    refuted_in: '批次 142（SOURCE_OBSERVATIONS.md §4.63）',
    reason: '**那条立规是从 4 个读数过度归纳出来的，方向是反的。** 批次 141 的八档数据本身就没被算对：`max(48×0.36, 24) = 24`，而 36% 档**实测是 `17.28`**；`max(48×0.6, 24) = 28.8`，而 60% 档**实测是 `24`** ⇒ `max` 在两端都算错，节点角把手是 **`min(48×scale, 24)`（封顶）**、边把手厚度是 **`min(20×scale, 10)`（封顶）**，交叉点 50%。批次 142 补测**组卡片**（canvas 恒 560，九档 20/25/30/40/50/60/100/150/200%）得到方向**相反**的结论：组角把手 = **`max(24×scale, 24)`（保底，交叉点 100%）**，组边把手厚度 = **`10×scale`（完全不钳位）**，组边把手长度 = 卡片 canvas 宽 × scale（**不钳位**）。🔑 直接证据：≥120% 时组角读 `36 / 48` **大于**节点角的 `24`。⇒ 合起来是「**三个量不钳、两个封顶、两个保底**」，连钳不钳都逐量不同。「高缩放给一个可点的下限」这个**直觉解释**也失效：把手在高缩放下是**不再变大**（封顶），不是托底。📌 **立规（替换批次 141 那条）**：**公式只在它被实测的那一族里成立**；跨族推广必须先测那一族，哪怕「看起来显然是同一套」。读任何 UI 元件在缩放下多大时，唯一可靠动作是把它自己的低段与高段各量几档，分别反推 `屏上/scale`（看 canvas 常量）与绝对值（看屏上常量）——**钳不钳、往哪钳、交叉点在哪，三者都要从数据里读出来**。',
  },
  {
    id: 'node-resize-handles-are-max-48-24',
    label: '「节点四角把手 = `max(48 × 缩放, 24)`、边中点把手厚度 = `max(20 × 缩放, 10)`」—— 原写在 10-tasks/create-first-node.md「拖动要按住卡片主体」小节、20-reference.md「缩放把手是八向」小节、PROGRESS.md 批次 141、AUDIT.md 批次 141',
    patterns: [
      '`max\\(48 × 缩放, 24\\)`',
      '`max\\(20 × 缩放, 10\\)`',
      'max\\(48\\s*×\\s*缩放',
    ],
    pattern_note: '（这两串是**逐字**的公式写法，全册只出现在批次 141 写下的那几处；正确写法 `min(...)` 不含 `max(`，不会误命中。与 `group-toolbar-width-blame-card-width` 同源：**pattern 要能区分同一族里写对与写错的两处**。）',
    refuted_in: '批次 142（SOURCE_OBSERVATIONS.md §4.63.1）',
    reason: '**算一遍就知道 `max` 不成立**：批次 141 自己的八档表里，36% 档实测 `17.28` 而 `max(48×0.36, 24) = 24`；60% 档实测 `24` 而 `max(48×0.6, 24) = 28.8` —— **两端都算错**。正确公式是 **`min(48 × scale, 24)`（封顶，交叉点 50%）** 与 **`min(20 × scale, 10)`（封顶，交叉点 50%）**：低缩放时把手随画布一起缩（36% → `17.28`，用户能看见它在缩），放大到 50% 以后**不再变大**，固定在角 `24px` / 边 `10px`。📌 反向证据：组卡片的同名把手走的是**相反**方向（`max(24×scale, 24)`，交叉点 100%），所以不能拿任一侧的公式推另一侧。',
  },
];
let n = 0;
for (const e of 新) {
  if (!j.entries.some((x) => x.id === e.id)) { j.entries.push(e); n++; }
}
fs.writeFileSync(F, JSON.stringify(j, null, 2) + '\n');
console.log('追加', n, '条，当前总条数 =', j.entries.length);
