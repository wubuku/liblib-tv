# LibTV Selected Overlay Positioning Contract

> Scope: the current LibTV standard selected-image state. This is a research contract for later implementation and verification, not authorization to modify `src/`.

## 1. Scope And State Boundary

The standard image state contains exactly two node-linked surfaces:

```text
selected image
├── standard image toolbar above the node
└── image generation/edit panel below the node
```

This contract does not treat every image-toolbar action as the same state. `preview`, `annotate`, `元素编辑`, `旋转` and `图层分离` can replace the standard toolbar/panel or mutate the graph. Their separate evidence is in [`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md).

## 2. Coordinate Definitions

Use one live viewport snapshot for both surfaces:

| Symbol | Meaning |
|---|---|
| `x`, `y` | node flow/world position after adding parent positions when the node is nested |
| `W`, `H` | node flow size used by the source editor |
| `vx`, `vy` | React Flow viewport translation in CSS pixels |
| `z` | live viewport zoom |
| `nodeLeft` | `x * z + vx` |
| `nodeTop` | `y * z + vy` |
| `nodeWidth` | `W * z` |
| `nodeHeight` | `H * z` |
| `nodeCenterX` | `nodeLeft + nodeWidth / 2` |

The current source bundle computes the same shape with minified variables: `eE = nodeLeft`, `ek = nodeTop`, `ej = nodeWidth`, and `p = z`. Do not mix a store zoom, a stale screenshot value and a different DOM node size in one calculation.

## 3. Standard Toolbar Contract

The current production chunk [`0jf40wzwc66-8.js`](https://liblibai-web-static.liblib.cloud/liblibtv_online/static/_next/static/chunks/0jf40wzwc66-8.js) renders the standard host with this positioning shape:

```text
left = nodeLeft + nodeWidth / 2
top = nodeTop - 24 * z - 10
transform = translateX(-50%) translateY(-100%)
```

The `top` value is the host's pre-transform top. Since `translateY(-100%)` lifts the host by its own height:

```text
toolbarBottom = nodeTop - 24 * z - 10
toolbarGap = nodeTop - toolbarBottom = 10 + 24 * z
```

Current live evidence in a `929x874` viewport:

| Zoom | Toolbar | Top gap | Center delta |
|---:|---:|---:|---:|
| `0.282798` | `1092.5x49` | `16.794px` | about `-0.001px` |
| `0.339357` | `1092.5x49` | `18.152px` | about `-0.003px` |
| `0.407229` | `1092.5x49` | `19.778px` | about `0.001px` |
| `0.5` | `1092.5x49` | `22px` | about `0.005px` |

The toolbar width is content-sized (`w-fit`) and currently contains 9 text actions plus annotate, rotate, download and preview icons. The historical `900.5x49` action set is retained only as a dated source snapshot. Full rects and raw values are in [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md) and [`libtv-overlay-multizoom-audit-2026-08-26.json`](../liblib-seedance-2.5-2026-08-25/libtv-overlay-multizoom-audit-2026-08-26.json).

## 4. Standard Bottom Panel Contract

The source panel is centered on the same `nodeCenterX`, remains `660px` wide on screen and is inverse-scaled inside the node:

```text
panelLeft = nodeCenterX - 660 / 2
panelTop = nodeTop + nodeHeight + 16 * z
panelTransform = scale(1 / z)
```

The measured outer panel height is content-state dependent (`191`, `211` or `273.797px` in current evidence). The `16 * z` value is the screen-space gap after the node transform. The clone's `bottom: -17px` is a node-border compensation, not a claim about source CSS.

## 5. State And Lifecycle Rules

| State | Top surface | Bottom surface | Safe conclusion |
|---|---|---|---|
| Standard selected image | `1092.5x49` current toolbar | `660px` panel | use Sections 3-4 |
| Empty annotate | `536x49` dedicated toolbar | standard panel absent | canvas stage overlays node; Escape restores standard state |
| Empty element edit | `272x44` dedicated toolbar | record panel is inside edit mode; standard panel absent | point/box/brush authoring exists; Escape restores standard state |
| Rotate entry | may enter an editor branch, but current shared fixture produced a selected `旋转与镜像` derived node | do not infer | treat as graph-mutation capable until isolated on a disposable fixture |
| Layer separation | dedicated composition editor | task/composition-dependent | do not click on shared research canvas |
| Preview | page-level `fixed` overlay | node surfaces remain behind it | close returns to unchanged selection |
| Empty canvas | no toolbar | no panel | selection clear must unmount both surfaces |

The selected node can leave the DOM at 100% because of source visibility/virtualization while the toolbar host briefly remains. A missing node DOM is not enough to infer that selection state was lost.

## 6. Verification Contract

Any later clone verification should capture node, toolbar, panel and viewport from the same frame and assert:

1. Standard single-image selection produces one toolbar and one panel; switching selection replaces both as a unit.
2. `toolbarCenterX - nodeCenterX` and `panelCenterX - nodeCenterX` stay within the selected tolerance, normally `<= 1px` after DOM rounding.
3. Standard toolbar bottom satisfies `nodeTop - (10 + 24 * zoom)`; bottom panel top satisfies `nodeBottom + 16 * zoom`.
4. Standard toolbar is content-sized for the selected action set and remains screen-sized across zoom; the current source set is `1092.5x49`.
5. Negative x/y and natural React Flow clipping are allowed. Do not recenter or clamp to browser edges.
6. Empty-canvas selection clears both surfaces; active image tools replace the standard state instead of adding a third floating layer.
7. Zoom, pan and selection changes do not change graph node/edge counts; any action that can do so is tested only on a disposable fixture.

## 7. Source Fact / Inference / Clone Decision

### `SOURCE_FACT`

- The current standard host uses node-center `left`, `node-top - 24 * zoom - 10` `top`, and `translateX(-50%) translateY(-100%)`.
- The standard top gap is therefore `10 + 24 * zoom`; the bottom gap is `16 * zoom`.
- Current source standard toolbar is `1092.5x49` and content-sized; source allows edge clipping.
- Active image tools have separate render branches and must not inherit the standard toolbar formula without evidence.

### `INFERENCE`

- React Flow `NodeToolbar offset=16` alone cannot express the current source top contract at every zoom; the clone must either map it deliberately or use an equivalent measured host.
- The source's 100% toolbar residue is a virtualization/update-order case, not proof of a business-state mismatch.

### `CLONE_DECISION` (pending authorization)

- Preserve the clone's top `NodeToolbar` plus node-internal bottom panel architecture.
- Update action set and width before interpreting any remaining visual mismatch.
- Validate the top formula and panel formula from one shared viewport snapshot before adding any new offset or clamp.
- Do not implement rotate/layer-separation graph behavior from this document alone; use the action matrix and a disposable test fixture.

## 8. Evidence Links

- [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md): five-node action set and historical width attribution.
- [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md): live rects, source formula and virtualization boundary.
- [`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md): active-tool replacement and side-effect boundaries.
- [`ImageNode.spec.md`](ImageNode.spec.md) and [`ImageEditPanel.spec.md`](ImageEditPanel.spec.md): current clone component contracts.
- [`LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](../LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md): current coordinate-domain, live/stable viewport, host-resize and generation composition gaps; it does not replace the formulas in this contract.
