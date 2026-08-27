# LibTV Viewport, Coordinate And Placement Contract

> Scope: ordinary LibTV React Flow host geometry, coordinate-domain conversion, live/stable/bootstrap viewport ownership, navigation and graph gesture lifecycle, entry-specific placement, host resize reconciliation, history boundaries and verifier design.
>
> Status: `STATIC_AUDIT_COMPLETE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_PARTIAL` / `SOURCE_PARITY_PARTIAL`.
>
> Clone baseline: `3ddd9da`. Open Canvas baseline: `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> Authorization boundary: research/design only. This contract does not authorize changes to `src/`, tests, FrameOS, Director runtime, either submodule or source websites.

## 1. Why This Contract Exists

The current clone already contains several correct spatial islands:

- source-shaped selected-image toolbar/panel formulas;
- per-canvas viewport storage;
- controlled React Flow viewport;
- V/H/Space navigation state with blur/visibility cleanup;
- one-history node drag compression;
- absolute parent traversal and collision-aware derived placement;
- source-shaped organize positions and viewport;
- fixed-flow duplicate placement.

These islands do not yet share one owner model. A plain `{x,y}` may currently mean browser client pixels, canvas-local pixels, graph flow units, child-relative flow units or normalized media coordinates. A plain `{x,y,zoom}` may mean a live gesture frame, a stable per-canvas value, a source-shaped bootstrap preset or an animation target.

The visible consequence is already concrete: default add placement computes the center from `window.innerWidth/innerHeight`, while the actual React Flow host can be shifted/narrowed by the asset panel. The correctness consequence is broader: viewport/organize/drag/connection callbacks can outlive their canvas owner.

The contract target is:

```text
current route + canvas generation
  -> current measured host frame
  -> current live/stable viewport owner
  -> typed coordinate conversion at one boundary
  -> named gesture or placement intent
  -> validated plan with captured owner
  -> live projection and/or one stable/domain commit
  -> exact history/selection/feedback reconciliation
```

## 2. Authority Composition

This contract owns only spatial frame, viewport phase, gesture owner and placement intent.

| Adjacent authority | Remains authoritative for |
|---|---|
| [`LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md) | source-exact selected-image toolbar/panel geometry and state-specific surface replacement |
| [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md) | T0/T1/semantic change classification, current-store reducer base and drag transport |
| [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) | canvas registry/generation, switch/delete reconciliation and external owner cleanup |
| [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md) | V/H/Space/zoom shortcut dispatch, foreground surface suspension and focus |
| [`LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md) | copy closure, ID/reference mapping, edge policy, flow-anchor/fixed-delta semantics and history |
| [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md) | mutation ingress T0-T5, proposal/plan/commit authority and zero-partial graph writes |
| [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md) | semantic graph/history invariants and compatibility cases |
| [`NAVIGATION_GESTURES.spec.md`](liblib-canvas-batch6-2026-08-25/NAVIGATION_GESTURES.spec.md) | historical/current V/H/Space behavior provenance |
| [`ORGANIZE_CANVAS.spec.md`](liblib-canvas-batch7-2026-08-25/ORGANIZE_CANVAS.spec.md) | organize product flow, preview confirmation and source-shaped layout |

The fixed fact inventory and issue IDs remain in [`LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md).

## 3. Coordinate Domain Model

### 3.1 Domain vocabulary

| Domain | Unit/origin | May persist in graph | Example |
|---|---|---:|---|
| `CLIENT` | CSS px from browser visual viewport | no | pointer `clientX/Y` |
| `HOST_LOCAL` | CSS px from current React Flow host rect | no | screen menu `left/top`, host center |
| `FLOW_WORLD` | React Flow world units | yes, as node/graph position | node top-left, paste anchor |
| `NODE_LOCAL` | child/parent-local flow units | yes, only with valid parent relation | grouped child position |
| `SCREEN_OVERLAY` | CSS px surface size/gap anchored to flow | no | selected toolbar/panel rect |
| `MEDIA_NORMALIZED` | normalized or intrinsic media editor space | only through media-domain schema | crop/mark/brush point |

### 3.2 Conceptual point descriptor

At conversion/planning boundaries, a point conceptually carries:

```text
SpatialPoint {
  domain
  x
  y
  route
  canvasId
  canvasGeneration
  hostEpoch?       // required for CLIENT/HOST_LOCAL conversions
  ownerId?         // gesture/surface/operation when the point survives a turn
}
```

The descriptor is a design model. It does not require every hot-path runtime point to allocate an object, and it does not authorize storing client/host coordinates in node data. Equivalent typed APIs/validated command objects are acceptable.

### 3.3 Host frame

The current React Flow host is represented conceptually as:

