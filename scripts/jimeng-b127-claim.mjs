// 批次 127 · 追加第 52 条被推翻的主张（「搜索面板尺寸是 320×211」）。
//
// 📌 pattern 的取法（本批的教训，写在文件里免得下一个人又写宽）：
//   手册里 **`320×211` 绝大多数是「生成历史」面板的正确读数**（批次 126/127 复测三次未变），
//   所以**不能**拿 `320×211` 当 pattern —— 那会把 20 处正确记录判成「没回填」。
//   改用「同一行里 搜索 与 320×211 相邻」的正则，两个方向都收：
//     `搜索[^|\n]{0,80}320×211` 与 `320×211[^|\n]{0,80}搜索`
//   `[^|\n]` 是为了不跨表格单元格（那会把整张表吞进来）。
//   实测命中恰好 7 处、**零误伤**。
import { readFileSync, writeFileSync } from 'node:fs';

const f = new URL('./jimeng-refuted-claims.json', import.meta.url);
const j = JSON.parse(readFileSync(f, 'utf8'));
const id = 'search-panel-size-is-not-320x211';
if (j.entries.some((c) => c.id === id)) { console.log('已存在，跳过'); process.exit(0); }

j.entries.push({
  id,
  label:
    '「顶栏『搜索』展开的面板是 `role="dialog"`、`320×211`、位于 (765, 56)」—— 原写在 10-tasks/navigate-canvas.md「搜索节点」小节与同文件批次台账、20-reference.md 顶栏速查行、SOURCE_OBSERVATIONS.md §3.27 与顶栏 testid 对照表、AUDIT.md 与 PROGRESS.md 的批次 2026-10-01 记录',
  patterns: ['搜索[^|\\n]{0,80}320×211', '320×211[^|\\n]{0,80}搜索'],
  pattern_note:
    '（不可用裸的 `320×211`：手册里它多半是「生成历史」面板的**正确**读数，' +
    '拿它当 pattern 会把 20 处正确记录判成「改了结论没回填」。' +
    '⇒ 立规：**refuted-claims 的 pattern 要能区分「同一串数字的不同归属」**。）',
  refuted_in: '批次 127（SOURCE_OBSERVATIONS.md §4.47）',
  reason:
    '**现行构建的搜索面板是 `320×604@765,56`；`320×211` 只在「输入框有词且一个都没匹配上」时才出现。** 2026-10-03 批次 127 用同一套仪表把搜索面板与生成历史面板各读一遍，搜索面板本体是 `<ASIDE role="dialog" aria="搜索" data-testid="canvas-feature-panel">`，x 坐标 **765**（生成历史是 797，宽度都是 320）。五种状态各测一次：① 全部 76 条 / 输入框空 ⇒ **604**；② 输入「音频」命中 68 条 ⇒ **604**；③ 主体页签（该类型 0 个节点）/ 输入框空 / 0 条 ⇒ **604**；④ 输入「zzz不存在」0 命中 ⇒ **211**；⑤ 同上（主体页签内）⇒ **211**。⇒ 相关量是**「输入框有没有词」＋「有没有命中」**，不是结果条数（③④ 都是 0 条却一个 604 一个 211 在不同条件下）。**604 的构成**：`56`（输入行）＋`36`（页签行）＋`512`（结果区，其中视口 `460` ＋ 分页条 `52`；无分页时视口就是 512）。**211 的构成**与生成历史的空态同形（`56`＋`36`＋`119`）。📌 顺带四条：① 搜索面板**与生成历史面板是同一个组件**（同一个 `ASIDE` ＋ 同样的 `canvas-feature-panel-surface` / `canvas-feature-panel-content` 两层包装 ＋ 同一个父级 `canvas-workbench-shell`），只有最内层 `SECTION` 的 testid 不同（`canvas-search-panel` vs `generation-history-panel`）—— 手册一直把它们写成两个独立面板；② **九个分类页签一行放不下**（`role="tablist"` `320×36`、`scrollWidth 519` vs `clientWidth 320`），只有**横向滚动**或点右端那个 `aria="Next search categories"` 的 `24×24` 圆钮才能看到「时间线 / 组 / 其他」；③ **分页条有 4 个按钮**（首页 / 上一页 / `1 / 6` / 下一页 / 末页），其中首页与末页的 aria 是**没插值的 ICU 占位串** `{num, plural, other {向前 {num} 页}}` / `{num, plural, other {向后 {num} 页}}`；④ 面板**记住了上次选的页签**（关掉再开仍停在「其他 1」）。',
});
writeFileSync(f, JSON.stringify(j, null, 2) + '\n');
console.log('追加后条数：', j.entries.length);
