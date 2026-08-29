# Batch 86 计划：Director 变换/移动入口与拒绝反馈

> 状态：`COMPLETED` / `RECORDED_PASS`。
>
> 建档日期：2026-08-29。
>
> 本批是当前最多五个连续 batch 中的第三个。目标是把 Director “选中后如何
> 移动”变成可发现、可验证的 clone-owned workflow，并检查移动相关输入路径
> 是否都遵守既有 `DIRECTOR_TARGET_LOCKED` 与 gesture/history 合同。

## 1. 背景与现状证据

已阅读：

- `docs/research/liblib-canvas-batch77-2026-08-28/`：TransformControls
  explicit attachment、真实 pointer drag、one-entry history 和 cleanup；
- `docs/research/liblib-canvas-batch78-2026-08-28/`：Director pointer
  cancellation、失焦/隐藏/卸载清理；
- `docs/research/liblib-canvas-batch84-2026-08-29/`：锁定对象的
  `DIRECTOR_TARGET_LOCKED` 编辑保护；
- `DirectorViewport.tsx`、`DirectorInspector.tsx`、`DirectorObjectTree.tsx`
  和 `directorStore.ts` 的当前实现。

当前 clone 已具备：

- 对象树选择对象后，Viewport 渲染显式绑定的 `TransformControls`；
- 底部工具栏的移动、旋转、缩放 mode；
- Inspector 的位置 X/Y/Z 数值字段；
- `authoredObjects` 到 runtime `objects` 的变换投影；
- Director gesture 一次提交一条 history；
- 锁定对象仍可选择/隐藏/删除，但变换编辑被 store 拒绝。

发现的可改进点：

1. 底部变换工具栏只有 icon，未投影当前变换目标；没有选择目标时，用户很难
   判断为什么看不到 gizmo。
2. 锁定对象的工具栏仍可切换 mode，但不会在工具栏附近告诉用户当前目标不可
   编辑；锁定信息只在 Inspector/对象树中可见。
3. 对象和分组 `TransformControls` 主要依赖 window `pointerup` 与
   `onMouseUp`，路径控制点已有显式 `onPointerCancel`；移动输入路径应统一
   处理 pointer cancel/lost capture，避免未来实现变化时残留 gesture。
4. 需要用 fresh-page 真实 pointer 输入覆盖对象 gizmo、Inspector 位置字段和
   locked rejection，而不是只调用 store action。

## 2. 证据边界

| 标签 | 本批允许的结论 |
|---|---|
| `CLONE_FACT` | 当前 clone 的对象树、Inspector、TransformControls 和 store action 结构 |
| `CLONE_DECISION` | 用目标状态投影/tooltip 提升移动入口发现性；统一 pointer cancel/lost capture 清理 |
| `SOURCE_UNKNOWN` | LibTV 原站 Director 是否有相同 TransformControls、目标提示、快捷键、文案和 exact placement |
| `UPSTREAM_INSPIRATION` | StoryAI/现有 clone 对 Director 变换工具与对象树的组织方式，仅作为借鉴，不作 LibTV 事实 |

本批不重新识别已有截图；如需视觉证据，先查对应 `SCREENSHOT_ANALYSIS.md`，
并只在现有记录不能回答问题时新增截图。

## 3. 实施范围

纳入：

- 为 Director 变换工具栏增加稳定的目标上下文/状态投影和 ARIA；
- 在无选择、分组选择、锁定对象或锁定分组成员时，提供可发现的 tooltip/状态；
- 为对象和分组 TransformControls 增加显式 pointer cancel/lost capture 清理；
- 保持移动、旋转、缩放均由同一 TransformControls/gesture/history authority；
- 增加 Batch 86 pure/source verifier 和 fresh-page Playwright verifier；
- 更新 current manifest、verification ledger、Harness、research index、
  component coverage 和本批实施记录。

不纳入：

- 重新推导 LibTV 原站 Director exact DOM/CSS；
- 引入键盘箭头移动、系统剪贴板或新的坐标系；
- 改变 Batch 77 的 explicit attachment、普通画布导航或 React Flow；
- 改变锁定对象的删除/可见性策略；
- 重构所有 Director pointer hooks；
- 真实 mesh、全景、远程资源或 provider。

## 4. 验收标准

- 选中普通对象时，变换工具栏能通过 DOM/ARIA 发现当前目标和当前 mode；
- 选择对象后，真实 gizmo pointer drag 能改变 authored/runtime position，
  只产生一条 history，undo/redo 可往返；
- Inspector 位置字段仍可修改并保持同一 document/history authority；
- 无选择时不会误显示可编辑目标；
- 锁定对象和包含锁定成员的分组显示不可编辑状态，直接 store/gesture 调用
  返回 `DIRECTOR_TARGET_LOCKED`，不产生 document/history mutation；
- pointercancel/lost pointer capture 后 transform object 恢复、active gesture
  清空、后续 pointer drag 仍可工作；
- desktop/mobile 不溢出，console/page/request diagnostics 为 0；
- 专项 verifier、`npm run check`、`npm run docs:check` 和文档检查通过。

## 5. 计划步骤

- [x] 阅读 Batch 77/78/84 合同和当前移动实现；
- [x] 记录当前缺口、证据边界和实施范围；
- [x] 实施变换目标状态投影与 pointer cleanup；
- [x] 新增并运行 pure/source verifier；
- [x] 新增并运行 fresh-page Playwright verifier；
- [x] 补齐 Batch 86 `README.md`、`IMPLEMENTATION.md`、`runtime-audit.json`；
- [x] 更新治理入口和当前 verifier manifest；
- [x] 运行跨批回归与全量检查；
- [x] commit/push，确认工作区干净。

## 6. 结果摘要

- Batch 86 pure/source verifier：`PASS`；
- Batch 86 fresh-page Playwright：`SCRIPT_RECORDED_PASS`；
- Batch 59、67–86 current-gate 串行回归：全部通过；
- `npm run check`、`npm run docs:check`、`python3 scripts/verify-docs.py`
  和 `git diff --check`：通过；
- 无截图新增；Director source-exact 结论仍为 `SOURCE_UNKNOWN`；
- 代码和文档 checkpoint 在本批 closeout commit 中建立并推送。