```text
HostFrame {
  route: "libtv"
  canvasId
  canvasGeneration
  epoch
  clientRect: { left, top, width, height }
  measuredAt
}
```

Requirements:

- width and height are finite and greater than zero;
- the DOM owner is connected and belongs to the ordinary LibTV route;
- `epoch` changes when the host rect/layout owner changes in a way that can invalidate delayed client/local anchors;
- measurement is taken from the actual React Flow host, not `window` and not a sibling toolbar;
- a stale host frame cannot be used to place graph content after switch/remount/resize.

### 3.4 Viewport snapshot

```text
ViewportSnapshot {
  canvasId
  canvasGeneration
  x
  y
  zoom
  phase: BOOTSTRAP | LIVE | STABLE | TARGET
  operationId?
  hostEpoch?
}
```

`TARGET` is a programmatic animation destination. It is not current transform truth until React Flow emits/commits the corresponding frame or an immediate command explicitly applies it.

### 3.5 No implicit domain conversion

The following are contract violations:

- subtracting node width from client pixels and storing the result as flow position;
- using `window.innerWidth/innerHeight` as the host rect;
- clamping graph flow coordinates to keep a screen menu visible;
- applying viewport transform to a child position before resolving its parent chain;
- feeding graph viewport zoom into media-editor normalized coordinates;
- reading a stable store viewport while a current gesture/live transform is different;
- using an old host rect after panel/route/canvas layout change.

## 4. Strict Geometry Validation

### 4.1 Finite values

All accepted spatial values are finite. `NaN`, `Infinity`, `-Infinity` and non-numeric strings reject before side effects.

Fallbacks are allowed only for absent optional bootstrap fields under an explicit schema. Invalid supplied values do not silently become `0` or `1`.

### 4.2 Viewport bounds

Current ordinary clone bounds remain:

```text
minZoom = 0.1
maxZoom = 8
```

These are current clone compatibility values, not Open Canvas or LibTV source proof. A future source/product decision may change them by updating this contract, UI controls and fixture together.

Validation policy:

| Field | Rule |
|---|---|
| `x/y` | finite; no arbitrary clamp because large translations may be valid |
| `zoom` | finite and within current route bounds |
| host width/height | finite and `> 0` |
| node width/height | finite and `> 0`, using declared measured/default fallback source |
| canvas/generation | equals current owner at apply/commit |
| host epoch | equals current frame for delayed client/local conversion |

### 4.3 Invalid result

Invalid geometry returns a stable typed result and causes:

- no graph mutation;
- no semantic history;
- no selection shift;
- no viewport projection;
- no screen menu opened from a fabricated `(0,0)`;
- owner-local diagnostic only when user recovery requires it.

## 5. Conversion Contract

### 5.1 Client to host-local

```text
localX = clientX - hostRect.left
localY = clientY - hostRect.top
```

The host frame and client event must belong to the same active route/canvas frame. Points outside the host are either rejected or explicitly allowed by the entry policy; they are not automatically clamped into the graph.

### 5.2 Host-local to flow

For pure-model verification:

```text
flowX = (localX - viewport.x) / viewport.zoom
flowY = (localY - viewport.y) / viewport.zoom
```

At runtime, current React Flow `screenToFlowPosition` is the preferred boundary for client points. Pure tests verify equivalence with the captured host/viewport model. The API result is still rejected if owner/epoch/value validation fails.

### 5.3 Flow to host-local

```text
localX = flowX * viewport.zoom + viewport.x
localY = flowY * viewport.zoom + viewport.y
```

Client rect is then:

```text
clientX = hostRect.left + localX
clientY = hostRect.top + localY
```

### 5.4 Parent-local to world

Resolve the complete ancestor chain before viewport projection:

```text
world = node.position
for each valid ancestor from parent to root:
  world += ancestor.position
```

Dangling parent, cycle or owner mismatch returns invalid/unknown according to graph document policy. Do not partially sum and continue.

### 5.5 Default host-center placement

For a node with declared flow dimensions:

```text
hostCenterClient = {
  x: hostRect.left + hostRect.width / 2,
  y: hostRect.top + hostRect.height / 2
}
centerFlow = clientToFlow(hostCenterClient, current live viewport)
nodeTopLeft = {
  x: centerFlow.x - nodeWidth / 2,
  y: centerFlow.y - nodeHeight / 2
}
```

This replaces the design assumption “browser window center equals canvas center”. It is a clone correctness default; exact source add placement remains in the decision queue.

### 5.6 Screen surface and graph anchor separation

A future pointer/connection menu may carry:

```text
surfaceAnchor: HOST_LOCAL / CLIENT
graphAnchor: FLOW_WORLD
```

