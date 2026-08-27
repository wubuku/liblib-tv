# LibTV Selection, Focus And Command Context Contract

> Scope: ordinary LibTV node/edge/primary selection, DOM focus zones, foreground surface command policy, keyboard and clipboard dispatch precedence, Escape layering, focus acquisition/containment/return, canvas/history/async reconciliation, and the Open Canvas methods and counterexamples that inform the design.
>
> Status: `STATIC_AUDIT_COMPLETE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_PARTIAL` / `SOURCE_PARITY_PARTIAL`.
>
> Clone baseline: `2c10292`. Open Canvas baseline: `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> Authorization boundary: this document defines research, design, fixture and verifier requirements. It does not authorize changes to `src/`, tests, FrameOS, either submodule or a source website.

## 1. Why This Contract Exists

Canvas interaction has three related but non-equivalent authorities:

```text
selection: which graph entities a command may target
focus: which DOM/editor owner receives native input
command context: which route/surface may interpret a key as an application command
```

The current clone already has useful islands:

- node selection is projected through `selectedNodeIds/selectedNodeId` instead of being kept in stored node data;
- active image tools consume page keys in capture phase;
- editable targets skip the ordinary page dispatcher;
- Director owns a full-screen focus root and blocks ordinary page shortcuts;
- local video/picture tools consume Escape before the page handler;
- Batch 58 reconciles selected node-bound UI owners across delete/switch.

The same runtime still has cross-cutting gaps:

- edge selection remains in stored edge records while node selection is session state;
- node selection has three write paths and no explicit primary-order contract;
- a foreground button or visually modal surface does not automatically suspend canvas commands;
- Character/History are pointer-modal but not keyboard-modal;
- Canvas dropdown and page Escape can both handle one event;
- Preview/Director acquire focus without a general close-return policy;
- organize confirmation can coexist with later graph commands that invalidate its before/after meaning;
- selection, focus and shortcut docs previously drifted behind Batch 50 runtime.

The contract target is:

```text
raw pointer / keyboard / framework event
  -> resolve active route + canvas generation
  -> resolve validated selection snapshot
  -> resolve event target focus zone + foreground surface context
  -> classify local/native/route command ownership
  -> HANDLED | CONSUMED | PASS | BLOCKED | NOOP
  -> named command with captured selection/owner
  -> typed outcome + feedback
  -> deterministic selection/focus reconciliation
```

This document composes rather than replaces:

- [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md);
- [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md);
- [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md);
- [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md);
- [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md);
- [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md);
- [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md);
- [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md).

## 2. Evidence And Claim Boundary

### 2.1 `OPEN_CANVAS_FACT`

Fixed Open Canvas directly establishes:

- node and edge selection are React Flow record flags;
- selected-node editor, selected count, clipboard and delete use different projections of those flags;
- conflict gating blocks all node/edge changes, including selection variants;
- document copy/paste skips input, textarea, select, contenteditable and role-textbox targets, and pauses during image preview;
- title/note/text editors own local focus and Enter/Escape commit/cancel;
- Quick Add Escape closes from a document bubble listener without propagation ownership;
- dialogs and dropdowns delegate substantial focus/keyboard mechanics to fixed Radix primitives;
- there is no single app-level shortcut dispatcher for undo/tool/group/duplicate/zoom.

Evidence IDs: `OC-046..052`. Detailed paths and boundaries are in the [dated static audit](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md#3-fixed-open-canvas-findings).

These facts do not prove LibTV source shortcuts, modal focus, visual skin or product policy.

### 2.2 `CLONE_FACT`

The fixed clone directly establishes:

- node session selection is projected into React Flow nodes and stripped before stored-node writeback;
- `onNodesChange`, `onSelectionChange` and `onNodeClick` can all write node selection;
- `selectNodes` validates active node IDs while `selectNode` accepts the supplied ID;
- edge selection passes through generic `onEdgesChange` into stored edge records;
- page Delete reads only node selection;
- active image surfaces use capture-phase `stopImmediatePropagation`;
- ordinary editable guard omits `select` and role textbox;
- Director active blocks the complete ordinary page dispatcher;
- Character/History have pointer backdrops without focus modality;
- Preview and Director establish focus owners but no cross-surface focus-return rule.

Detailed evidence: [dated static audit](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md#4-current-clone-selection-findings).

### 2.3 `RECORDED_RUNTIME`

- Batch 50 verifies Director workspace focus ownership and background page shortcut isolation;
- Batch 58 verifies node-bound owner invalidation on delete/switch;
- Batch 60 verifies one standard selected image owner across toolbar/panel and selection migration;
- earlier multi-selection/marquee batches verify bounded clone behavior but do not establish edge authority or source parity.

### 2.4 `INFERENCE`

The following are evidence-backed engineering inferences:

- node/edge selection needs one session projection before document sanitation and mixed-selection commands are reliable;
- z-index, backdrop and component names cannot determine keyboard ownership;
- event-target editable checks are necessary but insufficient when a foreground surface remains active without focus;
- one Escape should resolve one declared top context before the page clears unrelated state;
- focus return needs owner identity because the opener may be deleted, switched away or unmounted;
- stale async completion must not steal current selection or focus;
- conflict/read-only mutation blocking should not automatically freeze inspect-only selection.

### 2.5 `DECISION`

The selection snapshot, context taxonomy, dispatch result, policy matrix, focus return order, invariants, fixture and verifier are clone-only correctness decisions. Exact LibTV key chords, modal semantics, focus ring, animation and whether a source surface blocks a particular command remain source-gated where identified.

### 2.6 Explicit exclusions

- no global modal manager is introduced by this document;
- no Radix dependency or Open Canvas visual is adopted;
- no FrameOS selection/toast/store state is reused;
- no selection state enters semantic graph history or portable document;
- no source-only shortcut is implemented;
- no ARIA/focus claim is upgraded to source parity from clone-only behavior;
- no code, test or source interaction is authorized.

## 3. Selection Authority

### 3.1 Canonical active selection snapshot

Conceptual shape:

```ts
type LibTVSelectionRef =
  | { kind: "node"; id: string }
  | { kind: "edge"; id: string };

