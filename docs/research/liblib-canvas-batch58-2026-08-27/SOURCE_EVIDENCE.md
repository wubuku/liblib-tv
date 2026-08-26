# Batch 58 源站与 clone 证据边界

> 本批不重新操作共享源站，也不执行 destructive source graph action。
> 目标是修复 clone 的节点绑定 UI 生命周期。

## 1. 可复用的已有证据

- [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](../LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)
  记录当前 clone 的 surface、mount owner、关闭路径和不同 anchor 策略；
- [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](../LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)
  将 preview、annotate、element edit 和 Director 列入 UI invalidation impact；
- [`components/ImageAnnotateMode.spec.md`](../components/ImageAnnotateMode.spec.md)
  和 [`components/ImageElementEditMode.spec.md`](../components/ImageElementEditMode.spec.md)
  记录 image owner 及 selection boundary；
- Batch 52-54 记录 image preview/annotate/element-edit 的 local runtime；
- Batch 35-50 记录 Director workspace 的 local runtime。

## 2. Source fact 与 clone fact

### Source fact

本批没有新增 source fact。已有源站证据只授权继续区分：

- selected-node surface；
- active authoring surface；
- full-screen Director surface；
- graph mutation 与 UI-only lifecycle。

它没有授权把 clone 的删除关闭行为写成 LibTV 源站事实。

### Clone fact

修复前的 clone：

- image owner state 只有 `nodeId` 和 media snapshot；
- annotate/element-edit 有 selection mismatch effect；
- preview 没有 graph owner reconciliation；
- Director 只依赖 `activeDirectorNodeId`，没有 route-level node existence guard；
- canvas switch 清 selection，但不统一清理这些 owner。

### Clone decision

本批采用：

```text
owner = { kind, canvasId, nodeId }
valid iff owner.canvasId === activeCanvasId
       && activeNodeIds includes owner.nodeId
```

失效 owner 直接关闭。Preview 不保留为 detached snapshot，因为当前 clone 没有
独立的“脱离 graph 仍可查看”的产品合同；后续若取得明确产品/源站证据，再单独
立项。

## 3. 不可推出的结论

- 删除 graph node 是否需要源站确认弹窗；
- 删除 node 是否同时删除远端媒体、任务或 Director workspace；
- undo 是否恢复 session overlay；
- source canvas 切换是否由服务端驱动；
- owner cleanup 的具体 toast、动画、focus 或 timeout。