Screen clamp/flip/avoidance may update only `surfaceAnchor`. `graphAnchor` remains the captured flow point unless the user explicitly chooses a new graph location.

This rule can be used to verify current anchored overlays. It does not authorize implementing Quick Add.

### 5.7 Media conversion isolation

Media editor points use their own current media DOM rect and intrinsic/normalized transform. They never call graph client-to-flow conversion merely because both receive pointer events.

## 6. Viewport Ownership Model

### 6.1 Four phases

| Phase | Owner | Purpose | Persistence/history |
|---|---|---|---|
| `BOOTSTRAP` | initial canvas setup only | source-shaped first framing/default | promote once to stable; no graph history |
| `LIVE` | current React Flow gesture/animation frame | overlays, zoom label, pointer conversion | page/session projection; no graph history |
| `STABLE` | per-canvas viewport owner | restore/switch/default placement outside gesture | canvas UI state; no semantic graph history |
| `TARGET` | current programmatic viewport operation | requested zoom/fit/center destination | not authoritative until applied/current |

### 6.2 Precedence

For current interaction/conversion:

```text
current React Flow/live frame
  -> current-generation stable viewport
  -> valid first-initialization bootstrap
  -> identity viewport only for an explicit new empty canvas
```

An old bootstrap preset never overwrites a user-owned stable viewport on switch or breakpoint change.

### 6.3 Gesture update and commit

Default pan/zoom flow:

```text
START  capture stable baseline + canvas/generation + host epoch
UPDATE accept current-owner finite frame -> LIVE
END    commit final current-owner finite frame -> STABLE exactly once
CANCEL restore LIVE to baseline STABLE; no stable change
STALE  ignore; no projection/commit
```

Implementation may keep stable viewport in `CanvasData` and live viewport in page/runtime state. The contract does not prescribe a store library.

### 6.4 Programmatic viewport command

Fit, zoom-to, zoom-by, set-center, organize viewport and host-resize reconciliation use an operation ID:

```text
request -> TARGET(owner, destination)
React Flow frames -> LIVE(owner)
completion/onMoveEnd -> STABLE(owner)
interruption/newer operation -> old owner STALE
```

If an immediate no-animation command applies the target synchronously, it may set LIVE and STABLE in one validated commit.

### 6.5 Zoom percent

Visible zoom percent is a derived projection of the current LIVE viewport, rounded for display. It is not an independent authority and is not used to reconstruct graph coordinates.

### 6.6 Overlay input

Viewport-dependent overlays read one validated LIVE snapshot from the same render/frame as measured node geometry. They do not combine:

- stable store zoom with current DOM translation;
- UI rounded percent with exact node transform;
- old host rect with current viewport;
- one selected node's size with another node's position.

## 7. Host Resize And Layout Reconciliation

### 7.1 Resize causes

- browser resize/orientation;
- asset panel open/close;
- agent drawer or route layout change;
- mobile breakpoint/layout transition;
- font/scrollbar/layout changes that alter the host rect;
- React Flow remount after canvas switch.

### 7.2 Clone correctness default

When a layout change alters the host but does not intentionally navigate the graph, preserve the flow point under the old host center at the new host center:

```text
oldCenterFlow = clientToFlow(oldHost.center, oldLiveViewport)
newViewport.x = newHost.width / 2 - oldCenterFlow.x * zoom
newViewport.y = newHost.height / 2 - oldCenterFlow.y * zoom
```

This is a conservative usability default, not proven LibTV source behavior. A source-authorized surface may instead preserve local/client position, but it must declare that policy.

### 7.3 Surface response

| Surface/state | On host epoch change |
|---|---|
| selected overlay | recompute from current node + live viewport + new host |
| screen menu/popover | remeasure and clamp/flip, or close if owner invalid |
| captured graph anchor | keep flow point; do not derive again from moved screen surface |
| pointer gesture | current browser/React Flow capture continues only if owner remains valid |
| stale delayed client point | reject; do not convert using new host silently |
| stable viewport | reconcile by declared anchor policy, commit once |

### 7.4 Responsive bootstrap boundary

`desktopViewport` and `compactViewport` are source-shaped initial fixtures for the demo canvas. They apply only before that canvas obtains user-owned stable viewport state. A media-query change after interaction invokes resize reconciliation, not bootstrap replacement.

## 8. Gesture Session Model

### 8.1 Session descriptor

```text
GestureSession {
  id
  kind
  route
  canvasId
  canvasGeneration
  hostEpoch
  startedAt
  pointerId/key?
  baselineViewport?
  baselineGraph?
  selectionSnapshot?
  state: STARTED | ACTIVE | ENDED | CANCELED | STALE
}
```

### 8.2 Gesture kinds

