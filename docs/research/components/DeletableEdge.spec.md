# DeletableEdge Specification

> Custom React Flow edge component registered as `default` in `src/app/page.tsx`.

## Overview

- **Target file:** `src/components/nodes/DeletableEdge.tsx`
- **Visual reference:** [Original site screenshot](../../design-references/canvas-desktop-full.png)
- **Interaction model:** Hover-triggered pulse effect + drag/click to delete

## Purpose

Replicates the original LibTV's edge hover effect precisely:

1. **Base edge** is a thin gray line.
2. **On hover OR select**: the edge becomes thicker, glows cyan, and shows 3 light segments flowing along the path.
3. **Midpoint shows a scissors delete button** — click it to remove the edge.

The edge hover effect was extracted from the original site by walking its live DOM through Playwright; the design is faithful to that extraction rather than guessed.

## DOM Structure

```
<g className="react-flow__edge">  ← React Flow edge wrapper
  <defs>
    <filter id="edge-flow-filter-{id}">  ← Gaussian blur + flood + composite + merge
      <feGaussianBlur stdDeviation="6" />     <!-- outer glow -->
      <feFlood floodColor="rgba(120,200,255,0.6)" />
      <feComposite in="floodOuter" operator="in" />  <!-- mask blur by flood -->
      <feGaussianBlur stdDeviation="2" />     <!-- inner glow -->
      <feFlood floodColor="rgba(180,230,255,0.85)" />
      <feComposite in="floodInner" operator="in" />
      <feMerge>
        <feMergeNode in="glowOuter" />
        <feMergeNode in="glowInner" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>

  <BaseEdge ... />  <!-- The base path stroke (color changes on hover) -->

  <path />  <!-- Invisible 40px hit-area for hover detection -->

  <g filter="url(#edge-flow-filter-{id})">
    <PulsePath d=... phase={0} />
    <PulsePath d=... phase={1} />
    <PulsePath d=... phase={2} />
  </g>

  <EdgeLabelRenderer>
    <button data-edge-delete={id}>
      <!-- scissors icon, 8×8 paths in 32×32 dark circle -->
    </button>
  </EdgeLabelRenderer>
</g>
```

## Computed Styles

### Base path (when idle)

| Property | Value |
|----------|-------|
| `stroke` | `#86909c` |
| `stroke-width` | `2` |
| `opacity` | `1` |
| `transition` | `stroke 200ms, stroke-width 200ms, opacity 200ms` |

### Base path (when active: hover or selected)

| Property | Value |
|----------|-------|
| `stroke` | `#c0c8d0` (light gray-blue, matching `--canvas-edge-hover`) |
| `stroke-width` | `4` |
| `opacity` | `0.45` (dimmed so the flow segments stand out) |
| `filter` | `drop-shadow(0 0 4px rgba(100,180,255,0.5))` |

### Flow segments (3, staggered)

Each flow segment path:

| Property | Value |
|----------|-------|
| `stroke` | `url(#edge-flow-grad-{id}-{phase})` |
| `stroke-width` | `6` |
| `stroke-linecap` | `round` |
| `stroke-linejoin` | `round` |
| `pathLength` | `100` (normalized — animations use 0-100% values) |
| `stroke-dasharray` | `"20 80"` (20% visible segment + 80% gap) |
| `style.animation` | `<unique-edge-flow-kf> 1.6s linear infinite` |
| `style.animationDelay` | `${-phase * 0.53}s` (3 segments offset by ~530ms each) |

Each segment's `<linearGradient>` (one per segment):

```xml
<linearGradient id="edge-flow-grad-{id}-{phase}" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%" stopColor="rgba(180,220,255,0)" />
  <stop offset="50%" stopColor="rgba(180,220,255,1)" />
  <stop offset="100%" stopColor="rgba(180,220,255,0)" />
</linearGradient>
```

### Pulse keyframe (injected into `document.head`)

```css
@keyframes edge-flow-kf-{edgeId}-{phase} {
  from { stroke-dashoffset: 100; }
  to   { stroke-dashoffset: 0; }
}
.edge-flow-kf-{edgeId}-{phase} {
  animation: edge-flow-kf-{edgeId}-{phase} 1.6s linear infinite;
}
```

### Delete button

| Property | Value |
|----------|-------|
| Size | 32×32 |
| `position` | absolute at `translate(-50%, -50%)` of `(labelX, labelY)` (edge midpoint) |
| Background | `#1c1d29` |
| Border | `1px solid #3a3d4a` |
| Icon | White scissors icon (two circles + two diagonal strokes), 16×16 |
| `opacity` | `0` → `1` when `isActive` is true (via className toggle) |
| `transition` | `opacity 0.15s, transform 0.15s` |

The button is rendered via `EdgeLabelRenderer` so it's positioned relative to the React Flow viewport (and can render outside the SVG).

## States & Behaviors

| State | Trigger | Effects |
|-------|---------|---------|
| Idle | — | Default base path visible; no flow segments; delete button hidden. |
| Hover | `onMouseEnter` on hit-area path → `setHovered(true)` | Base path becomes thick + cyan + dimmed; flow segments appear with staggered animation; delete button fades in. Sets `document.body.dataset.hoverEdge = id` (legacy, not used elsewhere). |
| Selected | `selected` prop from React Flow | Same visual as hover (light glow, flow, delete button). |
| Hover + drag interaction | hover on hit-area path triggers `onMouseEnter`; React Flow's overlay-path hover detection still works simultaneously | Visual effects don't conflict with React Flow's edge hover/select. |
| Click delete button | `onClick` on `[data-edge-delete]` button | Dispatches `CustomEvent("delete-edge", { detail: { id } })`. `page.tsx` listens and calls `canvasStore.removeEdge(id)`. The edge disappears immediately. |

## CSS-in-JS Keyframe Injection

Each edge injects its own `<style>` tag into `document.head` (with id `edge-flow-kf-{edgeId}-{phase}`). Cleanup hook removes the style tag on unmount.

**Why per-edge?** The `animation` CSS property requires a fixed name. Each edge has 3 segments with different `animationDelay` values, so we need 3 distinct keyframe names per edge. A per-instance name is the simplest way to scope the keyframe to one edge.

**Alternative considered**: a single shared keyframe with a CSS variable for delay. Rejected because CSS `@keyframes` rules can't be parameterized by CSS variables easily.

## Connection drag works

The handle (not the edge) is the drag source. See `globals.css` `/* Node Handle */` section. Users drag from `<Handle>` to create the connection — clicking on an edge does NOT start a drag (because we don't subscribe to `onEdgeMouseDown`). The handle uses React Flow's native magnet + connection-line preview.

## Files Referenced

- `src/components/nodes/DeletableEdge.tsx` — implementation
- `src/app/globals.css` — base path / global transition styling
- `src/app/page.tsx` — `onConnect` handler + `delete-edge` event listener
- `src/store/canvasStore.ts` — `removeEdge` action