type LibTVSelectionSnapshot = {
  route: "libtv";
  canvasId: string;
  canvasGeneration: number;
  nodeIds: string[];
  edgeIds: string[];
  primary: LibTVSelectionRef | null;
  source: LibTVSelectionSource;
};
```

This is a design shape, not an instruction to add these exact TypeScript names.

### 3.2 Selection sources

| Source | Meaning | Primary rule |
|---|---|---|
| `POINTER_SINGLE` | unmodified node/edge click | clicked entity |
| `POINTER_TOGGLE` | modified click adds/removes | last explicitly added entity; deterministic fallback when removed |
| `MARQUEE` | framework selection rectangle | last framework anchor if available; otherwise stable final item |
| `FRAMEWORK_RECONCILE` | React Flow select variants | preserve valid primary when still selected |
| `COMMAND_RESULT` | duplicate/create/process explicitly selects output | command-declared entity only |
| `RESTORE_CLEAR` | undo/redo/load invalidates selection | null |
| `CANVAS_SWITCH_CLEAR` | active canvas changes | null under current clone policy |
| `OWNER_DELETE_RECONCILE` | selected entity removed | surviving deterministic fallback or null |
| `SOURCE_PARITY_OVERRIDE` | future proven source transition | must cite source evidence and verifier |

### 3.3 Selection invariants

| ID | Invariant |
|---|---|
| `LIBTV-SFC-I-001` | snapshot `canvasId/generation` equals the active session at commit |
| `LIBTV-SFC-I-002` | node and edge IDs are unique, ordered and exist in that active graph |
| `LIBTV-SFC-I-003` | `primary` is null iff both ID lists are empty |
| `LIBTV-SFC-I-004` | non-null `primary` belongs to exactly one selected list |
| `LIBTV-SFC-I-005` | selection is not a portable document field or semantic history payload |
| `LIBTV-SFC-I-006` | React Flow `selected` is a projection/transport field, not semantic graph authority |
| `LIBTV-SFC-I-007` | node and edge selection use one active-session authority |
| `LIBTV-SFC-I-008` | malformed or stale IDs are removed before any command reads selection |
| `LIBTV-SFC-I-009` | a command captures its selection snapshot before planning graph effects |
| `LIBTV-SFC-I-010` | reject/noop/stale/unknown command outcomes do not change selection unless explicitly specified by a non-graph UI command |
| `LIBTV-SFC-I-011` | async completion cannot select/focus output unless its canvas/generation/operation owner is current and the command contract allows it |
| `LIBTV-SFC-I-012` | canvas switch and active delete follow one declared selection cleanup path |
| `LIBTV-SFC-I-013` | inactive canvas records contain no selected runtime flags after document projection |
| `LIBTV-SFC-I-014` | focus and selection may differ; focused control does not become graph primary implicitly |
| `LIBTV-SFC-I-015` | mixed node/edge selection commands declare accepted entity kinds before mutation |

### 3.4 Primary selection semantics

`primary` answers “which selected entity owns a single-entity inspector or action,” not “which DOM element is focused.”

Rules:

1. a plain click replaces selection and sets clicked entity primary;
2. additive selection makes the last explicitly added entity primary;
3. removing the primary chooses the most recently retained valid entity by declared order, otherwise null;
4. marquee must not depend on object-map iteration order;
5. a node-only editor mounts only when `nodeIds.length === 1`, `edgeIds.length === 0` unless source evidence explicitly allows mixed primary;
6. a command-created output becomes primary only when that command contract says so;
7. focus restoration to an owner node does not mutate graph selection unless the close contract explicitly requires reselecting it.

Current source parity for mixed node+edge selection is `UNKNOWN`; the correctness default is not to show a single-node editor for a mixed selection.

### 3.5 Framework routing

React Flow selection variants are T0 transport described by [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md). They should be converted into one selection proposal and committed once.

The following current duplication is not the target:

```text
onNodesChange(select) -> selectNodes
onSelectionChange     -> selectNodes
onNodeClick            -> selectNode
```

Implementation may retain multiple event sources only if they converge through one pure proposal reducer and have a deterministic precedence test. Whole-batch malformed/semantic rejection must not partially update selection.

### 3.6 Command input snapshot

Before a graph command runs, capture:

```text
route
canvasId + generation
nodeIds + edgeIds + primary
command context ID
event/chord source
```

Delete, duplicate, group, copy, organize, process and future Option-drag then declare which selection kinds they accept. They must not re-read “whatever is selected now” after an async boundary.

## 4. Focus And Command Context Model

### 4.1 Focus zone taxonomy

| Zone | Examples | Native/local priority |
|---|---|---|
| `BROWSER_NATIVE` | browser chrome/file picker, OS composition | application must pass |
| `EDITABLE` | input, textarea, select, contenteditable, role textbox, approved editor root | native text/editor commands first |
| `NODE_EDITOR` | prompt editor, rename field, local title/body editor | local commit/cancel before canvas |
| `TARGET_SCOPED_SURFACE` | Agent/Asset drawer, node toolbar/panel, anchored tool surface | commands originating inside surface stay local or block canvas |
| `POPOVER_MENU` | Canvas dropdown, Add Node, Zoom, Shortcuts, local menus | foreground menu command policy |
| `MODAL` | Character, History, future blocking dialogs | suspend background canvas commands |
| `ACTIVE_TOOL` | Preview, Annotate, Element Edit, video/picture local editor | local exclusive command vocabulary |
| `DIRECTOR` | Director root and nested viewer/panels | route-local exclusive workspace |
| `CANVAS` | React Flow pane/node/edge without foreground exclusive surface | ordinary selection/graph/viewport commands |

### 4.2 Context descriptor

Conceptual fields:

```text
contextId
kind
route
canvasId + generation
surfaceId
ownerNodeId?
parentContextId?
keyboardPolicy
focusPolicy
openedFromElement?
```

This does not require one global React context. It requires each mounted foreground surface to expose enough identity for a resolver and verifier.

### 4.3 Context policy modes

| Policy | Meaning |
|---|---|
| `ROUTE_EXCLUSIVE` | only workspace/local commands; ordinary LibTV canvas dispatcher is suspended |
| `LOCAL_EXCLUSIVE` | active tool consumes declared keys and blocks all canvas commands |
| `SUSPEND_CANVAS` | foreground modal/menu handles local commands and blocks background graph/tool/viewport shortcuts |
| `TARGET_SCOPED` | events from inside the surface do not become canvas commands; canvas-origin events may continue |
| `CANVAS_ACTIVE` | ordinary canvas command map may run |
| `PASS_NATIVE` | browser/editor owns the event |

### 4.4 Context precedence

Resolve from most specific to broadest:

```text
IME/browser-native owner
  -> event-target local editor
  -> active-tool capture owner
  -> Director nested owner
  -> Director workspace
  -> topmost modal
  -> topmost popover/menu
  -> target-scoped drawer/node surface
  -> ordinary canvas
  -> browser fallback
