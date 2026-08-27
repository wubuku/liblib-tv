# LibTV Viewport, Coordinate And Gesture Static Audit

> Status: `STATIC_AUDIT_COMPLETE` / `DESIGN_NOT_YET_FORMALIZED` / `RUNTIME_PARTIAL` / `SOURCE_PARITY_PARTIAL`.
>
> Scope: fixed Open Canvas viewport/coordinate/placement methods and counterexamples, plus the current ordinary LibTV clone viewport, gesture and placement owners.
>
> Clone baseline: `e0b8fad`. Open Canvas baseline: `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> Authorization boundary: documentation only. This audit does not authorize changes to `src/`, tests, FrameOS, Director runtime, either submodule or a source website.

## 1. Executive Conclusion

The repository already knows the exact selected-image toolbar/panel formulas and already has a bounded V/H/Space navigation specification. The remaining cross-cutting gap is not another CSS offset. It is the absence of one authority for coordinate conversion, viewport lifecycle, gesture ownership and placement intent across all entry points.

The static audit establishes six conclusions:

1. A canvas prototype needs at least `CLIENT`, `CONTAINER_LOCAL`, `FLOW_WORLD`, `NODE_LOCAL`, `SCREEN_SIZED_OVERLAY` and `MEDIA_NORMALIZED` domains. Values from different domains cannot be combined because they are all represented as plain `{x,y}`.
2. Open Canvas demonstrates a useful split between live viewport during pan/zoom and persisted viewport at move end. It also demonstrates a useful dual-anchor menu model: screen placement is clamped for the menu while graph placement preserves the original flow point.
3. Open Canvas is not a correctness template as a whole. Its viewport normalization accepts non-finite/out-of-range values, narrow-container menu clamp can become negative, panning visual state lacks pointer-cancel/blur cleanup, and multi-file drop mutates sequentially.
4. The clone's highest-confidence visible placement defect is `addNode()` using `window.innerWidth/innerHeight` instead of the actual React Flow container and its conversion API. Asset panel/layout changes can therefore move the visible canvas center without changing the computed add point.
5. The clone's V/H/Space state machine is stronger than the fixed Open Canvas middle/right-button visual state: temporary pan clears on keyup, window blur and document visibility change. This behavior should be preserved.
6. The clone has several current-state races already named by other contracts: viewport, organize, drag and connection transients lack a canvas generation owner; demo responsive bootstrap can overwrite a stored viewport. The new formal contract must compose those authorities rather than create a second lifecycle model.

At audit completion, the recommended next document was a formal contract with fixture `LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` and verifier `LIBTV-VR-020`. That follow-up is now complete in [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md); this dated audit remains the fixed-fact inventory.

## 2. Evidence Discipline

| Label | Meaning in this audit |
|---|---|
| `OPEN_CANVAS_FACT` | directly visible in fixed upstream source |
| `CLONE_FACT` | directly visible in clone baseline source/history docs |
| `RECORDED_RUNTIME` | already supported by a bounded batch verifier or screenshot |
| `INFERENCE` | engineering implication supported by fixed facts, not source parity |
| `CLONE_DECISION_CANDIDATE` | conservative proposal for a future formal contract |
| `SOURCE_UNKNOWN` | LibTV source behavior is not established and must not be filled by Open Canvas |

This document does not infer current LibTV source behavior from Open Canvas. It also does not treat a helper name such as `getViewportCenterPosition` as proof that the returned point is the center of the user's visible canvas.

## 3. Coordinate Domain Taxonomy

### 3.1 Required domains

| Domain | Origin and unit | Typical values | Valid owner |
|---|---|---|---|
| `CLIENT` | browser visual viewport top-left, CSS px | `event.clientX/Y`, DOM rect | current browser event/frame |
| `CONTAINER_LOCAL` | React Flow host top-left, CSS px | absolute menu `left/top`, container center | measured current host rect |
| `FLOW_WORLD` | React Flow graph origin, flow units | node positions, edge control point, graph placement | active canvas graph + current transform |
| `NODE_LOCAL` | node/parent content origin, flow units | child position, node-internal panel offset | node/parent identity |
| `SCREEN_SIZED_OVERLAY` | screen px while anchored to flow geometry | toolbar/panel dimensions and gaps | live viewport + measured node + overlay contract |
| `MEDIA_NORMALIZED` | media element bounds, usually `[0,1]` or intrinsic px | marks, crop points, brush/box coordinates | media rect/intrinsic size + editor session |

`MEDIA_NORMALIZED` is recorded so future code does not reuse graph conversion helpers for image-edit marks. Detailed media editors remain outside this audit.

### 3.2 Allowed conversion chain

```text
CLIENT -- current host rect / React Flow API --> CONTAINER_LOCAL / FLOW_WORLD
FLOW_WORLD + active viewport --> CONTAINER_LOCAL
NODE_LOCAL + ancestor positions --> FLOW_WORLD
FLOW_WORLD + measured node + live viewport --> SCREEN_SIZED_OVERLAY anchor
CLIENT + current media rect/intrinsic scale --> MEDIA_NORMALIZED
```

The preferred client-to-flow boundary is React Flow's `screenToFlowPosition`, not hand-written arithmetic. It accounts for the actual instance/container transform. Hand arithmetic may be valid only inside a documented pure model with the exact host rect and viewport snapshot.

### 3.3 Values that must carry identity

A point alone is insufficient when it may survive an event turn or surface lifecycle. The conceptual identity is:

```text
point = {
  domain,
  x,
  y,
  route,
  canvasId,
  canvasGeneration,
  capturedAt,
  optional owner/surface/gesture
}
```

This is a design requirement, not an instruction to persist DOM/client coordinates in graph data. Portable graph nodes store only validated `FLOW_WORLD` positions.

## 4. Fixed Open Canvas Findings

### 4.1 `OC-053`: one menu action keeps two coordinate projections

`CanvasMenuState` stores container-local `x/y` and a separate `flowPosition`. [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L327) makes the distinction explicit.

`openQuickAddMenu`:

- measures `canvasViewportRef.getBoundingClientRect()`;
- converts client coordinates into container-local menu coordinates;
- clamps the visible menu with 20px padding;
- separately calls `screenToFlowPosition({clientX,clientY})`;
- stores both projections in one menu session.

Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4144).

When the user chooses a type, the node uses `quickAddMenu.flowPosition`, not the clamped menu `x/y`. Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4925).

`INFERENCE`: edge avoidance for a screen surface must not silently move the graph insertion point. This method is directly useful for future LibTV menu/connection research, while Open Canvas menu dimensions and padding are not.

### 4.2 `OC-054`: live viewport and persisted viewport are separate

The fixed studio initializes local `liveViewport` from the document viewport. Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3666).

React Flow then uses:

```text
onMove     -> setLiveViewport(nextViewport)
onMoveEnd  -> setLiveViewport(nextViewport) + updateViewport(nextViewport)
```

Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6232).

The selected editor/action overlays read `liveViewport`, so they follow continuous motion without making every overlay frame a document authority. Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5964).

`INFERENCE`: the useful method is two-phase ownership, not Open Canvas's persistence product. Ordinary LibTV may keep viewport outside semantic graph history while still separating gesture-frame projection from stable per-canvas state.

### 4.3 `OC-055`: placement policy is entry-specific

| Entry | Fixed placement | Domain |
|---|---|---|
| direct add without point | actual canvas container center through `screenToFlowPosition` | `CLIENT -> FLOW_WORLD` |
| Quick Add/pane/connection menu | captured trigger `flowPosition` | `CLIENT -> FLOW_WORLD` |
| duplicate node | source `+48,+48` | `FLOW_WORLD` |
| paste subgraph | selection bounds centered on current viewport flow center + repeated `48` shift | `FLOW_WORLD` |
| file drop | pointer flow point + per-file `36,28` stagger | `CLIENT -> FLOW_WORLD` |
| node double-click | measured node center, same zoom | `FLOW_WORLD -> viewport command` |

Direct add evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4887). Duplicate evidence: [`canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L283). Paste evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3940). Drop evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4580). Double-click evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5030).