| Kind | Live effect | Stable/semantic effect |
|---|---|---|
| `PAN` | live viewport | one stable viewport on end |
| `ZOOM` | live viewport + overlay/label | one stable viewport on end |
| `TEMP_PAN_KEY` | effective navigation mode | none after key release |
| `NODE_DRAG` | T1 node positions | one graph history step on end |
| `SELECTION_RECT` | session selection projection | zero semantic history |
| `CONNECTION` | connection preview/pointer | named edge command or zero mutation |
| `MENU_ANCHOR` | screen surface + captured graph point | none until named command |
| `ORGANIZE_PREVIEW` | planned graph + viewport preview | organize-specific keep/restore authority |
| `DROP_IMPORT` | future preview/plan | unsupported until separate source/product contract |

### 8.3 Start

Start validates current route, canvas/generation, host frame and incompatible foreground context. It captures the baseline before accepted updates.

Starting a new mutually exclusive session cancels or supersedes the previous one explicitly. It cannot rely only on component remount.

### 8.4 Update

Every update validates session owner. Unknown/non-finite/stale updates do not partially mutate live viewport, graph, selection or history.

Node drag framework frames remain governed by the T1 transport allowlist. This contract adds owner/gesture identity only.

### 8.5 End

End is idempotent. A duplicate pointerup/moveEnd/animation completion cannot create a second stable viewport or graph history entry.

### 8.6 Cancel and stale

| Session | Correctness default on cancel |
|---|---|
| pan/zoom | restore live baseline; stable unchanged |
| temporary Space pan | clear temporary state; stable viewport remains any already-ended valid pan |
| node drag | restore baseline graph with zero new history unless product explicitly chooses commit-on-cancel |
| selection rect | preserve last valid/declared selection policy; zero graph history |
| connection | clear preview/session; zero edge/history |
| menu anchor | close surface; captured graph point discarded |
| organize preview | use organize keep/restore contract |

Switch/delete/unmount makes an old session stale. Stale completion never targets the new active canvas.

### 8.7 Blur and visibility

The current V/H/Space behavior is retained:

- Space keyup clears temporary pan regardless of later target focus;
- window blur clears temporary pan;
- hidden document clears temporary pan;
- foreground Director/active image surfaces suspend ordinary page gesture commands through the command-context contract.

Pointer-owned application state also declares pointercancel/lost-capture/unmount cleanup when the app, rather than React Flow, owns that state.

## 9. Placement Policy Registry

### 9.1 Placement plan

```text
PlacementPlan {
  commandKind
  owner: route + canvasId + generation
  strategy
  anchorDomain
  anchor
  node/closure bounds
  delta/collision policy
  selectionEffect
  historyEffect
  sourceParity
}
```

The planner validates all spatial values and graph owner before allocating/committing domain identities.

### 9.2 Current strategies

| Strategy | Entry | Rule | Status |
|---|---|---|---|
| `HOST_CENTER` | ordinary Add Node / Character Library | actual host center -> flow center -> node top-left | design target; runtime mismatch |
| `EXPLICIT_FLOW` | `addNodeAtPosition` / future accepted point | use validated current-owner flow point | runtime primitive; caller typing missing |
| `SOURCE_RIGHT_SLOT` | derived outputs | absolute source right + domain offset/collision | current useful runtime |
| `FIXED_FLOW_DELTA` | duplicate selection/node copy | root `+40,+40`, children per copy contract | current compatibility |
| `FLOW_ANCHOR` | future clipboard paste | align closure bounds to explicit flow anchor + repeat delta | design only |
| `FRAMEWORK_DRAG` | user drag | framework current positions, one end transaction | runtime partial |
| `ORGANIZE_LAYOUT` | organize | source-shaped IDs + fallback columns + viewport plan | runtime bounded |
| `BOOTSTRAP_TOPOLOGY` | demo initial nodes | fixed fixture coordinates | fixture/source-shaped only |

### 9.3 Entry-specific policy

No strategy is silently reused because two commands both “create a node”. In particular:

- derived output remains relative to source, not host center;
- duplicate remains flow-delta, not current cursor;
- future paste uses closure bounds, not first-node dimensions;
- future pending connection uses captured release point only if source/product authorizes that entry;
- organize remains an explicit layout operation;
- source-shaped initial fixture positions never become generic add defaults.

### 9.4 Selection and visibility

Placement is not complete merely because node coordinates exist. Named graph command defines:

- selected result IDs/primary;
- whether viewport remains unchanged, recenters or fits;
- whether a screen surface closes/rebinds;
- one semantic history step;
- typed outcome/feedback.

Default add currently selects the created node and records one graph history step. Exact source auto-pan/selection remains open.