```

Z-index is evidence for visual ordering, not the resolver itself. The resolver uses mounted owner state and event target containment.

### 4.5 Surface policy matrix

| Surface family | Target policy | Selection visibility | Initial focus | Close return |
|---|---|---|---|---|
| Character / History | `SUSPEND_CANVAS` | preserve session selection but do not act on it | first meaningful control or dialog root | opener if valid, else canvas root |
| Preview / Annotate / Element Edit | `LOCAL_EXCLUSIVE` | owner node remains selected per current contract | declared local control/stage | owner node control if valid, else canvas root |
| Director | `ROUTE_EXCLUSIVE` | graph selection preserved/reconciled; local object selection separate | workspace root, then nested local rules | exported/source node affordance if valid, else canvas root |
| Canvas dropdown / Add Node / Zoom | `SUSPEND_CANVAS` while open | preserve selection | trigger/first local target as source requires | trigger if valid, else canvas root |
| Shortcuts | `SUSPEND_CANVAS` | preserve selection | close button/panel root under clone accessibility decision | trigger if valid |
| Agent / Asset drawer | `TARGET_SCOPED` | may inspect/change selection by named actions | current local editor/control behavior | no forced return while canvas remains visible |
| Node toolbar/panel | `TARGET_SCOPED` | owner selection required | focused child owns native/local keys | owner node or canvas fallback |
| Organize confirmation | `SUSPEND_CANVAS` for graph-mutating commands | preserve operation snapshot selection separately | explicit keep/restore controls if focus policy is added | canvas root/current valid selection |
| Ordinary canvas | `CANVAS_ACTIVE` | active selection | canvas/node/edge as framework supports | n/a |

The exact source behavior of Character/History/Shortcuts focus remains unknown. `SUSPEND_CANVAS` is the clone correctness and accessibility floor for visually blocking surfaces, not a LibTV source claim.

### 4.6 Editable target predicate

The predicate should cover at least:

- `input:not([type=button], [type=submit], [type=reset])` as appropriate;
- `textarea`;
- `select`;
- contenteditable true/plaintext/editor roots;
- role textbox/searchbox/combobox where editing is real;
- project-declared code/rich-text editors;
- shadow/editor integration through an explicit adapter if introduced.

Do not classify all buttons, sliders or menuitems as editable. They belong to a surface command context that blocks or handles relevant canvas shortcuts.

IME composition is always local/native. Enter/Escape during composition must not commit/cancel unless the editor contract explicitly proves the desired behavior.

## 5. Dispatch Result And Command Classes

### 5.1 Dispatch result

| Result | Meaning | Default/propagation policy |
|---|---|---|
| `HANDLED` | a named local/route command ran | prevent browser default when collision exists; stop only as required by owner |
| `CONSUMED` | context intentionally absorbs key without command | prevent collision; exclusive owner may stop propagation |
| `PASS` | current layer declines; next layer/native may handle | no prevent/stop |
| `BLOCKED` | command recognized but forbidden in context | prevent unsafe/default action; project feedback may be silent or owner-local |
| `NOOP` | valid command with no eligible target/effect | follow command feedback contract; no graph/history residue |

`stopImmediatePropagation` is reserved for exclusive capture owners with a documented reason. It is not the default implementation of context priority.

### 5.2 Command classes

| Class | Examples | Normal owner |
|---|---|---|
| `NATIVE_EDIT` | text copy/paste/delete, IME, select navigation | browser/editor |
| `LOCAL_EDITOR` | commit/cancel rename, brush/tool key, Director local command | local surface |
| `SURFACE_LIFECYCLE` | close top popover/modal, switch local tab | foreground surface |
| `SELECTION` | clear, select all future, marquee/toggle | canvas session |
| `GRAPH_MUTATION` | delete, duplicate, group, undo/redo | named graph command |
| `VIEWPORT` | pan tool, zoom, fit view | active canvas viewport |
| `ROUTE_MODE` | enter/exit Director, workbench/storyboard | route/workspace owner |
| `CLIPBOARD_GRAPH` | copy/paste subgraph | canvas session + clipboard contract |

### 5.3 Dispatch pipeline

```text
normalize event/chord
  -> if composing/native: PASS_NATIVE
  -> resolve local editor/active tool/Director owner
  -> resolve modal/menu/target-scoped policy
  -> match allowed command class
  -> capture canvas/selection/context owner
  -> HANDLED | CONSUMED | BLOCKED | PASS | NOOP
  -> command outcome/feedback adapter