`INFERENCE`: there is no universally correct “new node offset”. Placement intent belongs to the named command/entry. The reusable method is explicit policy and one conversion boundary.

### 4.4 `OC-056`: hydrate owns the initial stable viewport

On canvas identity change, the fixed studio hydrates the full document, normalizes its viewport, writes `liveViewport`, then schedules `reactFlow.setViewport(..., duration:0)` on the next animation frame. Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4345).

Conflict reload/rebase paths also hydrate and apply the resulting document viewport explicitly. Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4744).

`INFERENCE`: document identity and viewport projection need an explicit convergence step. A route remount alone is not the viewport contract.

### 4.5 `OC-057`: gesture policy differs from LibTV and is not portable

The fixed React Flow configuration uses middle/right button panning, left-drag partial selection, no wheel zoom, and 0.25-1.8 zoom bounds. Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6216).

A separate wheel listener pans vertically or horizontally and immediately updates live/store/React Flow viewport. Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4474).

`SOURCE_UNKNOWN`: none of these exact bindings or bounds establish LibTV source behavior. The clone's V/H/Space and 0.1-8 range come from its own research/compatibility history.

### 4.6 `OC-058`: selected overlays share a live transform input

The fixed selected editor and action overlay independently derive center/top/bottom from the same selected node, measured dimensions and `liveViewport`. Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5964).

