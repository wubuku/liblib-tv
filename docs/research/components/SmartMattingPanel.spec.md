# SmartMattingPanel Specification

## Purpose

`src/components/SmartMattingPanel.tsx` 是 ready-video 节点的 selected-node lower toolbar，用于从主体编辑菜单进入智能抠像提交态。组件只拥有可视面板和提交/取消命令；graph transaction 由 `VideoNode` 与 `canvasStore.createSmartMatting` 协作完成。

## Evidence Boundary

Batch 30 的 source bundle 证据确认了主体编辑菜单顺序、时长 guard、智能抠像面板、request-shaped metadata 和 output graph 方向。它不证明真实服务已接通，也不提供成功媒体、透明通道或计费结果。

| 层级 | 已确认内容 | 边界 |
|---|---|---|
| `SOURCE_FACT` | `主体消除 / 主体修改 / 主体替换 / 智能抠像` 顺序；智能抠像进入节点下方面板；provider/model/task/format vocabulary 和 pending output 关系 | 不包含真实任务响应、媒体结果或永久计价 |
| `CLONE_FACT` | `NodeToolbar` bottom anchor、`16px` offset、measured-width clamp、disabled/spinner、pending node/edge/history transaction | 只在本地 Zustand graph 中生效 |
| `CLONE_DECISION` | output slot search、pending placeholder、未计算 power 显示 `--` | 不声明为源站完整 resolver 或算力值 |

完整工作流合同见 [`SMART_MATTING_WORKFLOW.spec.md`](../liblib-canvas-batch30-2026-08-25/SMART_MATTING_WORKFLOW.spec.md)。

## Ownership And Visibility

```text
ready VideoNode
  -> single selected node
  -> activeTool === "matting"
  -> SmartMattingPanel visible
```

- 普通 `VideoGenerationPanel` 在 matting active tool 期间卸载。
- 多选、节点未选中或非 ready 状态不显示本面板。
- `VideoNode` 从 React Flow internal node 读取 measured width；缺失时回退到 `512`。
- 面板不拥有 `activeTool` 状态，只通过 `onCancel` 和 `onGenerate` 回调请求转换。

## Geometry

| Property | Contract |
|---|---|
| React Flow owner | `NodeToolbar` |
| position | `Position.Bottom` |
| offset | `16px` |
| alignment | center |
| width | `clamp(round(nodeWidth), 360px, 560px)` |
| current `512px` node result | `512x48px` |
| interaction classes | `nodrag nopan` |

The measured node and toolbar own screen anchoring. Do not add a decorative absolute overlay or reuse page-level modal coordinates.

## Visual Structure

```text
SmartMattingPanel
├── close
├── 智能抠像
├── power: sparkle + --
└── generate
    ├── idle: ArrowUp
    └── submitting: LoaderCircle
```

- Pointer/click propagation is stopped at the panel shell so controls do not start node drag or canvas pan.
- Close and generate are disabled while submitting.
- The panel has no prompt input, resolution selector or result preview.

## State Transitions

| Event | UI result | Graph result |
|---|---|---|
| open from picture-edit menu | generator replaced by matting panel | none |
| close while idle | matting panel removed, ordinary generator restored | none |
| generate | spinner and disabled commands | one pending output and direct source edge through one store transaction |
| submit completion in prototype | panel closes, source remains selected | output metadata remains in graph |
| undo/redo | component follows restored graph/tool state | transaction is atomic in Batch 30 contract |

## Graph Handoff

The component must not construct nodes or edges directly. `canvasStore.createSmartMatting` owns:

- source absolute-position resolution;
- pending `512x288` video creation;
- direct source edge;
- provider/model/task/format metadata;
- deterministic repeated-output placement;
- one history snapshot and redo clearing.

Output media remains a placeholder and must not reuse the source poster or claim a generated alpha channel.

## Stable Selectors

- `[data-smart-matting-panel]`
- `[data-smart-matting-close]`
- `[data-smart-matting-power]`
- `[data-smart-matting-generate]`
- `[data-smart-matting-submitting]`
- `[data-smart-matting-output]`

Metadata selectors on the output node are defined by the Batch 30 workflow contract.

## Verification Status

`scripts/verify-liblib-batch30.py` records focused coverage for:

- menu order and hover timing;
- duration guard without graph mutation;
- `512x48` panel, node center and `16px` gap;
- close-to-generator transition;
- submitting/disabled state;
- output metadata, edge, selection and one-step undo/redo;
- repeated output non-overlap, multi-selection hiding and mobile natural clipping.

The recorded pass is a bounded clone contract. Re-run the verifier when the panel, `VideoNode` active-tool lifecycle or store transaction changes.

## Future Gate

Real task submission requires explicit backend/provider authorization and new evidence for request/response, progress, failure, cancellation, credits and result media. Do not infer those contracts from the pending local graph.
