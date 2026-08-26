# StoryboardBoard Specification

## Purpose

`src/components/StoryboardBoard.tsx` 是 LibTV `/` 路由在 `editorMode === "storyboard"` 时替换 React Flow 主体的故事板投影视图。它读取当前 active canvas，将图片、视频和脚本节点投影为关键元素与故事板卡片；它不拥有第二份 graph。

## Evidence Boundary

| 层级 | 已确认内容 | 不能推出的内容 |
|---|---|---|
| `SOURCE_FACT` | 2026-08-25 原站截图显示左侧“关键元素 · 全部”、中部“故事板”的图片/视频列，以及右侧并列 Agent | 卡片点击目的、排序/展开、拖拽、发布和远端任务 |
| `CLONE_FACT` | 当前组件从 active canvas 投影节点，点击卡片调用 `selectNode`，返回工作台保留 selection；Batch 13 有专项 Playwright | clone 卡片交互等同于源站深层导航 |
| `CLONE_DECISION` | `Lib Image / Lib Video` 标签、失败卡、显式“返回工作台”和内部横向滚动 | 这些不是完整源站 story authoring contract |

专项 source screenshot 解释见 [`SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch13-2026-08-25/SCREENSHOT_ANALYSIS.md)，原始 Batch 合同见 [`STORYBOARD_MODE.spec.md`](../liblib-canvas-batch13-2026-08-25/STORYBOARD_MODE.spec.md)。

## Mode Lifecycle

```text
TopNavBar: 分镜
  -> uiStore.setEditorMode("storyboard")
  -> close other top-level overlays
  -> isAgentOpen = true
  -> page mounts StoryboardBoard instead of ReactFlow

返回工作台
  -> uiStore.setEditorMode("workbench")
  -> isAgentOpen = false
  -> page remounts ReactFlow for the same active canvas
```

- Mode switching does not create, delete or reorder graph nodes/edges.
- Selected node identity remains in `canvasStore` across the round trip.
- Agent is rendered by the page outside `StoryboardBoard`; do not mount a second Agent inside the component.
- LibTV mode state remains in `uiStore`; it must not use FrameOS route/store state.

## Data Projection

| Node type | Key elements | Storyboard column | Media source |
|---|---:|---:|---|
| `image` | yes, 图片 group | yes, 图片 | `data.imageUrl` |
| `script` | yes, 文本 group | no | document icon |
| `video` | no | yes, 视频 | `data.posterUrl`, otherwise failed/empty state |
| other | no | no | not projected |

- The component finds `canvases.find(canvas.id === activeCanvasId)` on every render.
- Missing active canvas behaves like an empty node list.
- Labels prefer `data.filename`, then `data.title`, then node type/`未命名节点`.
- Dimensions display only when both numeric `data.width` and `data.height` exist.
- Reference thumbnails accept only string entries and show at most three.
- Counts derive from projected nodes, not from saved constants.

## Structure

```text
StoryboardBoard
├── key elements rail (148px)
│   ├── 图片 group
│   └── 文本 group
└── scrollable storyboard body
    ├── header / 返回工作台
    ├── 图片 column (204px)
    └── 视频 column (204px)

AgentDrawer (page sibling, 340px source-shaped width)
```

The board uses internal horizontal/vertical scrolling. At `390x844`, content may extend inside the board but must not create document-level horizontal overflow.

## Selection Contract

- Every key-element and media card carries the source `node.id` in `data-storyboard-card`.
- Clicking a card calls `canvasStore.selectNode(node.id)`.
- A selected card exposes `aria-pressed="true"` and cyan border/background feedback.
- The same node can appear in both key elements and the image storyboard column; both projections read the same `selectedNodeId`.
- Selection in storyboard mode is graph selection context, not a new storyboard-specific identity.

## Empty And Failed States

- Empty key groups: `暂无图片元素` / `暂无文本元素`.
- Empty media columns: `当前画布暂无图片素材` / `当前画布暂无视频素材`.
- Video without poster uses the local `生成失败` presentation.
- These states are clone prototype copy; they do not describe remote task retry semantics.

## Stable Selectors

- `[data-storyboard-board]`
- `[data-storyboard-key-elements]`
- `[data-storyboard-key-group="image"]`
- `[data-storyboard-key-group="text"]`
- `[data-storyboard-column="image"]`
- `[data-storyboard-column="video"]`
- `[data-storyboard-card="<node-id>"]`
- `[data-storyboard-return]`

## Verification Status

`scripts/verify-liblib-batch13.py` records coverage for:

- active-canvas image/script/video counts;
- card-to-node selection;
- workbench round trip with selection preservation;
- switching to an empty canvas without stale cards;
- `390x844` internal overflow behavior;
- desktop/empty/mobile screenshots and zero console errors.

Batch 11 separately protects mode/Agent/overlay lifecycle. These recorded passes validate the bounded clone projection, not source ordering, editing or publication workflows.

## Future Gate

Before adding drag/sort/edit/publish behavior, inspect the current source for storyboard item identity, order persistence, graph relation, Agent context and mutation history. Do not create a second storyboard store or duplicate active-canvas nodes merely to support visual ordering.