This supports the general method “one frame, one measured node, one viewport”. It does not replace the current LibTV source formulas in [`LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md).

### 4.7 `OC-059`: normalization and clamp counterexamples

The fixed `normalizeCanvasViewport` uses `Number(value || fallback)` without `Number.isFinite` or zoom-range enforcement. Evidence: [`serialization.ts`](../../research/upstream/open-canvas/shared/lib/canvas/serialization.ts#L83).

Consequences:

- non-numeric truthy input can become `NaN`;
- finite but extreme values remain accepted;
- zero zoom is silently replaced by `1`, hiding invalid input instead of diagnosing it;
- API/document validation may normalize, but the runtime helper itself is not a strict authority.

The Quick Add clamp computes an upper bound `rect.width - menuWidth - padding`. If the host is narrower than menu width plus padding, the final `Math.min` can produce a negative position. It also does not remeasure/reclamp an already-open menu after host resize. This is a code-backed edge-case inference, not recorded runtime evidence.

The selected editor overlay derives width from `canvasViewportRef.current.clientWidth`, but that width is not a dependency of its `useMemo`. A host resize without node/viewport state change may leave a stale width until another dependency updates. Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5964).

### 4.8 `OC-060`: gesture/session ownership remains partial

The middle/right panning CSS state clears on `window.pointerup`, but there is no fixed `pointercancel`, `window.blur` or visibility cleanup in that effect. Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4509).

Multi-file drop converts the pointer once, then asynchronously creates/uploads files one by one with staggered positions. Earlier files may commit while a later file fails; the path has no all-file atomic plan and no explicit canvas generation owner. Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4580).

Quick Add from a pending connection creates the node first and then attempts the edge. A failed edge leaves the node committed. This is already relevant to graph transaction authority; this audit only adds that the captured flow point and pending source identity belong to one menu session.

## 5. Current Clone Findings

### 5.1 Viewport projection pipeline

The ordinary route has three simultaneous projections:

| Projection | Current owner | Update path |
|---|---|---|
| React Flow controlled viewport | page `flowViewport` state | `onViewportChange`, responsive effect, organize/restore |
| per-canvas stable viewport | `CanvasData.viewport` | `setViewport` writes current active canvas |
| visible zoom percent | `uiStore.zoomLevel` | `onViewportChange`, responsive effect, organize/onInit |

Evidence: [`page.tsx`](../../src/app/page.tsx#L143), [`page.tsx`](../../src/app/page.tsx#L285), [`canvasStore.ts`](../../src/store/canvasStore.ts#L2784).

`CLONE_FACT`: `onViewportChange` writes all three on every callback. Unlike Open Canvas, there is no declared frame/stable split.

`CLONE_FACT`: viewport writes do not enter graph history. This is coherent with the current graph-history contract and must not be “fixed” by adding per-frame undo entries.

### 5.2 Navigation gesture state is a positive island

The current route computes:

```text
effectivePan = canvasTool === "pan" || isSpacePressed
```

V/H switch the persistent tool, Space is temporary, and the temporary state clears on keyup, window blur and document hidden. React Flow receives one derived `panOnDrag/selectionOnDrag/nodesDraggable` policy and disables its built-in activation key. Evidence: [`page.tsx`](../../src/app/page.tsx#L379), [`page.tsx`](../../src/app/page.tsx#L577).

This is consistent with [`NAVIGATION_GESTURES.spec.md`](liblib-canvas-batch6-2026-08-25/NAVIGATION_GESTURES.spec.md). It is a clone contract shaped by LibTV shortcut evidence, not an Open Canvas transplant.

### 5.3 Default add placement uses the browser window, not the canvas host

`addNode()` reads the active canvas viewport and delegates to `getViewportCenterPosition`. That helper uses `window.innerWidth/innerHeight` and manual viewport arithmetic. Evidence: [`canvasStore.ts`](../../src/store/canvasStore.ts#L942), [`canvasStore.ts`](../../src/store/canvasStore.ts#L2910).

The actual React Flow host is the flexible `<main>` after the optional 240px asset panel and before other overlay UI. Evidence: [`page.tsx`](../../src/app/page.tsx#L508).

Therefore, when layout reduces or shifts the visible host, “window center” and “canvas host center” differ. The static code proves the coordinate mismatch; exact pixel drift under each panel/mobile state still needs a focused browser fixture.

This is `LIBTV-VGP-001` and the highest-confidence future implementation candidate in this batch.

### 5.4 Placement writers are explicit but distributed

Current graph placement includes:

- default add at computed viewport center;
- explicit `addNodeAtPosition`;
- derived node to the right of absolute source with collision slots;
- specialized audio/frame/subtitle/shot/process result layouts;
- duplicate root at fixed `+40,+40` flow offset;
- group/ungroup relative/absolute conversion;
- React Flow node drag final positions;
- organize source-shaped/fallback positions;
- initial demo hard-coded topology.

The helper layer already has useful absolute-parent traversal and collision checks. Evidence: [`canvasStore.ts`](../../src/store/canvasStore.ts#L403), [`canvasStore.ts`](../../src/store/canvasStore.ts#L421).

`CLONE_FACT`: ordinary LibTV currently has no file-drop, graph clipboard paste, Quick Add-at-pointer or create-on-connection runtime path. These are absent capabilities, not defects, until LibTV source/product evidence authorizes them.

### 5.5 Viewport lifecycle is not generation-bound

`setViewport` captures `activeCanvasId` when called but accepts any finite/non-finite shape without validation or result. The page callback does not carry a canvas ID or generation. A queued callback around switch can therefore target the active owner at callback time rather than the event's original owner.

React Flow is keyed by `activeCanvasId`, which reduces stale instance state but does not by itself define callback ownership. This gap is already identified in [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md).

### 5.6 Demo responsive viewport is bootstrap and runtime at once

On mount, active canvas change and media-query change, `canvas-2` receives fixed compact/desktop viewport values and they are also written to store. Evidence: [`page.tsx`](../../src/app/page.tsx#L335).

This can overwrite a user-adjusted stored viewport after switching away/back or crossing the breakpoint. The behavior is a source-shaped demo bootstrap, not a safe general restore policy.

### 5.7 Organize and drag transients lack owner identity

`organizeSnapshot` stores nodes and viewport but no canvas ID/generation. Restore later writes current route/store owners. Evidence: [`page.tsx`](../../src/app/page.tsx#L309).

`dragHistorySnapshot` stores graph snapshot and node IDs but no canvas ID/generation. `onNodeDragStop` reads whichever canvas is active at stop time. Evidence: [`page.tsx`](../../src/app/page.tsx#L536).

`connectionGesture` similarly stores node/handle identity without canvas identity and currently only clears on `onConnectEnd`. Evidence: [`page.tsx`](../../src/app/page.tsx#L138), [`page.tsx`](../../src/app/page.tsx#L277).

These issues belong to lifecycle/routing contracts. The viewport contract should specify the captured geometry/gesture owner, while graph contracts retain mutation/history authority.

### 5.8 Overlay geometry is already specialized

The current selected-image top toolbar is screen-sized through React Flow `NodeToolbar`; the bottom panel is node-local and inverse-scaled. The exact source-derived gaps and action-state boundaries are already formalized in [`LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md).