```

Matching a chord is not permission to run it. Context resolution happens first.

### 5.4 Current command decision matrix

| Input | `EDITABLE` | `MODAL/ACTIVE_TOOL/DIRECTOR` | `POPOVER_MENU` | `CANVAS` |
|---|---|---|---|---|
| Delete / Backspace | native/local | local or blocked | blocked unless local menu action | named mixed-selection delete |
| Tab | native focus/editor | local focus policy | local menu/panel focus | Add Node only if current source/shortcut contract allows |
| Space | native text/editor | local or consumed | consumed unless declared | temporary pan |
| Escape | local cancel/pass | close top local context only | close top menu only | clear selection/declared overlays |
| Meta/Ctrl+Z/Y | editor-local when supported | local or blocked | blocked | graph undo/redo |
| Meta/Ctrl+D | native/editor or local | blocked | blocked | duplicate captured selection |
| G / Shift+G | text/local | blocked | blocked | group/ungroup eligible selection |
| V / H | text/local | blocked | blocked | canvas tool selection |
| Meta/Ctrl+0/+/- | browser/editor decision | blocked unless local | blocked | viewport command |
| Copy/Paste | native editor | local/blocked | local/native | graph clipboard when payload eligible |

Exact LibTV source chords remain governed by [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md).

## 6. Escape And Close Ordering

### 6.1 One Escape, one top context

Default resolution:

```text
IME/editor local Escape
  -> active image/video/picture tool
  -> Director nested viewer/panel
  -> Director workspace
  -> top modal
  -> top popover/menu
  -> ordinary page overlay policy
  -> selection clear
  -> PASS