### 9.5 Collision and clamping

Graph collision avoidance, if used, operates in `FLOW_WORLD` with declared node/closure bounds. Screen clamp operates in `HOST_LOCAL/CLIENT`. They are separate policies.

## 10. History And Document Boundaries

### 10.1 Zero semantic graph history

The following create no semantic graph history entry:

- live/stable viewport changes;
- zoom percent projection;
- host frame/resize measurement;
- pan/zoom gesture state;
- temporary Space mode;
- menu screen anchor/clamp;
- selection rectangle by itself;
- canceled/stale/invalid gesture or placement.

### 10.2 One semantic graph history step

- accepted default/explicit node add;
- accepted duplicate/paste/derived graph plan;
- completed node drag with changed positions;
- accepted connection;
- organize graph mutation according to its own transaction contract.

Viewport endpoint may be part of an operation-specific preview/result without entering generic graph undo snapshots.

### 10.3 Portable document

Portable graph documents contain validated `FLOW_WORLD/NODE_LOCAL` node positions according to graph schema. They do not contain:

- client/host rect;
- live gesture frame;
- pointer/key/host epoch;
- menu anchor;
- zoom UI percent;
- overlay screen rect;
- temporary navigation mode.

Whether stable viewport belongs to a future portable document/persistence envelope is owned by the graph document/product contract. It remains outside semantic graph history.

## 11. Canvas Lifecycle

### 11.1 Switch

Before target projection:

1. cancel/invalidate old viewport/drag/connection/menu/organize sessions;
2. prevent old callbacks from committing by canvas/generation;
3. load target graph and stable viewport;
4. remount/project React Flow;
5. establish target host epoch;
6. set live viewport from target stable value;
7. reconcile overlays/selection/focus through adjacent contracts.

### 11.2 Delete

Deleting an active canvas invalidates every spatial/gesture owner tied to it. Focus/selection/surface fallback follows lifecycle/selection contracts. No callback may redirect to the fallback canvas merely because it became active.

### 11.3 Duplicate

Canvas duplicate viewport policy remains the current lifecycle decision: copy source stable viewport unless source/product contract changes it. No live gesture/session is copied.

### 11.4 Async completion

Async graph completion may use operation-specific placement only from a current captured plan/current graph replan. It cannot late-read current active viewport/cursor to place a result that belongs to an old canvas.

## 12. Overlay Composition

### 12.1 Standard selected image

This contract supplies:

- current host frame;
- current live viewport;
- validated world position including parents;
- measured/default node dimensions;
- frame/generation invalidation.

The overlay contract supplies:

- top host `nodeTop - 24 * zoom - 10` plus translate;
- top gap `10 + 24 * zoom`;
- bottom gap `16 * zoom`;
- `1092.5x49` current action-state width/height evidence;
- inverse scale/natural clipping and active-tool replacement.

### 12.2 Resize and switch

An overlay cannot remain attached to an old host epoch or inactive canvas. It either recomputes from a valid current frame or unmounts through owner reconciliation.

### 12.3 No visual transplant

Open Canvas selected panel top/bottom numbers, width, clamp, z-index and container are not used as LibTV visual input.

## 13. Result And Reason Vocabulary

| Result | Meaning | Default effects |
|---|---|---|
| `APPLIED_LIVE` | current gesture/animation frame accepted | live projection only |
| `COMMITTED_STABLE` | final current viewport accepted | one stable viewport update |
| `COMMITTED_PLACEMENT` | named graph placement committed | exact graph/selection/history result |
| `CANCELED` | current session explicitly canceled | rollback/cleanup by session kind |
| `STALE` | owner/generation/operation/host epoch no longer current | zero effect |
| `INVALID_COORDINATE` | point/domain/value invalid | zero effect |
| `INVALID_VIEWPORT` | viewport/host invalid | zero effect |
| `OWNER_MISMATCH` | route/canvas/session mismatch | zero effect |
| `HOST_UNAVAILABLE` | no valid connected host frame | zero effect or defer explicit bootstrap |
| `UNSUPPORTED` | source/product entry not implemented | honest local feedback if invoked |
| `NOOP` | valid command has no changed endpoint/placement | zero graph/history |

Reasons are stable codes/args, not localized strings. Presentation follows [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md).

## 14. Invariants