The new viewport contract must only provide:

- the definition of one current live viewport snapshot;
- parent-to-world position conversion;
- container/frame ownership;
- resize/switch/gesture invalidation rules.

It must not replace `10 + 24 * zoom`, `16 * zoom`, toolbar width or active-image-tool state rules.

## 6. Placement Writer Inventory

| Writer/entry | Current policy | Coordinate owner | History | Audit status |
|---|---|---|---|---|
| Add Node panel / Character Library | window-center arithmetic using stored active viewport | ambiguous window vs host | one graph step | `LIBTV-VGP-001` confirmed mismatch |
| `addNodeAtPosition` | supplied flow point | caller | one graph step | caller boundary not typed |
| derived node | absolute source right + named offset/collision | active graph | one graph step | useful current method |
| audio/video specialized outputs | absolute source/result columns | active graph | one graph step | domain-specific; no generic rewrite |
| duplicate selection | fixed `+40,+40` flow delta | captured selection graph | one graph step | covered by copy contract |
| group/ungroup | world <-> parent-local transform | current graph | one graph step | covered by graph contracts |
| node drag frames | React Flow position changes | current instance/store | zero per-frame, one stop step | owner generation missing |
| organize | source-shaped/fallback flow positions + width-derived viewport | page snapshot/current graph | graph one step; viewport outside history | owner/height policy partial |
| fitView/zoom | React Flow instance animation | current instance | zero graph history | stable endpoint implicit in callbacks |
| responsive bootstrap | fixed compact/desktop viewport | media query + canvas ID | zero graph history | overwrites user viewport |
| pending connection menu | absent | n/a | n/a | `SOURCE_UNKNOWN`, do not copy Open Canvas |
| file drop | absent | n/a | n/a | `SOURCE_UNKNOWN`, do not copy Open Canvas |
| clipboard paste | design only | future explicit flow anchor | one graph step | copy contract, runtime missing |

