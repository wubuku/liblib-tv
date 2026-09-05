# Batch 115：双击画布打开添加节点面板

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 114。
>
> 源站证据：[`../liblib-canvas-sampling-2026-09-06/README.md`](../liblib-canvas-sampling-2026-09-06/README.md) §2。

空画布提示「双击画布 自由生成节点」的源站行为经采样确认：双击 = 打开添加
节点面板。clone 在 `page.tsx` 的画布容器上增加委托 dblclick 监听（仅
`.react-flow__pane` 命中时），打开 `isAddNodePanelOpen`；不创建节点、不改
graph/history。Escape 关闭后可再次双击打开。

## 完成定义

1. `verify-liblib-batch115.py` 7 checks、`0/0/0` diagnostics 通过。
2. 相邻 batch13 通过；`npm run check`、`npm run docs:check` 通过。
3. master commit/push。

行为确认限工作流模式；节点创建仍通过面板条目完成。
