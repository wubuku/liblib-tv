// 批次 126 · 追加第 51 条被推翻的主张（生成历史面板的「一级页签」）。
// 用脚本改是为了保证 JSON 仍然合法、且 patterns 是数组而不是被 shell 吃掉。
import { readFileSync, writeFileSync } from 'node:fs';

const f = new URL('./jimeng-refuted-claims.json', import.meta.url);
const j = JSON.parse(readFileSync(f, 'utf8'));
const id = 'generation-history-panel-has-no-primary-tabs';
if (j.entries.some((c) => c.id === id)) { console.log('已存在，跳过'); process.exit(0); }

j.entries.push({
  id,
  label:
    '「生成历史面板分两层：一级页签两个（生成历史 ｜ 积分明细），二级类型页签五个（全部/图片/视频/音频/文本）」—— 原写在 10-tasks/canvas-context.md「查看生成历史」小节与同文件批次 11 补测记录、SOURCE_OBSERVATIONS.md §2.15 与 §4.xx 台账；20-reference.md 也据此写「生成历史两级页签」',
  patterns: [
    '一级页签两个',
    '一级页签',
    '生成历史两级页签',
    '面板分两层',
    '分两层',
  ],
  refuted_in: '批次 126（SOURCE_OBSERVATIONS.md §4.46）',
  reason:
    '**面板里根本没有「一级页签」，只有一层 `role="tablist"` 和 5 个 `role="tab"`。** 2026-10-03 批次 126 把 `canvas-feature-panel` 整棵 DOM 拆开：面板本体是 `<ASIDE role="dialog" aria="生成历史">` `320×211@797,56`，标题行 `320×56@797,56` 里只有两样东西 —— `H2`「生成历史」`56×36@813,72`（是**标题**）和一个 `BUTTON`「积分明细」`68×36@1033,72`（**没有 `role`、没有 `href`、没有 `aria-label`**，只带一个 `12×12` 的右向箭头 svg）。**全面板 `role="tab"` 恰好 5 个、`role="tablist"` 恰好 1 个**，`role="tabpanel"` 恰好 1 个 ⇒ 计数判据直接否掉「两层」。📌 立规：**「一层 / 两级 / 嵌套」这类措辞必须能被一个计数判据支持**（本例即「`role="tablist"` 的个数」）；批次 31 写下那句话时没有这个判据，所以它错了三个月也没人发现。📌 顺带四条：① 面板有 **4 个元素与它同矩形**（本体 + `canvas-feature-panel-surface` + `canvas-feature-panel-content` + `generation-history-panel`）⇒ 按矩形数会多数三次；② 直接父级是 `canvas-workbench-shell`，**没有 portal 到 body**；③ 5 个页签的 **`aria-controls` 全指向同一个** `generation-history-items`，逐个点过后**面板逐字与矩形一个字都没变** ⇒ 空态是共用的「暂无生成历史」，不是按类型各说一句；④ 那个「积分明细」按钮**开的是「项目信息」对话框**（`workspace-project-info-dialog` `800×546@240,87`，与批次 125 同一个组件、内部同样是 `project-consumption-summary`）并**直接落在「积分消耗」页签** —— 与「更多 → 项目信息」是同一个框，差别只在初始页签。',
});
writeFileSync(f, JSON.stringify(j, null, 2) + '\n');
console.log('追加后条数：', j.entries.length);
