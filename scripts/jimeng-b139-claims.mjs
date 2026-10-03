// 批次 139：把本批的订正写进订正台账（scripts/jimeng-refuted-claims.json）。
//
// 📌 为什么单独一个脚本而不是手改 JSON：台账是**门**的输入（jimeng-backfill-gate.mjs
//   逐条 grep 全册、要求命中处 ±3 行内有订正标记），手改容易写出打不开的 JSON 或者漏字段。
//   走脚本 = 走同一条路径，顺带自检。
import fs from 'node:fs';

const F = 'scripts/jimeng-refuted-claims.json';
const j = JSON.parse(fs.readFileSync(F, 'utf8'));
const 新 = {
  id: 'group-toolbar-width-blame-card-width',
  label: '「组工具条宽度跟随组卡片宽度……（同样 60%/47% 缩放下**卡片宽度不同所致**）」—— 原写在 10-tasks/organize-group-layout.md「组工具条（实测）」小节与 20-reference.md / 30-concepts.md 的同句',
  patterns: [
    '卡片宽度不同所致',
    '组工具条跟随组卡片宽度',
  ],
  pattern_note: '（不可用裸的 `宽度跟随`：`20-reference.md` 与批次 87/131 里关于**多选工具条**宽度的多段记述是**正确**的（公式是 `(包围盒canvas宽+80)×scale`），拿它当 pattern 会把正确记录判成「改了结论没回填」。⇒ 与 `multi-select-toolbar-does-not-follow-zoom`、`multi-selection-toolbar-has-no-add-tags`、`search-panel-size-is-not-320x211` 同源：**pattern 必须绑上「组工具条 + 卡片宽度不同所致」这个具体归因**，不能只抓关键词。）',
  refuted_in: '批次 139（SOURCE_OBSERVATIONS.md §4.60）',
  reason: '**「卡片宽度会因换缩放而变」是未经验证的猜测，而且方向反了。** 组卡片是 React Flow 节点，宽是 canvas 口径的 `style.width`（实测八档**恒为 560**）⇒ 换缩放**根本不会**改它。2026-10-03 批次 139 做**单自变量实验**（此前从未有人做过：批次 18 只有 100% 单档、屏上对屏上）：护栏建 3 个文本节点成组，**锁定同一个组只改缩放**，八档（40/45/50/53/55/60/100/200%）逐字复现。🔑 **完整公式：`组工具条屏上宽 = max(组卡片 canvas 宽 × 当前缩放, 296)`**，高度恒 40 —— 60/100/200% 三档 `560×scale` 逐字相等；40/45/50% 三档 `560×scale` 分别为 `224/252/280` **全都小于 296**，读数一律停在 `296`（即 `max` 的第二支）；**53% 是交叉点后第一档**（`560×0.53=296.8`，读数逐字 `296.8`，不是 296 也不是 297）⇒ `max()` 坐实、`296` 是硬下限。`296` 的来源是内层 `selection-context-toolbar` 的固有宽（四个按钮撑出来的，**八档恒定**，与卡片和缩放都无关），交叉点 = `296÷560 = 52.86%`。🔴 **手册那个 47% 的 `296×40` 由此得解**：`560×0.47 = 263.2 < 296` ⇒ **落在下限区**，不是「卡片宽度不同」。（同表 60% 那两行 `336/367` 的差异**是真的**卡片宽度不同，那是另一个自变量，不受影响。）📌 它**不是**批次 135 那个多选公式：多选是 `(包围盒canvas宽+80)×scale` **带 `+80`**，组这个**不带**（同组 60% 时 `(560+80)×0.6=384 ≠ 336`）⇒ **两套工具条同在画布坐标系之外，但各算各的**。📌 立规：**「宽度跟随某个 X」这句话要问三件事** —— ① X 本身是不是自变量（组卡片宽**不是**）；② 宽度与 X 是不是正比（是）；③ **有没有下限**（有，`max` 的第二支）。前两件对、第三件漏了，表格里就会出现「同 X 不同宽」的行，而人最容易把它归因到 X 变了。',
};
if (!j.entries.some((e) => e.id === 新.id)) {
  j.entries.push(新);
  fs.writeFileSync(F, JSON.stringify(j, null, 2) + '\n');
  console.log('已追加，当前条数 =', j.entries.length);
} else {
  console.log('已存在，跳过');
}