## 7. Clone Issue Register

| ID | Issue | Impact | Confidence | Existing owner | Recommended disposition |
|---|---|---|---|---|---|
| `LIBTV-VGP-001` | default add uses browser window center, not actual canvas host center | visible misplaced new node after panel/layout change | high static | none | P0 formalize + future focused fixture |
| `LIBTV-VGP-002` | viewport accepts non-finite/out-of-range values | broken transform/overlay/placement | high static | lifecycle partial | strict normalize/result in formal contract |
| `LIBTV-VGP-003` | viewport callback/write has no canvas generation | stale cross-canvas write | high inference | multi-canvas contract | compose, do not duplicate |
| `LIBTV-VGP-004` | `canvas-2` responsive effect rewrites stored user viewport | switch/resize loses user view | high static | multi-canvas DQ | bootstrap-only target |
| `LIBTV-VGP-005` | organize snapshot lacks canvas/generation | restore can affect wrong canvas | high static | lifecycle + organize spec | owner-bound transaction |
| `LIBTV-VGP-006` | drag snapshot lacks canvas/generation | wrong graph/history on switch race | high static | RF routing + lifecycle | owner-bound gesture transaction |
| `LIBTV-VGP-007` | connection gesture lacks canvas/generation/cancel matrix | stale menu/connection future risk | high static | connection + lifecycle | captured gesture owner |
| `LIBTV-VGP-008` | live/stable viewport phases are not declared | per-frame store churn and unclear completion | high static | none | two-phase projection contract |
| `LIBTV-VGP-009` | local/store/zoom-percent projections can drift | wrong label/overlay/add placement | medium inference | page/UI store | one canonical frame/stable snapshot |
| `LIBTV-VGP-010` | placement callers pass untyped `{x,y}` | domain mix remains easy | high design | copy/graph partial | conceptual domain-tagged boundary |
| `LIBTV-VGP-011` | host resize/panel open has no declared anchor preservation | content appears to jump or add center drifts | medium | overlay/layout specs | resize policy + browser fixture |
| `LIBTV-VGP-012` | zoom/fit animations rely on callbacks for final stable commit | interrupted animation endpoint unclear | medium inference | React Flow runtime | operation/session endpoint rule |
| `LIBTV-VGP-013` | organize viewport uses width only and fixed top margin | tall/short container framing may differ | high static, parity unknown | organize spec | preserve compatibility until source evidence |
| `LIBTV-VGP-014` | exact LibTV source add/drop/paste/pending-connection placement unknown | parity claims unsafe | high | source queue | keep gated |
| `LIBTV-VGP-015` | overlay contract lacks general host-resize/generation composition | correct formula can use stale frame | medium | overlay contract | add composition link, not formula rewrite |
| `LIBTV-VGP-016` | FrameOS/Director have independent viewport meanings | shared helper could corrupt route/domain boundaries | high architecture | route stores | explicit exclusion/isolation |

## 8. Open Canvas Adoption Boundary

