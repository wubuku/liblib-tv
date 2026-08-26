# Batch 58 实施记录：节点绑定浮层失效收口

> 状态：`SCRIPT_RECORDED_PASS`（2026-08-27 focused pass、相邻回归、质量门禁
> 和 checkpoint closeout 已完成）。

## 1. 变更历史

| 时间 | 变更 | 结果 |
|---|---|---|
| 2026-08-27 | 建立 Batch 58 计划、证据边界和截图台账 | 已完成 |
| 2026-08-27 | 新增纯 reconciliation、owner canvas identity 与 verifier hooks | 已完成 |
| 2026-08-27 | 接入普通 LibTV route lifecycle，覆盖删除和 active canvas 变化 | 已完成 |
| 2026-08-27 | 首次 focused verifier 运行 | 发现 preview modal 会拦截顶部 canvas trigger；不是业务断言失败 |
| 2026-08-27 | 将 canvas-switch scenario 改为 verifier-only store action | 已修正 |
| 2026-08-27 | focused verifier 重跑：删除/切换覆盖 preview、annotate、element-edit、Director | 已通过 |
| 2026-08-27 | 两张截图首次识别并写入台账 | 已完成；只记录 clone 可见层级 |
| 2026-08-27 | 跨批回归：Batch 35、50、52、53、54、56、57 | 全部通过 |
| 2026-08-27 | `npm run check`、`verify-docs.py`、`git diff --check` | 全部通过 |
| 2026-08-27 | commit/push checkpoint | 已完成；见下方 |

## 2. 预期文件

- `src/lib/libtvUiOwnerReconciliation.ts`
- `src/store/uiStore.ts`
- `src/app/page.tsx`
- `scripts/verify-liblib-batch58.py`
- 本目录的 runtime audit、截图和实施记录

## 3. 验证记录

已完成：

- pure reconciliation cases；
- preview/annotate/element-edit/Director delete cleanup；
- 四类 owner 的 active canvas switch cleanup；
- graph/history/selection 只发生 delete 本身的变化；
- desktop/mobile overflow；
- browser diagnostics；
- Batch 58 focused Playwright。

跨批与质量门禁：

- `verify-liblib-batch35.py`、`verify-liblib-batch50.py`、
  `verify-liblib-batch52.py`、`verify-liblib-batch53.py`、
  `verify-liblib-batch54.py`、`verify-liblib-batch56.py`、
  `verify-liblib-batch57.py`：全部通过；
- `npm run check`：通过；保留 9 条既有 lint warnings，无 error；
- `python3 scripts/verify-docs.py`：通过（478 Markdown files、2162 local targets）；
- `git diff --check`：通过；
- `verify-liblib-batch58.py`：通过，`runtime-audit.json` 记录四类 owner 的
  delete/switch cleanup、graph/history delete-only 断言和 browser diagnostics。

## 4. Checkpoint

本批计划 checkpoint：`a542068`（已 push）。
实施 checkpoint：`372d3ad`（已 push 到 `origin/master`；提交后工作区干净）。
Batch 58 只完成 clone-owned node-bound UI invalidation，不宣称完整
`LIBTV-VR-013` relation-aware delete planner，也不证明源站 destructive delete、
远程资源回收、Director workspace 持久化或 undo 恢复 overlay。