| ID | Invariant |
|---|---|
| `LIBTV-VGP-I-001` | every point at a conversion/planning boundary has one declared domain |
| `LIBTV-VGP-I-002` | client/local conversion uses the current actual React Flow host, never browser window dimensions |
| `LIBTV-VGP-I-003` | accepted coordinates and viewport values are finite |
| `LIBTV-VGP-I-004` | accepted zoom is within current ordinary LibTV route bounds |
| `LIBTV-VGP-I-005` | flow placement belongs to current route/canvas/generation |
| `LIBTV-VGP-I-006` | delayed client/local points also match current host epoch |
| `LIBTV-VGP-I-007` | graph stores only declared flow/node-local positions, not client/menu/overlay coordinates |
| `LIBTV-VGP-I-008` | parent-local position resolves through a valid acyclic ancestor chain before viewport projection |
| `LIBTV-VGP-I-009` | screen clamp/flip never mutates captured graph flow anchor |
| `LIBTV-VGP-I-010` | live viewport is current projection authority during gesture/animation |
| `LIBTV-VGP-I-011` | stable viewport changes exactly once at current gesture/programmatic completion |
| `LIBTV-VGP-I-012` | bootstrap viewport applies only before user-owned stable state exists |
| `LIBTV-VGP-I-013` | visible zoom percent derives from live viewport and is never coordinate authority |
| `LIBTV-VGP-I-014` | viewport/host/menu/temporary gesture changes create zero semantic graph history |
| `LIBTV-VGP-I-015` | completed changed node drag creates one graph history step |
| `LIBTV-VGP-I-016` | canceled node drag leaves no untracked changed graph |
| `LIBTV-VGP-I-017` | duplicate/stale gesture completion is idempotent and zero-effect |
| `LIBTV-VGP-I-018` | canvas switch/delete invalidates old spatial and gesture owners |
| `LIBTV-VGP-I-019` | old callback never retargets whichever canvas is active later |
| `LIBTV-VGP-I-020` | default add uses actual host center and declared node dimensions |
| `LIBTV-VGP-I-021` | placement strategy belongs to named command intent |
| `LIBTV-VGP-I-022` | fixed flow offsets are invariant under pan/zoom |
| `LIBTV-VGP-I-023` | collision avoidance and screen clamp operate in separate domains |
| `LIBTV-VGP-I-024` | overlay inputs come from one current frame/owner |
| `LIBTV-VGP-I-025` | host resize uses one declared anchor-preservation policy |
| `LIBTV-VGP-I-026` | media-normalized pointer math remains outside graph viewport conversion |
| `LIBTV-VGP-I-027` | V/H persistent tool and Space temporary pan remain distinct state owners |
| `LIBTV-VGP-I-028` | Space temporary pan clears on keyup, blur and hidden document |
| `LIBTV-VGP-I-029` | unsupported source/product entries remain absent/honest, not filled from Open Canvas |
| `LIBTV-VGP-I-030` | FrameOS graph viewport and Director 3D viewport remain route/domain isolated |
| `LIBTV-VGP-I-031` | invalid/stale geometry causes zero graph/history/selection/viewport residue |
| `LIBTV-VGP-I-032` | one accepted placement plan has exact selection, viewport and history effects |

## 15. Current Runtime Mapping

| Area | Current runtime | Contract target | Maturity |
|---|---|---|---|
| V/H/Space | persistent + temporary with cleanup | preserve | runtime positive island |
| controlled viewport | page state + per-frame store write | live/stable phase split | partial |
| stable viewport | per-canvas object | validated generation-bound owner | partial |
| zoom percent | separate UI state | pure live projection | partial |
| default add | window center arithmetic | actual host center conversion | mismatch |
| derived placement | absolute source + slot/collision | named strategy | useful partial |
| duplicate | fixed flow delta | copy contract strategy | compatibility |
| drag | per-frame positions + end history | owner-bound session/cancel | partial |
| organize | unkeyed page snapshot | owner-bound preview | partial |
| connection | unkeyed ref | owner-bound session | partial |
| demo responsive | repeated preset overwrite | bootstrap-only + resize reconcile | mismatch |
| overlay | specialized current formulas | one current host/live frame composition | partial |
| drop/Quick Add/paste | absent/design-only | remain gated | correct boundary |

## 16. Decision Queue