### 8.1 Adopt/adapt as method

| Method | LibTV use | Boundary |
|---|---|---|
| actual host rect + React Flow conversion | default/pointer/menu placement | use current LibTV entry/product policy |
| menu screen point separated from graph flow point | future anchored surface design | do not create Quick Add without source authorization |
| live viewport during movement, stable viewport at end | overlay continuity + per-canvas owner | viewport remains outside semantic graph history |
| entry-specific placement policy | add/duplicate/derived/paste distinctions | offsets/numbers remain LibTV-specific |
| full document hydrate + explicit viewport convergence | canvas switch/restore | no URL/persistence transplant |
| measured node + one live viewport | general composition input | exact overlay formula remains LibTV authority |

### 8.2 Reject transplant

- Open Canvas 324px menu, 20px clamp, 0.25-1.8 zoom, middle/right pan or disabled wheel zoom;
- global document viewport persistence/save/conflict semantics;
- permissive `Number(value || fallback)` viewport normalization;
- narrow-container clamp that permits negative positions;
- one-by-one async file drop as an atomic import pattern;
- fixed `36/28/48` offsets as LibTV product truth;
- toolbar Quick Add trigger flow point as a decided LibTV add location;
- Open Canvas's lack of V/H/Space as evidence against the current LibTV navigation contract.

## 9. High-Value Work Ranking

| Rank | Documentation outcome | Value | Blocker |
|---:|---|---|---|
| 1 | formal container/client/flow conversion and default-add policy | directly prevents visible misplaced nodes | runtime implementation not authorized |
| 2 | live/stable/bootstrap viewport owner model | protects overlay continuity and canvas restore | source save semantics not needed |
| 3 | gesture transaction owner/cancel matrix | closes switch/delete/blur races | composes existing contracts |
| 4 | placement policy registry | prevents one offset/helper from spreading across commands | exact source placements partially unknown |
| 5 | resize/sidebar/mobile fixture | catches host/window center and stale overlay errors | browser fixture not implemented |
| 6 | source add/drop/paste/pending-connection evidence | improves parity decisions | disposable source state/login may block |

## 10. Formal Contract Questions

| Candidate ID | Question | Recommended default | Evidence needed before changing |
|---|---|---|---|
| `LIBTV-VGP-DQ-001` | canonical client-to-flow conversion | current React Flow instance + actual host rect/API | focused local fixture |
| `LIBTV-VGP-DQ-002` | live vs stable viewport commit point | live every frame; stable on end/explicit command completion | callback trace |
| `LIBTV-VGP-DQ-003` | viewport validation | finite x/y, finite zoom clamped to current route bounds | pure fixture |
| `LIBTV-VGP-DQ-004` | default add anchor | center of actual visible React Flow host | source if exact parity requested |
| `LIBTV-VGP-DQ-005` | panel open/close anchor preservation | preserve current flow point under host center unless source says otherwise | local visual fixture + source |
| `LIBTV-VGP-DQ-006` | interrupted zoom/fit endpoint | latest current-generation operation owns endpoint; stale callback ignored | browser trace |
| `LIBTV-VGP-DQ-007` | organize keep/restore viewport | owner-bound preview viewport, outside generic graph undo | existing organize/source contract |
| `LIBTV-VGP-DQ-008` | paste placement | explicit flow anchor + repeat delta; source parity remains unknown | copy fixture/source |
| `LIBTV-VGP-DQ-009` | future pointer menu clamp | screen surface clamps independently; graph point unchanged | source/live menu evidence |
| `LIBTV-VGP-DQ-010` | viewport on canvas switch | exact target stable restore; bootstrap only for first init | lifecycle fixture |
| `LIBTV-VGP-DQ-011` | nested node anchor | ancestor-summed world position before viewport projection | group overlay fixture |
| `LIBTV-VGP-DQ-012` | source add/drop/pending connection | remain absent until evidence and authorization | disposable source fixture |

## 11. Candidate Local Fixture

Fixture ID: `LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01`.

### 11.1 Deterministic topology

- canvas A and B with distinct generations and viewport states;
- one ordinary top-level node with known dimensions;
- one group with one child at known parent-local coordinates;
- one selected image with existing toolbar/panel contract;
- host states: full width, asset panel open, agent drawer open, compact width;
- viewport states: identity, translated, 0.28, 0.5, 1, max-range boundary;
- fake animation/gesture clock and explicit operation IDs.

