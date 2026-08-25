# LibTV Minimap Specification

## Scope

- **Target:** `MiniMap` in `src/app/page.tsx`
- **Styling:** `src/app/globals.css`
- **Trigger:** `BottomToolbar` button with label `显示缩略图` / `隐藏缩略图`
- **State:** `uiStore.showMinimap`

## Geometry contract

Desktop `929x874`:

```text
left: 152px from the React Flow canvas
bottom: 54px
width: 150px
height: 110px
```

The React Flow canvas begins after the 240px asset drawer. Keeping the minimap's left offset relative to that canvas makes it follow the bottom toolbar when the drawer opens.

Compact `390x844`:

- width and height remain `150x110px`;
- horizontal position remains fully visible;
- bottom offset is increased so the minimap sits above both bottom toolbars.

## Visual contract

- panel background: `#262626`;
- border: subtle white alpha;
- radius: `10px`;
- node fill: medium gray;
- node stroke: slightly lighter gray;
- viewport outside mask: dark translucent overlay;
- viewport outline: visible muted gray;
- no labels, edges or thumbnails.

## Interaction contract

| Action | Result |
|---|---|
| Click minimap trigger while hidden | Show minimap and set trigger `aria-pressed=true` |
| Click trigger while visible | Hide minimap and set trigger `aria-pressed=false` |
| Open asset drawer | Minimap remains visible and follows the React Flow canvas/trigger |
| Pan or zoom canvas | React Flow updates the viewport outline |

## Non-goals

- No minimap click-to-jump.
- No minimap drag-to-pan.
- No minimap wheel zoom.
- No claim about original animation timing.

## Stable selectors

- `[data-liblib-minimap]`
- `[data-testid="rf__minimap"]`
- `button[aria-label="显示缩略图"]`
- `button[aria-label="隐藏缩略图"]`

