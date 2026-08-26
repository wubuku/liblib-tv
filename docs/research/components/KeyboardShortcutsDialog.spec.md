# KeyboardShortcutsDialog Specification

## Purpose

`src/components/KeyboardShortcutsDialog.tsx` 是 LibTV 工作台底部“快捷键”入口上方的帮助面板。它只展示命令说明并提供关闭命令；它本身不注册、执行或验证任何键盘快捷键。

## Evidence Boundary

| 层级 | 已确认内容 | 不能推出的内容 |
|---|---|---|
| `SOURCE_FACT` | 2026-08-25、`929x874` 视口中，面板约 `905x446.5`、位于 `(12,354.5)`、圆角 `16px`、四列、无阻断画布的全屏遮罩 | 文案对应的快捷键监听器仍全部存在，Windows/macOS 映射或不同选中态下的可用性 |
| `CLONE_FACT` | 当前面板是固定四组常量，支持 close、共享 overlay 生命周期和响应式 2/1 列滚动 | 帮助行已经与 `page.tsx`/React Flow 实际键盘处理一致 |
| `CLONE_DECISION` | `cmd`/`ctrl` 都渲染为 Command 图标；clone 缺少数个 source rows 并增加 Windows 重做 | 这些差异不是当前源站合同 |

Source DOM/text snapshot 见 [`panel-audit.json`](../liblib-live-2026-08-25/panel-audit.json)，几何与 clone 截图记录见 [`BATCH_1_PANELS.md`](../liblib-live-2026-08-25/BATCH_1_PANELS.md)。

源站帮助文案、clone 帮助行、普通工作台 handler、React Flow gesture 和局部 Escape 优先级的完整对照见 [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](../LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)。

## Geometry And Topology

Source snapshot at `929x874`:

| Property | Value |
|---|---|
| panel | `905x446.5` |
| sampled position | `x=12`, `y=354.5` |
| border | `0.5px solid rgb(54,54,54)` |
| radius | `16px` |
| padding | `24px` |
| content | four columns, `20px` gap |
| backdrop | none; canvas remains visible/non-blocked |

Current clone:

- `bottom: 73px`, centered horizontally, `905x447px` desktop;
- `max-width: calc(100vw - 24px)`;
- mobile moves to `bottom: 109px`, keeps `447px` target height and allows internal vertical scroll;
- grid collapses from four columns to two, then one;
- the small rotated pointer is clone-calibrated to the current bottom toolbar.

The dated source audit confirms desktop geometry only. Clone mobile offsets are responsive decisions verified against local layout, not source mobile facts.

## Overlay Lifecycle

- `isOpen === false` returns `null`.
- Opening is owned by `uiStore.isShortcutsPanelOpen` through `LeftSidebar`.
- The visible shell exposes `data-liblib-overlay="shortcuts"`.
- Close button invokes `onClose` and has no graph side effect.
- `Escape`, opening another top-level overlay and storyboard mode transition close it through the shared Batch 11 lifecycle.
- There is no backdrop or outside-click owner inside this component.

## Source Command Snapshot

The 2026-08-25 source text contains the following visible groups. This is a dated help-text inventory, not proof that each command listener was exercised.

| Group | Source-visible commands |
|---|---|
| 创作 | 成组 `G`; 合并分镜组 `Option+G`; 解组 `Shift+G`; 连线 `L`; 复制节点和连线 `D`; 生成 `Enter`; 新建节点 `Tab`; 节点复制 `Option+拖动节点`; 创建副本 `Option+拖动` |
| 缩放 | 放大; 缩小; 适应画布 `0`; 触控板; 鼠标 |
| 移动画布 | 键盘 `Space`; 触控板; 鼠标; 移动 `V`; 抓手工具 `H`; 整理画布 `Option+Shift+F` |
| 其他 | 撤销 `Z`; 重做 `Shift+Z`; 删除 |

Modifier glyphs are normalized in this table for readability; the raw audit preserves the exact text sequence.

## Current Clone Command Snapshot

| Group | Current clone rows | Known difference |
|---|---|---|
| 创作 | 成组, 解组, 复制节点和连线, 新建节点, 删除 | missing 合并分镜组、连线、生成、节点复制、创建副本; 删除 moved from source “其他” |
| 缩放 | 放大, 缩小, 适应画布, 触控板, 鼠标 | clone adds explicit `cmd` to zoom rows |
| 移动画布 | 键盘, 触控板, 鼠标, 移动, 抓手工具, 整理画布 | high-level set matches snapshot; modifiers are clone formatting |
| 其他 | 撤销, 重做, 重做（Windows） | clone adds a Windows-specific row and omits source 删除 placement |

The dialog data is component-local. Updating it does not add keyboard behavior. Conversely, adding a listener without updating the dialog creates discoverability drift.

## Rendering Rules

- Four section titles use cyan text.
- Each command row separates label from keycaps/gesture icon.
- `cmd` and `ctrl` currently both render the Lucide `Command` icon; this is a clone limitation, especially for the Windows row.
- `hand` and `mouse` are explanatory visuals, not interactive controls.
- Labels use `white-space: nowrap`; compact layouts rely on the single-column/scroll fallback rather than shrinking text.
- The close icon is the only command inside the panel.

## Stable Selectors

```html
data-liblib-overlay="shortcuts"
```

There are no row-level selectors. If shortcut behavior becomes a tested domain, add stable command IDs shared by help rows and key handlers rather than selecting translated labels.

## Verification Status

- Source screenshot: `liblib-original-shortcuts-2026-08-25.png`.
- Clone screenshot: `liblib-clone-batch1-shortcuts-2026-08-25.png`.
- Batch 1 records desktop `905x447` and mobile `366x447` bounds without visible text overflow.
- Batch 11 verifies open, mutual exclusion and `Escape` cleanup.
- No focused verifier compares every source command row to the clone or proves that each displayed key executes the named action.

## Future Gate

The first static inventory of actual key handlers, React Flow defaults and platform-specific help drift is now recorded in the runtime crosswalk. Before changing the list or handlers, re-inspect the current source help panel with a disposable fixture, especially `Option+G`, `L`, `Enter`, `Option+drag`, `V/H` and duplicate semantics. A future typed `ShortcutCommand` registry should only be introduced when it can drive both execution and display without coupling LibTV to FrameOS shortcuts. Code changes still require explicit authorization.
