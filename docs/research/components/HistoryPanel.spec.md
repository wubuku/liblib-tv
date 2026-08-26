# HistoryPanel Specification

## Purpose

`src/components/HistoryPanel.tsx` 是 LibTV 工作台的历史资产 Modal。当前 clone 提供图片/视频/音频 Tab、缩略图缩放、批量模式、收藏和结果动作的本地 UI 状态，但不连接远端历史服务。

## Evidence Boundary

| 层级 | 已确认内容 | 不能推出的内容 |
|---|---|---|
| `SOURCE_FACT` | 2026-08-25、`929x874` 视口中，Modal 使用 `90vw x calc(100vh - 160px)`，采样边界约 `(46.45,80,836.09,714)`；有图片/视频/音频 Tab、100% 缩放、时间降序、批量操作和 3 张 `144x144` 图片 | 远端分页、筛选请求、批量动作、收藏/查看/使用/下载的 API 和 graph 副作用 |
| `CLONE_FACT` | 当前固定 3 张本地图片，视频/音频为空；缩放为 `50..150%`，收藏和 batch mode 是组件本地状态 | clone 数据来自用户账户或当前 canvas history |
| `CLONE_DECISION` | 排序按钮和查看/使用/下载按钮无业务动作；batch mode 只显示未选中的方框；日期与数量固定 | 这些占位交互不代表源站完整行为 |

证据入口：[`panel-audit.json`](../liblib-live-2026-08-25/panel-audit.json) 和 [`BATCH_1_PANELS.md`](../liblib-live-2026-08-25/BATCH_1_PANELS.md)。

## Structure

```text
HistoryPanel
├── backdrop
└── modal
    ├── header: 历史资产 / zoom / close
    ├── controls
    │   ├── 图片历史 / 视频历史 / 音频历史
    │   ├── 时间降序
    │   └── 批量操作
    └── results
        ├── date group
        ├── thumbnail cards
        │   ├── watermark / badge
        │   ├── favorite
        │   └── 查看 / 使用 / 下载
        └── end or empty state
```

## Geometry

Source snapshot at `929x874`:

| Property | Value |
|---|---|
| modal width | `min(90vw,1600px)`; sampled `836.09px` |
| modal height | `calc(100vh - 160px)`; sampled `714px` |
| position | sampled `x=46.45`, `y=80` |
| radius | `16px` |
| border | `0.5px solid rgb(54,54,54)` |
| source thumbnails | `144x144`, `12px` horizontal gap in the sampled first row |

Clone keeps the same high-level width/height formula, adds `min-height: 520px`, viewport-safe max height and a two-row mobile controls layout. The latter are clone responsive decisions.

## Local State

- `activeTab` defaults to `image`; video/audio render explicit empty states.
- Zoom starts at `100`, changes in `10` point steps and clamps to `50..150`.
- Zoom changes only thumbnail inline width/height; it is independent of React Flow viewport zoom.
- `batchMode` only toggles selection affordances; no item selection collection or batch command exists.
- `favorites` is an in-memory array toggled per image card and resets when the panel remounts.
- “时间降序” does not change order.
- “查看”“使用”“下载” currently do not preview, create graph nodes or write files.
- Backdrop/close and `uiStore.activePrimaryPanel === "history"` follow shared overlay lifecycle.

## Data Boundary

- Static clone media: `public/images/liblib-panels/history-01.webp` through `history-03.webp`.
- The panel does not read `canvasStore` undo history, active-canvas assets, generation tasks or a user account.
- `HistoryPanel` asset history and `canvasStore` graph undo/redo history are separate concepts and must not share one state model.

## Stable Selector

```html
data-liblib-overlay="primary:history"
```

Controls currently use accessible names; add narrower selectors only when their state transitions become real contracts.

## Verification Status

- Source screenshot: `liblib-original-history-2026-08-25.png`.
- Clone screenshot: `liblib-clone-batch1-history-2026-08-25.png`.
- Batch 1 recorded desktop/mobile geometry and no horizontal text overflow.
- Batch 11 verifies top-level overlay mutual exclusion and cleanup.
- No focused verifier proves thumbnail scaling bounds, favorite lifecycle, batch selection or real asset actions.

## Future Gate

Before implementing real history behavior, extract current source pagination, asset identity, media-type filters, sort options, preview lifecycle, use-to-canvas transaction, download behavior and batch commands. Define whether a command mutates account state, graph state, both or neither before coding.
