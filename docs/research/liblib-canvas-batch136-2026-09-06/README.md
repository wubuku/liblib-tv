# Batch 136：回收站勾选与批量恢复

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 135。

依据源站回收站的「已选择 0 项」计数碎片，为 /project 回收站面板补全：
逐项 checkbox、`已选择 N 项` 计数、`恢复所选 N 项` 批量恢复按钮。
恢复唯一条目后回收站转为空态（计数器随非空分支消失）。

## 完成定义

1. `verify-liblib-batch136.py` 8 checks、`0/0/0` diagnostics 通过：删除→回收站
   列出→勾选→计数→批量恢复→回到项目列表→选择清零。
2. `npm run check`、`npm run docs:check` 通过。
3. master commit/push。

批量恢复仅操作 clone 内存状态；源站勾选批量操作的完整交互仍为
`SOURCE_UNKNOWN`。