| ID | Decision | Current default | Evidence needed before change |
|---|---|---|---|
| `LIBTV-VGP-DQ-001` | exact source default add anchor | actual host center correctness default | disposable source add fixture |
| `LIBTV-VGP-DQ-002` | source panel open/close anchor preservation | preserve flow point under host center | source panel/viewport rect trace |
| `LIBTV-VGP-DQ-003` | live/stable commit callback shape | update live per frame; stable on end/explicit completion | React Flow focused trace |
| `LIBTV-VGP-DQ-004` | zoom bounds | preserve current 0.1-8 compatibility | current source zoom menu/runtime evidence |
| `LIBTV-VGP-DQ-005` | interrupted animation endpoint | newest current-generation operation owns current final transform | controlled local animation fixture |
| `LIBTV-VGP-DQ-006` | node drag cancel policy | rollback baseline, zero history | React Flow pointercancel/blur behavior + product decision |
| `LIBTV-VGP-DQ-007` | organize height/vertical framing | preserve current source-shaped fixed-top policy | source organize multi-viewport evidence |
| `LIBTV-VGP-DQ-008` | exact source selection/auto-pan after add | select created node; viewport unchanged by clone default | source add observation |
| `LIBTV-VGP-DQ-009` | future pointer menu/drop/pending connection | remain absent | source evidence + explicit authorization |
| `LIBTV-VGP-DQ-010` | clipboard paste anchor | explicit flow anchor per copy contract | source/product decision + fixture |
| `LIBTV-VGP-DQ-011` | stable viewport persistence envelope | per-canvas in-memory only | explicit persistence product scope |
| `LIBTV-VGP-DQ-012` | mobile host clamp/menu degradation | no new menu; current overlay natural clipping | source mobile evidence |

## 17. Local Fixture Contract

Fixture ID: `LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01`.

### 17.1 Topology and owner setup

- route ordinary LibTV only;
- canvas A/B with deterministic IDs and generations;
- distinct stable viewports;
- top-level node `N1` with known dimensions;
- group `G1` and child `C1` with known local/world positions;
- selected image `I1` using existing overlay contract;
- optional sibling nodes for collision/organize cases;
- host layout states full, asset-open, agent-open and compact;
- fake viewport operation clock/IDs.

### 17.2 Pure conversion cases

1. client -> host-local -> flow under identity;
2. translated 0.28/0.5/1/8 viewports;
3. host with non-zero client left/top;
4. flow -> host/client round-trip tolerance;
5. parent-local child -> world;
6. dangling/cyclic parent invalid;
7. host-center top-left placement with node size;
8. screen clamp leaves flow anchor exact;
9. fixed-flow duplicate invariant under viewport;
10. invalid NaN/Infinity/zero/negative/out-of-range zoom;
11. stale canvas generation/host epoch/operation ID;
12. host-resize center preservation.

### 17.3 Viewport cases

| Case | Required result |
|---|---|
| pan frames then end | live frames exact; one stable endpoint; zero graph history |
| pan cancel | live returns baseline; stable unchanged |
| zoom animation | live follows current frames; newest operation commits once |
| interrupted zoom | old completion stale; current endpoint exact |
| fitView | current-generation stable endpoint once |
| canvas switch mid-pan | A callback cannot alter B; B stable restored |
| demo breakpoint after interaction | stable user viewport reconciled, bootstrap not reapplied |
| invalid viewport event | zero live/stable/UI residue |

### 17.4 Gesture/placement cases

- V/H persistent mode and Space temporary override;
- Space keyup/blur/visibility cleanup;
- foreground context suspends ordinary gesture shortcuts;
- node drag one history step;
- node drag cancel/switch owner behavior;
- connection start/end/cancel stale cleanup;
- organize keep/restore with owner;
- default add full/asset-open/compact actual host center;
- derived/duplicate offsets invariant under zoom;
- absent file drop/Quick Add remains unsupported/honest.

### 17.5 Overlay composition

For each selected-image case record in one frame:

- host rect/epoch;
- live viewport;
- selected node world position/measured dimensions;
- toolbar and panel rect;
- existing formula residuals;
- graph/history/selection counts.

### 17.6 Reset

Each browser case uses a fresh Page or deterministic reset. It restores A/B graphs, stable viewports, host layout, selection, foreground surfaces, navigation tool, transient sessions and fake operation clock. Undo is not teardown.

FrameOS runs as a separate route case. Director 3D state is not seeded into this fixture.

## 18. Verifier Contract

Verifier ID: `LIBTV-VR-020`.

### 18.1 Static layer

- every current placement writer maps to a strategy/domain/owner;
- no ordinary default-add path uses browser window center;
- every delayed spatial/gesture session declares canvas/generation;
- bootstrap preset cannot overwrite stable user viewport;
- FrameOS/Director viewport domains remain separate.

### 18.2 Pure layer

- finite validation and reason/result;
- conversions and round-trip tolerance;
- parent/world resolution;
- host-center placement;
- resize anchor policy;
- placement invariance;
- operation/session stale/idempotent reduction.

### 18.3 Store/transaction layer

- live/stable/bootstrap ownership;
- exact per-canvas viewport;
- viewport zero semantic history;
- node drag/add/duplicate/organize exact history according to adjacent contracts;
- invalid/stale zero graph/selection/history/viewport residue.

### 18.4 Browser layer

Record:

- actual host DOM rect and layout state;
- React Flow viewport frames and operation ID;
- node/overlay DOM rects;
- pointer/key start/update/end/cancel;
- canvas/generation/selection/history before/after;
- desktop/compact cases;
- console/page/request errors.

