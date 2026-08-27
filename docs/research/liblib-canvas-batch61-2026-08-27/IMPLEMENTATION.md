# Batch 61 实施记录：React Flow Change Routing 与运行态选择权威

> 状态：`IMPLEMENTED_FOCUSED_PASS`。
>
> 实施日期：2026-08-27。
>
> 规划基线：`67e6276`。

## 1. 本轮完成

- 新增 [`src/lib/libtvReactFlowChangeRouting.ts`](../../../src/lib/libtvReactFlowChangeRouting.ts)：
  对安装版 `@xyflow/react@12.11.1` 的 Node/Edge change union 做整批分类；
  允许 T0 selection 与 T1 existing-node position/passive dimensions，拒绝
  semantic `add/remove/replace`、attribute resize、未知 variant、陈旧 ID 和
  非有限数值。
- `canvasStore` 增加 current-snapshot `routeReactFlowChanges`，并暴露
  `window.__libtv_route_react_flow_changes` 供 focused verifier 使用。
- 普通画布增加独立 `selectedEdgeIds` session owner；edge `selected` 仅由 route
  projection 产生，不再写入 semantic edge record。
- `page.tsx` 的 `onNodesChange/onEdgesChange` 不再直接使用 generic
  `applyNodeChanges/applyEdgeChanges`；selection 与 transport 都从同一 active
  canvas snapshot 路由。
- history snapshot、duplicate node/edge、setNodes/setEdges、named edge delete
  对 framework selection/runtime 字段做了边界处理。
- 增加 [`scripts/verify-liblib-batch61.py`](../../../scripts/verify-liblib-batch61.py)。
- 通过 Batch 6 框选回归发现并修复一个 controlled React Flow 交互问题：
  `onSelectionChange` 与 `onNodesChange/onEdgesChange` 双重写回会在框选期间
  重置内部 `.react-flow__selection`；现由 change routing 作为唯一 selection
  ingress，保留框选期间的 selection rectangle。

## 2. 验证结果

`python3 scripts/verify-liblib-batch61.py` 通过，覆盖：

- node/edge selection；
- finite position、passive dimensions、mixed T0/T1；
- semantic node/edge add/remove/replace 零副作用拒绝；
- attribute resize、NaN、Infinity、unknown variant、stale ID、old canvas；
- same-ID mixed batch 的 whole-batch reject；
- current store 新增 edge 不被旧 route closure 覆盖；
- history/copy runtime-field sanitation；
- 真实 node click、multi-frame drag + one stop、no-op drag；
- 真实 edge select、scissors delete、undo/redo；
- desktop `929x874`、mobile `390x844`、overflow 和 console/page/request diagnostics。

相邻回归：

- `python3 scripts/verify-liblib-batch4.py`：通过；
- `python3 scripts/verify-liblib-batch5.py`：通过；
- `python3 scripts/verify-liblib-batch6.py`：通过。
- `python3 scripts/verify-liblib-batch7.py`：通过；
- `python3 scripts/verify-liblib-batch8.py`：通过；
- `python3 scripts/verify-liblib-batch9.py`：按既有台账记录为
  `EXPECTED_HISTORICAL_MISMATCH`，失败于旧 `900.5px` toolbar 宽度；当前
  Batch 52/60 合同为 `1092.5px`，未回退当前实现。

首次真实 callback 观察到的安装版 payload：

```text
node dimensions: { id, type, dimensions }
node position:   { id, type, position, dragging }
edge selection:   { id, type, selected }
```

所有观察到的 callback 均返回 `status: "applied"`；semantic variant 通过
verifier-only synthetic corpus 证明为零副作用 reject。

## 3. 截图成本与证据边界

本批没有改变节点、边、图片双浮层或 Director 的视觉几何与样式，因此没有新增
截图。既有 Batch 57 的连接视觉证据、Batch 60 的图片双浮层证据继续作为相邻
视觉回归 authority；详细记录见 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)。

本批证明的是 clone-owned React Flow ingress/runtime selection 行为，不证明
LibTV 源站内部使用 React Flow，也不证明源站的混合 node+edge primary、Escape
或完整 focus policy。

## 4. 未完成与下一批入口

- 真实页面中，edge select 发生在已有 node selection 后不会自动清除 node
  selection；这是混合 selection/primary 规则，交给后续 Batch 62，不在本批
  臆测修复。
- `Escape` 与全局 focus/foreground surface 尚未统一；当前仍由既有 listener
  与局部 owner 规则处理。
- node resize、edge reconnect、clipboard/import、persistence、async/resource
  lifecycle、FrameOS 和 Director 不在本批。

后续最高价值 slice：基于本批独立 node/edge selection owner，补齐
selection/focus/command-context 的 primary、清选、foreground policy 和
命令输入快照，但必须继续保持源站 parity 与 clone-owned 行为边界分离。