```

One event closes at most one top context unless current source evidence explicitly proves a compound close.

### 6.2 Consume policy

- local cancel that changes a surface state returns `HANDLED`;
- exclusive active tools consume before page handling;
- a weak listener that closes a menu but lets page Escape also clear selection violates the target unless compound behavior is declared;
- busy/unsaved local state may return `BLOCKED` and keep focus;
- selection clear occurs only when no foreground context consumed Escape.

### 6.3 `closeAllPanels` boundary

`closeAllPanels` is a write-side convenience, not an Escape authority. A future dispatcher may call a specific close action or a named top-level policy result. It must not close Director, organize confirmation, node tool and unrelated modal merely because they are visually layered unless the contract says so.

## 7. Focus Lifecycle

### 7.1 Open

On a context that acquires focus:

1. capture opener identity as a DOM ref/selector plus route/canvas/node owner where applicable;
2. mount the surface;
3. on the next stable frame, focus the declared initial target with `preventScroll`;
4. do not mutate graph selection merely to prove focus;
5. expose a verifier marker for context and focus owner.

### 7.2 Containment

| Context | Requirement |
|---|---|
| Modal | focus stays within mounted modal until close, except browser-native dialogs |
| Active tool | local stage/controls own keyboard; canvas dispatcher suspended |
| Director | ordinary page dispatcher suspended; nested surfaces define local containment |
| Popover/menu | roving/local focus as applicable; background canvas commands suspended |
| Target-scoped drawer/panel | no full trap; events originating inside remain local |

### 7.3 Close return order

```text
still-connected explicit opener
  -> still-valid owner node affordance
  -> current canvas focus root
  -> route root
  -> no forced focus when browser-native owner took over