### 18.5 Composition

`VR-020` composes with:

- `VR-001/002` selected image/active surface geometry;
- `VR-011` subgraph placement;
- `VR-016` React Flow transport/drag;
- `VR-017` multi-canvas isolation;
- `VR-019` shortcut/focus/context;
- Batch 6 navigation, Batch 7 organize and current BottomToolbar/overlay regressions.

It does not replace their source, graph, accessibility or visual semantics.

### 18.6 Exit

- actual host/client/flow domains never mix;
- live/stable/bootstrap phases are observable and exact;
- no stale callback crosses canvas/host/operation owner;
- default add aligns to actual host center under layout changes;
- gestures cancel/end deterministically;
- overlay formula remains within existing tolerance;
- graph/history/selection effects match named command contracts.

## 19. Authorized Implementation Slices

No slice is currently authorized. If authorization is granted later:

### Slice A: pure spatial model

- finite viewport/host validation;
- domain conversion helpers/contracts;
- owner/result vocabulary;
- pure fixture cases only.

### Slice B: default add host authority

- measure actual React Flow host;
- convert host center through current instance;
- preserve existing add data/selection/history;
- asset-open/compact focused browser cases.

### Slice C: live/stable viewport projection

- separate current frame from stable per-canvas endpoint;
- keep zoom percent derived;
- preserve existing visual controls/ranges;
- no persistence/backend work.

### Slice D: gesture and canvas-generation ownership

- pan/zoom/drag/connection/organize owner IDs;
- cancel/stale/idempotent behavior;
- switch/delete/blur fixtures;
- compose routing/lifecycle contracts.

### Slice E: resize and overlay composition

- host epoch/resize observation;
- declared center preservation;
- selected overlay recompute;
- source formulas unchanged.

### Slice F: source-authorized placement entries

- only after current LibTV source/product evidence;
- update decision/adoption/fixture first;
- do not bundle file upload/provider/persistence into spatial work.

Each slice requires its own plan, implementation history, focused verifier, serial regressions and path-scoped commit/push.

## 20. Open Canvas Adoption Boundary

Adopt/adapt:

- screen surface anchor separate from graph flow anchor;
- actual host + framework conversion at input boundary;
- live viewport for motion/overlay, stable viewport at completion;
- entry-specific placement policy;
- explicit hydrate-to-instance viewport convergence;
- measured node + one live viewport frame.

Reject transplant:

- Quick Add visual/product behavior without LibTV evidence;
- Open Canvas menu dimensions/clamp and 0.25-1.8 zoom;
- middle/right pan or disabled wheel zoom as LibTV truth;
- permissive viewport normalization;
- sequential async drop as an atomic import pattern;
- fixed `36/28/48` offsets as LibTV values;
- local persistence/revision/conflict semantics;
- overlay dimensions/container/style.

## 21. Source Evidence Queue

Safe read-only source work remains:

1. default add placement under normal/side-panel host and two zooms;
2. fitView/zoom anchor and animation trace;
3. V/H/Space/wheel gesture and cancellation;
4. panel open/close viewport preservation;
5. selected nested/group node overlay if a disposable topology exists;
6. pointer menu/drop/pending connection only without mutating shared graph;
7. mobile/compact host behavior.

Stop before shared graph mutation, upload, provider task, payment, account preference or irreversible source state. `SOURCE_BLOCKED` is a valid result.

## 22. Completion Criteria

The viewport/coordinate/placement slice is complete only when:

- every accepted point has one domain and current owner;
- actual host rect replaces browser-window assumptions;
- live/stable/bootstrap/target viewport phases are explicit;
- viewport values are finite and bounded;
- default add and every placement writer has a named policy;
- gesture start/update/end/cancel/stale is deterministic;
- canvas switch/delete cannot receive old callbacks;
- host resize follows one declared anchor policy;
- overlay uses one current frame without changing source formulas;
- viewport remains outside semantic graph history;
- graph placements preserve exact one-step history/selection effects;
- source-unknown entries remain gated;
- `LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` and `LIBTV-VR-020` pass;
- adjacent verifier families and repository checks pass;
- research, implementation, verification and commit/push history are recorded.

Current conclusion:

> Spatial correctness is not one transform formula. It is the agreement between the current host frame, the current canvas generation, the current live viewport and the named command that owns placement. Open Canvas provides a useful dual-anchor and live/stable method, plus counterexamples that show why permissive normalization and implicit session cleanup are insufficient. The LibTV clone should keep its source-exact overlay and stronger navigation islands, then make the actual React Flow host and owner-bound viewport lifecycle the shared spatial authority.
