# Batch 61：React Flow Change Routing 与运行态选择权威

> 状态：`IMPLEMENTED_FOCUSED_PASS`。
>
> 建档日期：2026-08-27。
>
> 对应 backlog：`LIBTV-PAR-008`。
>
> 对应 Open Canvas 交接：`OC-BP-004` / `OC-ADOPT-019`。
>
> 对应 fixture / verifier：`LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01` /
> `LIBTV-VR-016`。

## 目标

把普通 LibTV 画布的 React Flow callback 从“接收 framework union 后直接
`apply*Changes` 并整数组写回”收敛为一个可审计的运行态入口：

```text
NodeChange[] / EdgeChange[]
  -> 整批解析与校验
  -> T0 selection 或 T1 existing-node transport
  -> current active-canvas snapshot
  -> 明确 owner 的原子提交
  -> semantic variant 零副作用拒绝或具名 command 接管
```

本批不是视觉重构。用户可见目标是保持既有选择、拖拽、连线、删除、双浮层
和 edge hover/select 体验，同时消除 semantic `add/remove/replace` 绕过命名
graph command、render closure 覆盖新状态和 mixed batch 部分写入的风险。

## 为什么是下一轮

Open Canvas 专题已经完成 graph ingress、React Flow 12.11.1 change taxonomy、
selection/focus、multi-canvas、viewport、media/editor 和 rendition 合同。当前
最适合进入本地实施的 slice 是 React Flow routing：

- 证据、设计、fixture corpus 和 verifier authority 已完整；
- 不需要共享源站写入、真实 provider、上传、计费或 disposable media fixture；
- 它是后续 delete/copy/async/editor/media graph transaction 的共同入口前置；
- 当前 clone 仍存在明确的 generic reducer 旁路和 stale render closure 风险；
- 可以保持现有视觉和已通过的 Batch 57/58/60 合同不变。

Auto Link、ready-video/process、真实 editor save、media ingress 和 ratio-diverse
source parity 仍有 fixture 或产品边界，不纳入本批。

## 明确不做

- 不实现 node resize、edge reconnect、Quick Add、file drop 或 clipboard import；
- 不重写全部 `canvasStore` graph command；
- 不实现 document persistence、server patch、revision/conflict 或 provider；
- 不改变 `<Handle>`、`DeletableEdge` pulse/glow、节点视觉或浮层几何；
- 不修改 FrameOS route/store；
- 不把 Open Canvas 的 callback、store shape 或 selected flags 复制为 LibTV
  源站事实；
- 不用 routine toast 展示 stale framework event。

## 接力入口

- [`PLAN.md`](PLAN.md)：实施切片、文件边界、fixture、验收、回归与 checkpoint。
- [`../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)：
  长期 routing authority。
- [`../LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](../LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)：
  T0-T5 graph ingress 总边界。
- [`../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)：
  node/edge/primary selection 的相邻权威。
- [`../open-canvas-2026-08-26/LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md`](../open-canvas-2026-08-26/LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md)：
  Open Canvas 到 LibTV 的七层交接。

实施结果见 [`IMPLEMENTATION.md`](IMPLEMENTATION.md)、
[`runtime-audit.json`](runtime-audit.json) 和
[`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)。