```

If opener canvas/generation is stale, do not focus it. If the owner node was deleted, use current canvas root. Focus return does not resurrect selection, UI owner or graph data.

### 7.4 Canvas switch and delete

- active surface with old canvas owner closes before focus return;
- no focus call may target an inactive canvas DOM subtree;
- canvas switch returns focus to the target canvas root unless a project-level foreground surface remains owner;
- deleting the focused/selected owner reconciles selection, closes invalid surface and then focuses a valid fallback;
- inactive document/history records remain unaffected.

### 7.5 Undo/redo and async completion

- current clone undo/redo clears selection; target contract keeps this compatibility until separately decided;
- focus should return/remain on the canvas root, not an unmounted selected node;
- async completion cannot move focus;
- async completion may change selection only through an explicit current-owner command result and never from stale/duplicate disposition.

## 8. Selection And Focus Transition Catalog

| Transition | Selection result | Focus/context result | Graph/history |
|---|---|---|---|
| plain node click | one node primary | canvas/node context | none |
| modified node click | ordered toggle | canvas/node context | none |
| marquee | validated node/edge set | canvas context | none |
| pane click | clear under current clone policy | canvas root/pane | none |
| open node panel | preserve owner selection | target-scoped surface | none |
| open modal | preserve selection | modal acquires focus, canvas suspended | none |
| close modal | preserve/reconcile selection | opener/owner/canvas fallback | none |
| enter active image tool | owner node remains sole selected | local exclusive | none at entry unless command contract says otherwise |
| close active image tool | preserve valid owner selection | owner/canvas fallback | tool-specific commit/cancel only |
| enter Director | preserve source selection/session | route exclusive | route command only |
| exit Director | command-declared source/export selection | owner/canvas fallback | Director output command if any |
| undo/redo | clear compatibility policy | canvas root | one history restore |
| duplicate | output IDs primary per command | canvas context | one graph history entry |
| delete selection | surviving deterministic fallback/null | canvas root or valid owner | one planned delete history entry |
| canvas switch | clear current clone selection | target canvas root | zero graph history |
| stale async completion | unchanged | unchanged | zero |

## 9. Context Invariants

| ID | Invariant |
|---|---|
| `LIBTV-SFC-I-016` | at most one route-exclusive or local-exclusive context is top authority |
| `LIBTV-SFC-I-017` | visual z-index alone never grants command authority |
| `LIBTV-SFC-I-018` | event-target editable/native owner resolves before canvas chord matching |
| `LIBTV-SFC-I-019` | pointer-modal surfaces also suspend destructive canvas commands under clone correctness policy |
| `LIBTV-SFC-I-020` | one Escape changes at most one top context unless explicitly specified |
| `LIBTV-SFC-I-021` | `HANDLED/CONSUMED/BLOCKED` policy determines prevent/propagation behavior |
| `LIBTV-SFC-I-022` | exclusive capture owners are explicit and cannot be created by arbitrary component listeners |
| `LIBTV-SFC-I-023` | opener/focus return target carries route/canvas/owner validity |
| `LIBTV-SFC-I-024` | focus return never resurrects deleted selection or surface state |
| `LIBTV-SFC-I-025` | Director active suspends every ordinary LibTV page command |
| `LIBTV-SFC-I-026` | FrameOS listeners/state are outside ordinary LibTV context resolution |
| `LIBTV-SFC-I-027` | selection/focus/context-only changes produce zero semantic graph history |
| `LIBTV-SFC-I-028` | modal/menu open does not silently clear graph selection unless its product transition requires it |
| `LIBTV-SFC-I-029` | pending organize or other reversible route transaction declares which later commands are blocked |
| `LIBTV-SFC-I-030` | command outcome feedback is projected in the resolved owner context, not whichever surface is current later |

## 10. Composition With Existing Authorities

### 10.1 React Flow routing

- node and edge `select` variants become one T0 selection proposal;
- selected runtime flags are stripped at history/document/copy boundaries;
- semantic add/remove/replace/reconnect never enter selection reducer;
- whole-batch reject leaves selection unchanged.

### 10.2 Graph commands and history

- command captures validated selection before planning;
- delete/copy/group/duplicate declare node/edge acceptance;
- one accepted graph transaction creates one history entry;
- selection result is transaction output, not history payload;
- no-op/reject/unknown leave selection/focus unless an explicit UI outcome says otherwise.

### 10.3 Multi-canvas lifecycle

- selection snapshot includes canvas generation;
- switch/delete reconciles context and focus target;
- page-local listeners cannot late-write/focus old owners;
- project-level surface policy is declared separately from canvas-bound surface policy.

### 10.4 Async ingress

- completion carries canvas/operation owner;
- selection/focus is not derived from active canvas at settle time;
- stale/duplicate completion has zero selection/focus effect;
- resource result visibility and feedback do not imply auto-focus.

### 10.5 Feedback ownership

- `BLOCKED` may be silent for obvious foreground modality or use owner-local guidance if source/product requires;
- editable/native pass has no canvas error;
- command `NOOP/REJECTED` uses stable reason, not DOM focus string;
- focus changes are not success feedback;
- announcements use the command's captured owner and never steal focus by default.

## 11. Current Runtime Mapping

| Area | Current maturity | Keep | Missing target |
|---|---|---|---|
| node selection | runtime partial | separate session IDs and stored-node sanitation | one ingress reducer, primary contract, edge composition |
| edge selection | runtime gap | React Flow visual behavior as evidence | separate session owner, command input, document sanitation |
| active image tools | runtime partial | capture isolation and owner selection reconciliation | narrower declared command vocabulary, focus return |
| editable guard | runtime partial | input/textarea/contenteditable priority | select/role/editor corpus and surface context |
| Director | recorded partial | complete page dispatcher suspension and workspace focus owner | full/nested containment, return target, source parity |
| Character/History | runtime gap | backdrop pointer behavior | keyboard modality, initial/return focus |
| Shortcuts/menu/dropdown | runtime gap | local close/render behavior | command suspension, one-Escape rule, return focus |
| organize confirmation | runtime gap | reversible node/viewport snapshot | block/compose policy for later graph commands |
| FrameOS | isolated route | separate store/listeners | no shared command manager |

## 12. Decision Queue

| ID | Question | Default until decided | Evidence needed |
|---|---|---|---|
| `LIBTV-SFC-DQ-001` | Does source allow mixed node+edge primary editor? | no single-node editor for mixed selection | disposable source selection fixture |
| `LIBTV-SFC-DQ-002` | Exact selection order after marquee/toggle? | deterministic insertion/explicit-anchor order | source + framework runtime audit |
| `LIBTV-SFC-DQ-003` | Character/History exact focus trap/return? | clone correctness modal containment | safe source modal inspection |
| `LIBTV-SFC-DQ-004` | Shortcuts source popover blocks canvas commands? | suspend canvas while foreground | source key/focus observation |
| `LIBTV-SFC-DQ-005` | Canvas dropdown Escape also clears selection? | one Escape closes dropdown only | source observation |
| `LIBTV-SFC-DQ-006` | Which anchored panels allow background canvas shortcuts? | target-scoped; event inside blocks canvas | source + local ergonomics fixture |
| `LIBTV-SFC-DQ-007` | Undo/redo should restore selection? | preserve current clear-on-restore behavior | LibTV source and product decision |
| `LIBTV-SFC-DQ-008` | Delete selection supports selected edges with nodes? | design supports both through delete planner; source parity unknown | disposable source graph fixture |
| `LIBTV-SFC-DQ-009` | Modal open should clear node surface visually? | preserve selection, foreground modal owns commands | source z-index/selection audit |
| `LIBTV-SFC-DQ-010` | Organize confirmation blocks which commands? | block graph mutation/history restore until keep/restore | clone product decision and fixture |
| `LIBTV-SFC-DQ-011` | Focus target after Director return? | export/source affordance then canvas fallback | source Director fixture |
| `LIBTV-SFC-DQ-012` | Should focus ring differ from graph selected ring? | keep separate state/visual identity | source visual evidence/accessibility decision |

Open decision does not permit arbitrary component behavior. The stated default is the design fallback for future authorized work and must remain labeled clone-only where source is unknown.

## 13. Local Fixture Contract

Fixture ID: `LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01`.

### 13.1 Topology and owners

Use a deterministic local active canvas A with:

- two ordinary nodes `A-N1/A-N2`;
- one group + child `A-G1/A-C1`;
- edges `A-E1` internal and `A-E2` external/mixed;
- selected-node standard surface support;
- Character, History, Shortcuts, Canvas dropdown, Preview, one active image tool and Director entry;
- editable corpus: input, textarea, select, contenteditable, role textbox and button;
- second canvas B with disjoint IDs;
- explicit canvas generation and reset.

No provider, upload, persistence, payment or source-site state is used.

### 13.2 Selection cases

| Case | Action | Expected |
|---|---|---|
| `SFC-S01` | plain select N1 | nodeIds N1, primary N1, zero history |
| `SFC-S02` | add N2, remove N1 | deterministic order/primary N2 |
| `SFC-S03` | select E1 | edgeIds E1, primary E1, stored semantic edge has no selected flag |
| `SFC-S04` | mixed N1 + E1 | declared mixed snapshot; no single-node editor by default |
| `SFC-S05` | marquee group/child | valid deterministic IDs, zero history |
| `SFC-S06` | malformed/stale ID | filtered/reconciled, no surface owner |
| `SFC-S07` | undo/redo | selection clears under compatibility policy, canvas focus valid |
| `SFC-S08` | switch A -> B -> A | selection clear each switch; graph/history exact |
| `SFC-S09` | delete primary | planner result + deterministic fallback/null; focus valid |
| `SFC-S10` | stale async completion | no selection/focus steal |

### 13.3 Command-context cases

| Case | Context/input | Expected |
|---|---|---|
| `SFC-C01` | canvas Delete with node/edge selection | one named delete command |
| `SFC-C02` | editable Delete/undo/copy/paste | native/local; zero canvas command |
| `SFC-C03` | button inside foreground surface + Delete/Tab/G | local/blocked; zero graph/tool change |
| `SFC-C04` | Character/History + canvas shortcuts | background suspended |
| `SFC-C05` | Shortcuts + Escape | close one panel; selection unchanged |
| `SFC-C06` | Canvas dropdown + Escape | close dropdown only; no page compound effect |
| `SFC-C07` | active image tool + key corpus | local exclusive; only Escape closes |
| `SFC-C08` | Director + page key corpus | ordinary page dispatcher zero calls |
| `SFC-C09` | Director nested viewer + Escape | nested closes before workspace |
| `SFC-C10` | organize pending + graph command | blocked/no residue until resolve |
| `SFC-C11` | Space keydown then blur/visibility/switch | temporary pan always resets |
| `SFC-C12` | IME composition + Enter/Escape | editor-local; no canvas command |

### 13.4 Focus cases

| Case | Transition | Expected focus |
|---|---|---|
| `SFC-F01` | open/close modal | initial target, containment, opener return |
| `SFC-F02` | opener removed before close | current canvas root fallback |
| `SFC-F03` | canvas switch while surface open | no inactive DOM focus; target canvas root |
| `SFC-F04` | Preview open/Tab/close | bounded local loop and owner/opener fallback |
| `SFC-F05` | Director enter/nested/exit | workspace/nested/local order, valid return |
| `SFC-F06` | delete focused selected node | surface closes; canvas fallback; no stale activeElement |

### 13.5 Reset and isolation

Every browser case starts from a fresh Page or deterministic reset that restores:

- canvas A/B graph and generation;
- empty selection and edge runtime flags;
- no foreground surfaces;
- no temporary pan/listener residue;
- focus on known canvas root;
- no Director/local timer/storage residue.

Undo is not teardown. FrameOS runs in a separate route case and must not observe ordinary LibTV state.

## 14. Verifier Contract

Verifier ID: `LIBTV-VR-019`.

### 14.1 Pure contract layer

Future pure tests should validate:

- selection normalization and primary fallback;
- context precedence and policy resolution;
- command class permission;
- Escape top-context reduction;
- focus return target selection from owner validity;
- canvas/generation reconciliation;
- transition and invariant tables.

### 14.2 Focused browser layer

Future Playwright should record:

- active element before/open/during/after surface lifecycle;
- node/edge/primary selection snapshot;
- graph/history/viewport/UI deltas;
- event default/propagation outcome via observable command counters, not monkey-patched browser internals;
- context owner markers and canvas generation;
- desktop and mobile cases where surface policy differs;
- console/page/request errors.

### 14.3 Composition

`VR-019` composes with:

- `VR-011` subgraph copy;
- `VR-013` delete/reference repair;
- `VR-015` async convergence;
- `VR-016` React Flow routing;
- `VR-017` multi-canvas lifecycle;
- `VR-018` outcome feedback;
- Batch 50 Director and Batch 58/60 UI owner verifiers.

It does not replace their graph, source, geometry or resource semantics.

## 15. Authorized Implementation Slices

No slice is currently authorized. If authorization is later granted, use this order:

### Slice A: pure selection/context model

- fixture model and pure normalizers;
- node/edge/primary invariants;
- context policy and dispatch result reducer;
- no visual redesign.

### Slice B: framework selection convergence

- route node/edge select variants through one active-session authority;
- sanitize selected runtime fields;
- preserve current visible node selection behavior;
- focused mixed-selection fixture.

### Slice C: foreground command suspension

- Director recorded behavior stays intact;
- correct Character/History/Shortcuts/Canvas dropdown command policy;
- one-Escape rule;
- do not introduce new source-unproven shortcuts.

### Slice D: focus lifecycle

- initial focus and containment for declared modal/exclusive contexts;
- opener/owner/canvas return;
- switch/delete fallback;
- accessibility assertions without claiming source visual parity.

### Slice E: source-parity refinements

- only after current LibTV source evidence;
- update decision queue, contracts and verifier before implementation;
- preserve clone correctness floor unless source behavior and explicit product decision justify a change.

Each slice requires its own plan, implementation history, verifier output, screenshot/DOM evidence where visual, and commit/push.

## 16. Open Canvas Adoption Boundary

Adopt or adapt:

- local editor owns commit/cancel keys;
- editable/native operations resolve before graph clipboard;
- foreground preview can suspend graph commands;
- selection projections must be explicit per command;
- mature dialog/menu primitives can own focus mechanics when the project deliberately chooses them.

Reject transplant:

- selected flags as portable graph/session authority;
- conflict gate automatically freezing inspect selection;
- weak Escape listener in a multi-listener app;
- framework default destructive keys as product command policy;
- Radix dependency/skin without local architecture and source justification;
- Open Canvas shortcut absence as evidence for LibTV behavior.

## 17. Source Evidence Queue

Safe read-only source research should prioritize:

1. Character/History/Share/Agent/Shortcuts initial focus and Tab containment;
2. Escape ordering with Canvas dropdown and another selected node surface;
3. Delete/undo/Tab while a foreground non-editable control is focused;
4. mixed node/edge selection and selected-node panel behavior;
5. selection after undo/redo, duplicate, delete and active tool close;
6. Director enter/exit/nested focus if a disposable source fixture exists;
7. focus ring versus graph selection ring.

Stop before any shared graph mutation, provider task, upload, payment or irreversible account preference. Source observation can change parity decisions but does not authorize code.

## 18. Completion Criteria

The selection/focus/context slice is complete only when:

- node, edge and primary selection have one active-session authority;
- selection runtime flags do not enter portable graph/history;
- every target surface declares context and keyboard policy;
- editable/native/local/route/canvas precedence is deterministic;
- one Escape resolves one top context;
- modal/exclusive surfaces have initial/contain/return behavior;
- switch/delete/undo/async leave valid selection and activeElement;
- Director isolation remains recorded and FrameOS remains separate;
- source-unknown choices remain labeled clone-only;
- `LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01` and `LIBTV-VR-019` pass;
- adjacent graph/overlay/canvas/feedback verifiers and repository checks pass;
- research, implementation, verification and commit/push history are recorded.

Current conclusion:

> Open Canvas is useful here because it shows both explicit local editor ownership and the limits of embedding selection/deletion in framework defaults. The LibTV clone should preserve its stronger node-session and Director islands, then converge edge selection, foreground command policy and focus return through one declared context model. Selection is not focus; focus is not permission; a chord is not a command until its current owner accepts it.
