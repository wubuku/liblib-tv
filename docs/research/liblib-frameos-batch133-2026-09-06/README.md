# Batch 133：FrameOS 复制节点落地

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 132。
>
> 依据：仓库文档长期记录的缺口——「FrameOS duplicateNode 已构造副本对象但
> 没有把它加入 nodes，复制快捷键当前不会新增节点」。

修复：duplicateNode 将副本对象追加进 nodes（selected: true 与 selectedNodeId
一致）；顺带清理 FrameosBreadcrumb 未用的 useRef import（基线警告 -1）。

## 完成定义

1. `verify-frameos-batch133.py` 10 checks、`0/0/0` diagnostics 通过：
   Cmd+D 插入节点、副本标题含 副本、视觉选中、undo/redo、复制 toast。
2. `npm run check`、`npm run docs:check` 通过。
3. master commit/push。

FrameOS 侧无源站采样依赖（行为依据为仓库文档记录的预期交互）。
