# ToolboxPanel Specification

## Purpose

`src/components/ToolboxPanel.tsx` 是 LibTV 工作台底部主工具条打开的预设工具面板。它负责浏览 source-derived 工具卡和展示本地“使用”反馈，不负责执行真实模板任务。

## Evidence Boundary

| 层级 | 已确认内容 | 不能推出的内容 |
|---|---|---|
| `SOURCE_FACT` | 2026-08-25、`929x874` 视口中，面板为 `480x460`、位于 `(160,341)`、圆角 `12px`、三列、25 个预设；首行媒体卡为 `141x141` | 当前线上预设仍是同一集合、分类下拉语义、点击“使用”后的 graph/task 行为 |
| `CLONE_FACT` | 当前组件使用 25 个本地化素材和 source-derived 标题，支持滚动、hover 和单个本地 used state | 真实模板安装、任务提交、账户同步或持久化 |
| `CLONE_DECISION` | 桌面固定在主工具条上方；窄屏限制到 viewport 并上移避让双排工具条 | 这些窄屏数值不是 LibTV 移动端源站测量 |

原始结构和媒体 URL 见 [`panel-audit.json`](../liblib-live-2026-08-25/panel-audit.json)，一次性解释见 [`BATCH_1_PANELS.md`](../liblib-live-2026-08-25/BATCH_1_PANELS.md)。

## Structure

```text
ToolboxPanel
├── header
│   ├── 我的工具箱
│   ├── info command
│   ├── category trigger
│   └── close
└── scroll area
    └── 3-column preset grid
        ├── 1:1 preview
        ├── hover action
        └── two-line title
```

## Geometry

Source snapshot at `929x874`:

| Property | Value |
|---|---|
| panel | `480x460` |
| position | `x=160`, `y=341` |
| background | `rgb(38,38,38)` |
| radius | `12px` |
| bottom padding | `12px` |
| columns | `3` |
| first-row preview | `141x141` |

Clone responsive rules:

- desktop: `bottom: 73px`, horizontal center relative to the primary toolbar calibration;
- mobile: `bottom: 109px`, `left: 50%`, `max-width: calc(100vw - 24px)`;
- content scrolls vertically without moving the header;
- the responsive offsets are clone calibration, not source facts.

## State And Commands

- Opening is owned by `uiStore.activePrimaryPanel === "toolbox"`.
- Opening another top-level overlay or pressing `Escape` closes the panel through the shared overlay lifecycle.
- Close sets the primary panel to `null` and does not mutate graph state.
- Hover reveals the action layer for a card.
- Clicking `使用` stores one local `usedPresetId`; only that card shows `已使用`.
- The info and category controls currently have no expanded state or business side effect.
- Closing/reopening remounts the component and clears local used state.
- No action consumes credits, creates a node, changes history or submits a remote task.

## Assets

- Preview assets live under `public/images/liblib-panels/toolbox-*.webp`.
- The source URLs and natural sizes remain in `panel-audit.json` and the panel asset manifest.
- Localized assets are prototype evidence material; they are not a remote preset API contract.

## Stable Selector

```html
data-liblib-overlay="primary:toolbox"
```

There are no card-level test selectors. Tests should prefer accessible names until a real card state machine requires a stable selector contract.

## Verification Status

- Source screenshot: `liblib-original-toolbox-2026-08-25.png`.
- Clone screenshot: `liblib-clone-batch1-toolbox-2026-08-25.png`.
- Batch 11 verifies top-level overlay mutual exclusion and `Escape` cleanup.
- No current focused verifier proves all 25 titles, category behavior or a real “use preset” transaction.

## Future Gate

Before implementing a real preset workflow, re-inspect the current source for category state, preset identity, input requirements, graph placement, task submission and result lifecycle. Do not extend `usedPresetId` into a graph transaction without that evidence and explicit coding authorization.