### 11.2 Pure cases

- client/container/flow round-trip under host offset and zoom;
- parent-local to world position;
- invalid `NaN/Infinity/zero/negative/extreme` viewport handling;
- host-center default placement with node dimensions;
- screen clamp leaves flow anchor unchanged;
- duplicate/derived fixed flow offsets remain invariant under pan/zoom;
- operation/canvas generation stale rejection.

### 11.3 Browser cases

- add same node with asset panel closed/open and assert host-center alignment;
- pan/zoom frames keep selected toolbar/panel attached from one viewport snapshot;
- finish/interruption yields one stable current-generation viewport;
- Space temporary pan clears on keyup/blur/visibility and does not move nodes;
- node drag creates one graph history step and no viewport history;
- switch during viewport/drag/organize invalidates old owner;
- resize/compact transition follows declared anchor policy;
- FrameOS and Director route/3D viewport remain unchanged.

Undo is not fixture teardown. Each browser case starts from a fresh Page or explicit deterministic reset.

## 12. Candidate Verifier

Verifier ID: `LIBTV-VR-020`.

| Layer | Required checks |
|---|---|
| static | every placement writer has one declared input domain/policy/owner |
| pure | conversions, finite validation, parent world position, placement invariance, stale generation |
| store | live/stable/bootstrap projection, exact per-canvas owner, zero semantic viewport history |
| browser | host rect, viewport trace, node/overlay rects, gesture start/update/end/cancel, resize/switch |
| composition | `VR-001/011/016/017/019` and organize/navigation regressions |
| exit | no window/host mix, no stale owner write, exact placement/history/selection effects |

`VR-020` must not replace source overlay geometry, graph copy, React Flow transport, multi-canvas lifecycle or command-context verifiers. It supplies their shared spatial/gesture frame.

## 13. Safe Source Evidence Queue

Read-only LibTV source research should prioritize:

1. Add Node from panel at two host widths and two zooms: where does the new node appear?
2. Asset/history/agent panel open/close: is current visual center or left/top flow point preserved?
3. Fit View and fixed zoom: anchor center, animation and overlay continuity.
4. V/H/Space/wheel gesture matrix and blur/cancel behavior.
5. Add from Handle/pending connection if safely available without committing graph mutation.
6. Clipboard/drop indicators without uploading or pasting into shared graph.
7. Group child selected overlay under pan/zoom if a disposable source topology exists.

Stop before creating shared nodes, uploading files, invoking providers, paying, changing account preferences or performing irreversible source mutations. Record `SOURCE_BLOCKED` rather than using Open Canvas behavior as a substitute.

## 14. Authority Handoff

| Question | Authority after this audit |
|---|---|
| exact selected-image toolbar/panel formula | [`LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md) |
| V/H/Space current behavior | [`NAVIGATION_GESTURES.spec.md`](liblib-canvas-batch6-2026-08-25/NAVIGATION_GESTURES.spec.md) |
| node position framework changes/history | [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md) |
| canvas switch/delete/generation | [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) |
| selection/focus/shortcut context | [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md) |
| copy/paste closure and flow-anchor design | [`LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md) |
| current fixed spatial facts and issue inventory | this dated audit |
| future coordinate/viewport/placement policy | planned `LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md` |

## 15. Completion Boundary

This dated audit is complete because it:

- fixes both source baselines;
- inventories coordinate domains, viewport projections, gesture state and placement writers;
- records Open Canvas positive methods and counterexamples separately;
- identifies one high-confidence visible clone defect without changing code;
- maps races and history rules back to existing authorities;
- defines issue IDs `LIBTV-VGP-001..016` and decision candidates;
- defines a candidate fixture/verifier boundary;
- leaves exact LibTV source behavior explicitly unknown where evidence is absent.

It does not prove runtime pixel drift, source placement parity, mobile behavior or authorized implementation readiness. Those claims require the formal contract, disposable fixture and focused browser/source evidence.

Current conclusion:

> Open Canvas is useful because it makes screen anchor and graph point separate values and because it distinguishes live movement from stable viewport state. Its own clamp, normalization, gesture cleanup and async drop gaps show why this method must be adapted rather than copied. The LibTV clone should first make the actual React Flow host and current canvas generation authoritative; only then should it add any source-confirmed pointer placement or menu behavior.
