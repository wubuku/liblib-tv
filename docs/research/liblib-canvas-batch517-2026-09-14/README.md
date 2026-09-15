# Batch 517 — GRAPH-DELETE focused fixture：plain 删除场景聚焦验收

> 状态：`FOCUSED_BROWSER_RECORDED_PASS`（commit 本批）。经真实
> removeSelectedNodes/undo/redo：删除选中节点同时移除其连接边（结构
> 闭合）、恰一步 history、选择不再引用已删节点、undo 完整恢复节点与
> 边、redo 再次移除（零残缺）。derived/shot/process 聚合修复与
> canvas 场景未建（留档）。

## 探针记录

- `addEdge` 校验返回词表为 `allow/reject`（batch 57 合同），拒绝 reason
  如 `INVALID_HANDLE_DIRECTION`；handle id 为字面 `source`/`target`。
