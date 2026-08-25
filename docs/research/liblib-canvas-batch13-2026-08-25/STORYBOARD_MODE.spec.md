# Storyboard Mode Specification

## Target

- Component: `src/components/StoryboardBoard.tsx`
- Route: `/`
- Mode trigger: `TopNavBar` 的“分镜”按钮
- Related lifecycle: `uiStore.editorMode` 与 `uiStore.isAgentOpen`

## Source-shaped layout

```text
┌──────────────────────────────────────────────────────────────┐
│ 关键元素 · 全部 │             故事板              │ Agent     │
│ 图片            │ 图片列                         │           │
│  缩略资源       │ 视频列                         │           │
│ 文本            │                                │           │
│  剧本           │                                │           │
└──────────────────────────────────────────────────────────────┘
```

- 左栏：约 `150px`，展示当前画布的图片和脚本关键元素。
- 中栏：可横向滚动的故事板区域，按“图片 / 视频”分列。
- 右栏：由页面外层的 `AgentDrawer` 提供，宽度 `340px`。

## Data projection

| Source node type | Key elements | Storyboard |
|---|---:|---:|
| `image` | yes | yes |
| `script` | yes | no |
| `video` | no | yes |
| other | no | no |

Images use `data.imageUrl`, videos use `data.posterUrl` when present and otherwise a failed/empty state. Node labels prefer `filename`, then `title`.

## Interactions

| Action | Effect |
|---|---|
| Click image/script/video card | `canvasStore.selectNode(node.id)` and mark the card pressed |
| Click “返回工作台” | `uiStore.setEditorMode("workbench")`; selected node remains selected |
| Switch active canvas | Rebuild all groups from the new active canvas |
| Empty group | Show explicit local empty state |

The selection and return command are local prototype decisions. No claim is made about the source site's exact click-through destination.

## Stable selectors

- `[data-storyboard-board]`
- `[data-storyboard-key-elements]`
- `[data-storyboard-key-group="image"]`
- `[data-storyboard-key-group="text"]`
- `[data-storyboard-column="image"]`
- `[data-storyboard-column="video"]`
- `[data-storyboard-card="<node-id>"]`
- `[data-storyboard-return]`

