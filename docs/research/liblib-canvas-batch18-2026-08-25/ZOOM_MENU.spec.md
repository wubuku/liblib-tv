# Zoom Menu Specification

## Scope

- **Target files:** `src/components/BottomToolbar.tsx`, `src/store/uiStore.ts`
- **Trigger:** Bottom canvas toolbar percentage button
- **Viewport commands:** provided by `src/app/page.tsx`

## Source-shaped structure

```text
┌────────────────────┐
│ 28               % │
├────────────────────┤
│ 放大           ⌘ + │
│ 缩小           ⌘ - │
│ 适合屏幕       ⌘ 0 │
├────────────────────┤
│ 缩放至50%          │
│ 缩放至100%         │
│ 缩放至800%         │
└────────────────────┘
```

- Approximate width: `188-196px`.
- Anchor: directly above and right-aligned to the percentage trigger.
- The current percent is display state, not a `- / +` segmented control.

## State contract

```ts
interface UIState {
  isZoomMenuOpen: boolean;
  toggleZoomMenu: () => void;
  closeZoomMenu: () => void;
}
```

`isZoomMenuOpen` is included in `closedOverlayState`, so any top-level overlay action and `closeAllPanels` clears it.

## Interaction contract

| Action | Result |
|---|---|
| Trigger | Toggle zoom menu and close other top-level overlays |
| 放大 | `onZoomBy(0.1)`, menu remains open |
| 缩小 | `onZoomBy(-0.1)`, menu remains open |
| 适合屏幕 | `onFitView()`, menu remains open |
| 50/100/800 | `onZoomTo(0.5/1/8)`, menu remains open |
| Escape | `closeAllPanels()` closes menu |
| Outside click | `closeZoomMenu()` |
| Open another overlay | Store mutual exclusion closes menu |

## Stable selectors

- `[data-viewport-menu-trigger="zoom"]`
- `[data-liblib-overlay="zoom-menu"]`
- `[data-zoom-current]`
- `[data-zoom-action="in|out|fit|50|100|800"]`

## Non-goals

- Viewport changes are not graph history.
- No grid command inside this menu.
- No custom wheel/pinch algorithm.
