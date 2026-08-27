# LibTV Viewport, Coordinate And Gesture Research Plan

> Status: `ACTIVE_RESEARCH`.
>
> Scope: documentation-only study of Open Canvas viewport/coordinate/placement methods and their value for the ordinary LibTV clone route.
>
> Baselines: clone `cfc7898`; Open Canvas `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> Authorization boundary: no changes to `src/`, tests, FrameOS, Director runtime, either submodule or source websites.

## 1. Problem

The repository already has a strong selected-image overlay formula and a historical navigation-gesture spec, but it does not yet have one cross-entry authority for:

- live viewport during pan/zoom versus persisted per-canvas viewport;
- client/shell/screen/flow/node-local/media-normalized coordinate domains;
- menu anchors versus graph placement points;
- add/drop/paste/duplicate/derived/pending-connection placement;
- pan/select/temporary-pan/node-drag gesture ownership and cancellation;
- fitView/zoom/bootstrap/resize/switch effects;
- viewport-dependent overlays, history and canvas-generation isolation.

Open Canvas is valuable because its fixed implementation contains both positive methods and counterexamples across these boundaries. It is not a visual or product truth source for LibTV.

## 2. Existing Authorities To Compose

| Authority | Owns | Must not be duplicated |
|---|---|---|
| [`LibTVOverlayPositioning.contract.md`](../research/components/LibTVOverlayPositioning.contract.md) | standard selected-image toolbar/panel geometry | source-exact toolbar/panel formulas |
| [`NAVIGATION_GESTURES.spec.md`](../research/liblib-canvas-batch6-2026-08-25/NAVIGATION_GESTURES.spec.md) | current V/H/Space clone gesture state | historical implementation provenance |
| [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) | per-canvas viewport and generation lifecycle | switch/delete owner policy |
| [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../research/LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md) | framework change transport and drag history | node-position mutation authority |
| [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../research/LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md) | shortcut/focus/context precedence | keyboard dispatch authority |
| [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../research/LIBTV_GRAPH_TRANSACTION_CATALOG.md) | semantic graph/history rules | named graph command semantics |

The new research should define composition edges and fill only the missing coordinate/gesture/placement authority.

## 3. Research Questions

1. Which coordinate domains exist in fixed Open Canvas and the current clone, and where are conversions allowed?
2. Which owner supplies viewport state during a gesture, at gesture end, during hydration and after canvas switch?
3. Why does Open Canvas keep Quick Add menu screen position and node flow position separately?
4. How do add-at-center, pointer drop, clipboard paste, repeated paste, duplicate and pending connection choose placement?
5. Which operations preserve a screen anchor while viewport changes, and which preserve a graph point?
6. What are the cancellation rules for blur, pointer cancel, surface open, switch, delete and stale callback?
7. Which viewport/placement transitions belong to semantic graph history, viewport history, page transient state or neither?
8. Which Open Canvas choices are product-specific and must be rejected for LibTV?
9. Which LibTV source interactions remain unknown and require a disposable read-only/source fixture before parity claims?

## 4. Evidence Queue

### 4.1 Fixed Open Canvas

Read and record exact paths for:

- `liveViewport` initialization, `onMove` and `onMoveEnd`;
- React Flow pan/select/zoom props and viewport bounds;
- `screenToFlowPosition` call sites;
- Quick Add `screenPosition + flowPosition` ownership and clamp;
- node add, drop, paste, repeated paste and viewport-center placement;
- fitView/zoom controls, initial viewport, hydration and responsive viewport adjustment;
- selected editor anchor and measured node conversion;
- any stale closure, rounding, container-rect or duplicated conversion counterexample.

Candidate evidence IDs: `OC-053..060`.

### 4.2 Current LibTV Clone

Read and record exact paths for:

- `flowViewport`, `onViewportChange`, store viewport and React Flow controlled state;
- zoom/fitView/organize preview and switch/hydrate behavior;
- V/H/Space gesture state and blur cleanup;
- node drag frame/end, history compression and canvas-generation gaps;
- default add-node placement and every derived/copy placement writer;
- selected toolbar/panel coordinate ownership;
- shell/sidebar/minimap/mobile layout effects;
- route isolation from FrameOS and Director's independent 3D viewport.

Candidate clone issue IDs: `LIBTV-VGP-001..N`.

## 5. Planned Deliverables

| Deliverable | Lifecycle | Purpose |
|---|---|---|
| `docs/research/LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md` | dated reference | fixed source/clone facts, issue inventory and authority gaps |
| `docs/research/LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md` | stable guide/reference | coordinate taxonomy, owner model, transitions, invariants and decision queue |
| `LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` | fixture design | deterministic A/B canvas, viewport, node, pointer and container cases |
| `LIBTV-VR-020` | verifier design | pure conversion/owner checks plus focused browser trace |
| `OC-PATTERN-10` / `OC-ADOPT-023` / `OC-BP-010` | Open Canvas translation | method, adoption boundary and implementation handoff |
| `OC-TR-016` / `LIBTV-TR-042` / `DEC-036` / `LIBTV-UIX-20` | governance | traceability, decision and UI/UX mapping |

IDs are reserved by this plan and become authoritative only when their target documents are added and indexed.

## 6. Work Sequence

1. Inventory existing authorities and contradictory/stale claims.
2. Extract fixed Open Canvas coordinate and viewport call sites into a dated fact table.
3. Extract current clone owners, ingress paths, placement writers and lifecycle races.
4. Separate `SOURCE_FACT`, `CLONE_FACT`, `INFERENCE`, `CLONE_DECISION` and source unknowns.
5. Rank issues by visible fidelity, correctness risk and implementation dependency.
6. Write the formal contract only after the static audit establishes the gap.
7. Define fixture and verifier replacements without modifying tests.
8. Sync Hub -> Guide -> Reference navigation and Open Canvas adoption/handoff chain.
9. Run documentation link and diff checks; commit/push each key batch.

## 7. Stop Conditions

Stop an evidence path when it would require:

- modifying or installing dependencies in the Open Canvas submodule;
- changing source-site graph, preferences, uploads, provider tasks or paid state;
- modifying clone runtime or verifier code;
- claiming LibTV parity from Open Canvas behavior;
- guessing exact mobile, drop, pending-connection or source placement behavior without evidence.

Record the unknown and continue with the next safe evidence path.

## 8. Acceptance Criteria

This research batch is complete when:

- every coordinate domain and conversion boundary has a declared owner;
- live/persisted/bootstrap viewport states are separated;
- gesture start/update/end/cancel and canvas-generation rules are explicit;
- all current placement writers are inventoried and mapped to named policies;
- overlay geometry composes with, rather than duplicates, the existing source formula;
- viewport-only effects are separated from graph/history effects;
- fixture `VIEWPORT-COORDINATE-01` and verifier `VR-020` have deterministic cases;
- Open Canvas methods and counterexamples have an explicit adoption boundary;
- agent navigation, decision, traceability and implementation handoff remain discoverable;
- documentation checks pass and no code/submodule/WIP path is modified.

## 9. Next Action

Extract exact fixed Open Canvas viewport, conversion, Quick Add, drop, paste and fitView call sites; then audit the corresponding clone route/store paths from current state rather than historical assumptions.
