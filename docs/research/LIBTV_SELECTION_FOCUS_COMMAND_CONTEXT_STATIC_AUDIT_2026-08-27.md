# LibTV Selection, Focus And Command Context Static Audit

> Audit date: 2026-08-27.
>
> Clone baseline: `7eef1cb`. Open Canvas baseline: `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> Status: `STATIC_AUDIT_COMPLETE` / `DESIGN_NOT_YET_AUTHORIZED` / `SOURCE_PARITY_PARTIAL`.
>
> Scope: ordinary LibTV selection projection, DOM focus, keyboard listener precedence, top-level/local/Director command contexts, and the positive and negative methods available from fixed Open Canvas.
>
> Authorization boundary: this audit records facts, inferences, risks and a design queue. It does not authorize changes to `src/`, tests, FrameOS, either submodule or a source website.

## 1. Why This Audit Exists

The repository already documents shortcut labels, overlay mount owners, graph transactions and Director keyboard isolation. It does not yet have one authority that answers all of these questions together:

1. Which node or edge selection is current, and which item is primary?
2. Is selection graph data, active-canvas session state or framework transport state?
3. Which DOM focus target owns `Delete`, `Tab`, `Space`, `Escape`, undo and duplicate?
4. Does a visible modal, drawer, menu or node editor suspend canvas commands?
5. Which listener wins when capture-phase local tools and bubble-phase page handlers observe the same event?
6. Where does focus move on open, close, canvas switch, node delete and Director return?
7. Which current statements describe the runtime now, and which still describe the pre-Batch-50 clone?

Without that authority, a UI fidelity change can accidentally become a graph correctness change. Typical failure modes are:

- pressing Delete on a focused button deletes a selected graph node behind the surface;
- edge selection is persisted through a generic graph writer while node selection is session-only;
- two selection callbacks disagree about the primary item;
- a local Escape handler closes its tool and the page handler also clears unrelated state;
- a modal looks blocking but never takes focus or suspends canvas commands;
- closing a workspace leaves focus in an unmounted subtree;
- documentation keeps reporting a shortcut leak that current code has already fixed.

This audit fixes the evidence baseline before a formal command-context contract is written.

## 2. Claim Vocabulary And Method

| Label | Meaning |
|---|---|
| `OPEN_CANVAS_FACT` | Directly visible in fixed Open Canvas source or lockfile. |
| `CLONE_FACT` | Directly visible in clone source at `7eef1cb`. |
| `RECORDED_RUNTIME` | Already covered by a dated clone verifier or runtime record. |
| `INFERENCE` | A consequence supported by facts but not proven in a browser scenario. |
| `SOURCE_UNKNOWN` | LibTV source-site behavior is not established. |
| `DESIGN_QUESTION` | Must be decided before implementation, but is not a current fact. |

Method:

1. locate all page-level and component-level keyboard listeners;
2. follow React Flow selection changes into each store writer;
3. separate node, edge, primary and surface selection;
4. inventory editable-target guards and listener phases;
5. identify focus acquisition, trapping and restoration behavior;
6. compare fixed Open Canvas methods without treating its product behavior as LibTV truth;
7. cross-check existing Batch 50 and overlay records for stale statements.

No browser interaction, source mutation, build, test or submodule update was required for this static audit.

## 3. Fixed Open Canvas Findings

### 3.1 Selection is embedded in React Flow node and edge records

`OPEN_CANVAS_FACT`:

- `selectedNodes` is derived from `nodes.filter(node.selected)`;
- `selectedNode` exists when exactly one node is selected;
- `selectedCount` sums selected nodes and selected edges;
- clipboard payload uses all selected nodes and only edges internal to that selected-node set;
- `deleteSelection` removes selected nodes, selected edges and incident edges;
- pane, node and edge context menus use different explicit menu targets.

Evidence:

- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3702)
- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3896)
- [`canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L594)
- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L2959)

The model has useful closure semantics for copy/delete, but it also mixes four concepts in framework records:

```text
node.selected / edge.selected
  -> active visual selection
  -> command input
  -> selected-node editor projection
  -> serialized/runtime graph object shape
```

`INFERENCE`: `selectedNode` ignores edge count. One selected node plus one selected edge still produces a non-null selected-node editor, while `selectedCount` reports two. This is not automatically wrong, but it requires an explicit primary-selection rule before it is reused elsewhere.

### 3.2 Conflict gating also gates selection transport

`OPEN_CANVAS_FACT`: both `onNodesChange` and `onEdgesChange` return immediately when `conflictDetected` is true, then otherwise pass the complete change array to the generic React Flow reducer.

Evidence: [`canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L629).

Because selection is a `NodeChange` / `EdgeChange` variant, conflict mode blocks not only persistent graph mutation but also selection changes.

`INFERENCE`: Open Canvas therefore uses one authority gate for document mutation and active interaction state. LibTV should not copy this coupling without an explicit product decision. A conflict, read-only or busy canvas may still need inspectable selection even when mutation is blocked.

### 3.3 The global editable-target guard is narrow and purpose-specific

`OPEN_CANVAS_FACT`: `isEditableTarget` recognizes:

- `input`;
- `textarea`;
- `select`;
- `[contenteditable="true"]`;
- `[role="textbox"]`.

The fixed studio uses this guard for document-level copy/paste and also blocks canvas clipboard handling while `imagePreview` is open.

Evidence:

- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L226)
- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4402)

Positive method:

- canvas clipboard does not steal native text copy/paste from common editable controls;
- a page-level preview can suspend graph clipboard commands without mutating graph selection.

Limit:

- the guard is not a general command-context registry;
- it does not prove behavior for arbitrary ARIA widgets, code editors, sliders, menus or every modal;
- it says nothing about React Flow's own default delete handling.

### 3.4 Local editors own commit and cancel keys

`OPEN_CANVAS_FACT`: title, note and text editors use local `autoFocus` or contenteditable state, stop pointer propagation, and handle Enter/modified Enter and Escape themselves.

Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3301).

This is a useful interaction-layer pattern:

```text
editing mode
  -> local focus target
  -> local commit/cancel key
  -> graph update through a named callback
```

The pattern is stronger than checking only `event.target` in one page listener because it gives the editor an explicit local command vocabulary.

### 3.5 Quick Add Escape is an intentionally weak local listener

`OPEN_CANVAS_FACT`: while Quick Add is open, a document bubble-phase `keydown` listener closes it on Escape. It does not call `preventDefault`, `stopPropagation` or `stopImmediatePropagation`.

Evidence: [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4374).

`INFERENCE`: this is safe only while no competing global Escape command has incompatible side effects. It is a useful counterexample for LibTV, where multiple page and local listeners already coexist.

### 3.6 Dialog and dropdown semantics are delegated to Radix

`OPEN_CANVAS_FACT`: the fixed repository wraps `@radix-ui/react-dialog@1.1.17` and `@radix-ui/react-dropdown-menu@2.1.18` primitives. Canvas image/template dialogs and provider settings use these wrappers; list and shell menus use Radix dropdown primitives.

Evidence:

- [`dialog.tsx`](../../research/upstream/open-canvas/shared/components/ui/dialog.tsx#L9)
- [`dropdown-menu.tsx`](../../research/upstream/open-canvas/shared/components/ui/dropdown-menu.tsx#L9)
- fixed `package-lock.json`.

`INFERENCE`: default modal focus containment, Escape handling, menu roving focus and trigger focus restoration are primarily library-owned, except where call sites override primitive behavior. This audit does not claim a browser-proven focus sequence for every Open Canvas surface.

### 3.7 There is no unified application shortcut dispatcher

`OPEN_CANVAS_FACT`: fixed studio defines document listeners for clipboard and Quick Add Escape, plus local editor keys, but no app-level dispatcher equivalent to the clone's page handler for undo, tool selection, group, duplicate and zoom.

The fixed React Flow instance does not override `deleteKeyCode`. Context menus expose explicit delete-selection, delete-node and delete-edge actions.

Evidence:

- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4402)
- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6216)
- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L2959)

`INFERENCE`: some destructive keyboard semantics are delegated to React Flow defaults and browser focus behavior. That is a negative design input for LibTV, not a shortcut parity specification.

## 4. Current Clone Selection Findings

### 4.1 Node selection has a separate session projection

`CLONE_FACT`: canonical ordinary-canvas node selection is held as:

```text
selectedNodeIds: string[]
selectedNodeId: string | null
```

`page.tsx` projects those IDs back into React Flow nodes with `selected: selectedIds.has(node.id)`. Stored nodes are explicitly stripped of `selected` after generic node changes.

Evidence:

- [`page.tsx`](../../src/app/page.tsx#L148)
- [`page.tsx`](../../src/app/page.tsx#L218)
- [`canvasStore.ts`](../../src/store/canvasStore.ts#L2646)

This is stronger than embedding node selection in portable graph data. It already supports the intended rule that selection is active-canvas session state and not graph history input.

### 4.2 Node selection has three event ingress paths

`CLONE_FACT`: selection can reach the store through:

1. `onNodesChange` select variants;
2. React Flow `onSelectionChange`;
3. `onNodeClick` for non-modified clicks.

Evidence: [`page.tsx`](../../src/app/page.tsx#L218) and [`page.tsx`](../../src/app/page.tsx#L501).

`selectNodes` filters against active-canvas node IDs and deduplicates in received order. `selectNode` does not validate the ID. `selectedNodeId` is the last ID in `selectNodes`, but is exactly the supplied ID in `selectNode`.

`INFERENCE`: ordinary node selection is mostly convergent, but primary identity and ordering depend on which callback ran last. A formal contract must declare whether primary means last selected, clicked anchor, keyboard focus target or a separate field.

### 4.3 Edge selection has a different authority

`CLONE_FACT`:

- `onEdgesChange` applies all edge changes to stored edges;
- edge `selected` is therefore retained in the active canvas edge array;
- `onSelectionChange` ignores selected edges;
- page Delete reads only `selectedNodeIds/selectedNodeId`;
- no ordinary-canvas `selectedEdgeIds` session owner exists.

Evidence:

- [`page.tsx`](../../src/app/page.tsx#L240)
- [`page.tsx`](../../src/app/page.tsx#L395)
- [`page.tsx`](../../src/app/page.tsx#L501)

This is the highest-confidence static gap in this audit:

```text
node selection -> session store -> flow projection -> excluded from stored node data
edge selection -> generic edge reducer -> stored graph edge.selected
```

It affects graph document sanitation, delete command input, copy behavior, history assumptions and edge toolbar parity. It does not prove a visible runtime failure until a focused browser fixture exercises edge selection, canvas switch and document/history boundaries.

### 4.4 Selection is cleared by graph restore and canvas lifecycle

`CLONE_FACT`:

- undo and redo clear node selection;
- create/switch/active delete clear node selection;
- selected-node surfaces derive visibility from node selection count;
- Batch 58 reconciles node-bound UI owners after selection/delete/switch.

Evidence:

- [`canvasStore.ts`](../../src/store/canvasStore.ts#L2732)
- [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)
- [`liblib-canvas-batch58-2026-08-27/`](liblib-canvas-batch58-2026-08-27/)

Current documents do not define the equivalent edge-selection cleanup or the focus target after these transitions.

## 5. Current Clone Keyboard Context Findings

### 5.1 Page dispatcher precedence

`CLONE_FACT`: page startup registers:

```text
window keydown capture -> active image surface guard
window keydown bubble  -> ordinary canvas dispatcher
window keyup bubble    -> temporary-pan cleanup
```

The active image surface capture listener calls `stopImmediatePropagation()` for every key while Preview, Annotate or Element Edit is active. It prevents browser defaults for Escape, Delete, Backspace, Tab, Space and modified Z/Y/D, then gives only Escape a local close action.

Evidence: [`page.tsx`](../../src/app/page.tsx#L357).

This is a strong route-local isolation mechanism, but it is broader than a conventional focus trap: unrelated keys are swallowed even when a descendant could need them. Exact LibTV source parity remains unknown.

### 5.2 Ordinary editable-target guard is incomplete but explicit

`CLONE_FACT`: the page dispatcher skips:

- `input`;
- `textarea`;
- `[contenteditable='true']`;
- `[contenteditable='plaintext-only']`.

It does not include `select`, `[role='textbox']`, generic `contenteditable` presence or a surface context marker.

Evidence: [`page.tsx`](../../src/app/page.tsx#L379).

Compared with Open Canvas, clone coverage is narrower. This difference is method input only; it does not authorize blindly copying the Open Canvas selector. A future guard must be tested against local sliders, menus, buttons, Director controls and custom editors.

### 5.3 Director isolation is already implemented

`CLONE_FACT`: after the editable-target check, the ordinary page dispatcher immediately returns when `activeDirectorNodeId` exists. This blocks all ordinary page shortcuts, not only Escape.

Evidence: [`page.tsx`](../../src/app/page.tsx#L385).

`RECORDED_RUNTIME`: Batch 50 verifies workspace focus ownership and that Tab, Space, Delete and undo do not mutate the background canvas.

Evidence: [`liblib-canvas-batch50-2026-08-26/`](liblib-canvas-batch50-2026-08-26/).

Therefore these older statements are stale and must be corrected:

- `LIBTV_UIUX_PARITY_BACKLOG.md` says only Escape is isolated;
- `LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md` risk `UI-05` says other page shortcuts still leak.

Remaining Director gaps are narrower: no complete focus trap, no exact source focus contract, nested Escape ownership remains distributed, and explicit focus restoration to the opener is not documented.

### 5.4 Local Escape listeners have different authority levels

| Surface | Phase/target | Prevent/stop | Result |
|---|---|---|---|
| Active image Preview/Annotate/Element Edit | window capture | prevent selected defaults + `stopImmediatePropagation` for every key | Escape closes top active image surface; page dispatcher never sees event |
| Video continuation | window capture | `preventDefault` + `stopImmediatePropagation` on Escape | local cancel |
| Picture edit | window capture | same | local cancel |
| Subtitle erase | window capture | same | local cancel |
| Canvas dropdown | document bubble | no prevent/stop | closes dropdown; page Escape can also clear selection/other overlays |
| Director workspace | window bubble | `preventDefault`, no propagation stop | nested viewer/panel conditions decide whether workspace closes |

These are current facts, not a recommendation to normalize every listener. A formal contract must preserve source-specific local editor behavior while making precedence testable.

## 6. Current Clone Focus Findings

### 6.1 Image Preview has a bounded single-control focus loop

`CLONE_FACT`: Image Preview:

- mounts as `role="dialog"` + `aria-modal="true"`;
- focuses the close button on mount;
- redirects Tab to the same close button;
- handles local Escape.

Evidence: [`ImagePreviewOverlay.tsx`](../../src/components/ImagePreviewOverlay.tsx#L18).

This is deterministic for a one-control preview. It does not preserve and restore the previously focused element when closing.

### 6.2 Director has a workspace focus owner, not a complete trap

`CLONE_FACT`: Director root mounts as an ARIA modal dialog, receives programmatic focus and owns Escape layering. Closing selects the export result or source node before unmount.

Evidence: [`DirectorDesk.tsx`](../../src/components/director/DirectorDesk.tsx#L99) and [`DirectorDesk.tsx`](../../src/components/director/DirectorDesk.tsx#L262).

`RECORDED_RUNTIME`: Batch 50 explicitly says the root is a focus owner, not a complete focus trap.

There is no formal cross-cutting rule for whether close should focus the returned node, a canvas root, or the original trigger.

### 6.3 Pointer-modal top-level surfaces do not establish keyboard modality

`CLONE_FACT`: Character and History use a full-screen backdrop that closes on `mousedown`, while their inner `section` only has an accessible label and stops pointer propagation. They do not declare `role="dialog"`, `aria-modal`, initial focus, a focus loop or focus restoration.

Evidence:

- [`CharacterLibraryPanel.tsx`](../../src/components/CharacterLibraryPanel.tsx#L78)
- [`HistoryPanel.tsx`](../../src/components/HistoryPanel.tsx#L34)

`CLONE_FACT`: Keyboard Shortcuts is an anchored `section`, not a modal. It does not take focus or suspend page shortcuts.

Evidence: [`KeyboardShortcutsDialog.tsx`](../../src/components/KeyboardShortcutsDialog.tsx#L67).

The visual term “dialog” in a component name is therefore not enough to infer a command context.

### 6.4 Local rename inputs acquire focus but return behavior is implicit

Canvas/project rename inputs use `autoFocus`; project rename handles local Escape, while canvas rename handles Enter and commits on blur. Closing the dropdown can also be observed by the page Escape handler.

Evidence: [`CanvasTabDropdown.tsx`](../../src/components/CanvasTabDropdown.tsx#L128).

This is a concrete case where editable focus, local command handling, outside-close and page Escape must be modeled together.

## 7. Fact Drift Corrections Required

| Document | Existing statement | Current fact | Required documentation action |
|---|---|---|---|
| `LIBTV_UIUX_PARITY_BACKLOG.md` PAR-004 | Director only blocks page Escape | page dispatcher returns for every key while Director is active | mark Batch 50 slice recorded; retain focus trap/source parity as open |
| `LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md` UI-05 | non-Escape shortcuts may mutate background | Batch 50 blocks ordinary page dispatcher | replace with remaining nested-focus/restore/source-exact risk |
| `LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md` 6.3 | Director is independent shortcut domain | current and correct | link this audit and make recorded runtime explicit |
| Batch 50 records | full page shortcut isolation, incomplete focus trap | current and correct | treat as runtime evidence authority |

This correction is documentation maintenance, not a new implementation claim.

## 8. Static Issue Register

| ID | Finding | Severity | Evidence maturity | Design implication |
|---|---|---:|---|---|
| `LIBTV-SFC-001` | Node and edge selection use different state authorities | High | `CLONE_FACT` | define node/edge/primary session projection before graph sanitation/history work |
| `LIBTV-SFC-002` | `onNodesChange`, `onSelectionChange` and `onNodeClick` all write node selection | Medium | `CLONE_FACT` | declare canonical ingress and primary-order semantics |
| `LIBTV-SFC-003` | `selectNode` accepts an ID without active-canvas validation | Medium | `CLONE_FACT` | stale/deleted selection must reconcile deterministically |
| `LIBTV-SFC-004` | Page shortcuts execute from non-editable buttons/sections even when a surface is visually foreground | High | `CLONE_FACT` | command context must be surface-owned, not only tag-owned |
| `LIBTV-SFC-005` | Clone editable selector omits `select` and `role=textbox` covered by Open Canvas | Medium | comparative static fact | define a project-specific interactive/editable predicate and fixture corpus |
| `LIBTV-SFC-006` | Escape precedence varies across capture/bubble listeners | High | `CLONE_FACT` | every active surface needs declared consume/pass/close behavior |
| `LIBTV-SFC-007` | Preview and Director acquire focus but do not explicitly restore opener focus | Medium | `CLONE_FACT` | define close destination and deleted-opener fallback |
| `LIBTV-SFC-008` | Character/History are pointer-modal but not keyboard-modal | High | `CLONE_FACT` | decide source parity vs accessibility correction before implementation |
| `LIBTV-SFC-009` | Keyboard Shortcuts looks like a foreground panel but remains ordinary page command context | Medium | `CLONE_FACT` | define whether it is inspect-only popover or command-blocking surface |
| `LIBTV-SFC-010` | Open Canvas conflict gate freezes selection with graph mutation | Medium | `OPEN_CANVAS_FACT` | reject transplant; keep inspect selection separate from write authority unless product requires otherwise |
| `LIBTV-SFC-011` | Open Canvas delegates some destructive keyboard behavior to React Flow defaults | Medium | `OPEN_CANVAS_FACT` / `INFERENCE` | do not treat upstream absence of dispatcher as a LibTV shortcut spec |
| `LIBTV-SFC-012` | Current PAR-004/overlay docs retain pre-Batch-50 Director statements | High | documentation drift | correct immediately and add a freshness rule |

## 9. Open Canvas Claim Candidates

The following claims are ready to enter the Open Canvas evidence matrix:

| Candidate ID | Claim | Type | Boundary |
|---|---|---|---|
| `OC-046` | selected node/edge flags are framework-record state; selected-node editor, selected count, copy and delete derive different projections | `OPEN_CANVAS_FACT` | not a LibTV selection schema |
| `OC-047` | conflict gate blocks all node/edge changes, including selection transport | `OPEN_CANVAS_FACT` / `INFERENCE` | does not prove runtime harm; do not transplant blindly |
| `OC-048` | document copy/paste uses input/textarea/select/contenteditable/role-textbox guard and image-preview suspension | `OPEN_CANVAS_FACT` | not a complete command-context registry |
| `OC-049` | title/note/text editors own local focus and commit/cancel keys | `OPEN_CANVAS_FACT` | node types and exact keys remain Open Canvas product behavior |
| `OC-050` | Quick Add Escape is a document bubble listener without propagation ownership | `OPEN_CANVAS_FACT` | useful negative example only |
| `OC-051` | dialogs/dropdowns delegate focus and keyboard mechanics to fixed Radix primitives | `OPEN_CANVAS_FACT` / `INFERENCE` | exact browser focus sequence still needs runtime verification |
| `OC-052` | fixed studio has no unified app shortcut dispatcher and leaves some destructive key behavior to React Flow/default focus semantics | `OPEN_CANVAS_FACT` / `INFERENCE` | not evidence for LibTV source shortcuts |

## 10. Formal Contract Questions

The next document should answer these questions mechanically:

### 10.1 Selection identity

- separate `selectedNodeIds`, `selectedEdgeIds` and `primarySelection`;
- define ordering and primary-selection semantics;
- define active-canvas validation and reconciliation;
- keep selection out of portable document and semantic history;
- define command-specific selection snapshots.

### 10.2 Focus zones

- `CANVAS`, `EDITABLE`, `NODE_EDITOR`, `POPOVER`, `MODAL`, `ACTIVE_TOOL`, `DIRECTOR`, `BROWSER_NATIVE`;
- one active command context with explicit parent/fallback;
- initial focus, trap/containment, close return and deleted-owner fallback;
- focus zone is not inferred only from z-index or component name.

### 10.3 Keyboard dispatch

- capture local tool before route dispatcher where justified;
- editable/native command ownership before canvas command ownership;
- modal/Director suspension before graph shortcut matching;
- explicit `HANDLED`, `CONSUMED`, `PASS`, `BLOCKED`, `NOOP` result;
- event default/propagation policy per command, not incidental listener order.

### 10.4 Composition

- overlay lifecycle;
- command outcome/feedback;
- React Flow change routing;
- multi-canvas lifecycle;
- async result selection stealing;
- graph transaction/history;
- FrameOS route isolation.

## 11. Proposed Fixture And Verifier Boundary

Candidate local fixture: `LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01`.

It should eventually cover:

1. single node, multi-node, single edge and mixed node/edge selection;
2. primary selection after click, marquee, modified click, undo/redo and duplicate;
3. Delete/Backspace from canvas, input, textarea, select, role textbox, button and contenteditable;
4. Escape with dropdown, pointer-modal, Shortcuts, Preview, active image tool and Director nested surface;
5. Tab and focus containment/return for each declared context;
6. active/inactive canvas switch, selected owner delete and stale selection ID;
7. no graph/history mutation from selection/focus-only transitions;
8. edge `selected` does not leak into portable graph/history payload;
9. FrameOS route remains unaffected.

Candidate verifier: `LIBTV-VR-019`.

No fixture or verifier is authorized by this audit.

## 12. Research And Implementation Gates

Before implementation:

- correct stale Director documentation;
- obtain current LibTV source evidence for modal/Share/Agent/Shortcuts keyboard behavior where safely observable;
- define primary node/edge selection and command-context result vocabulary;
- define which differences are source parity and which are explicit accessibility improvements;
- make focus return behavior testable for deleted/unmounted owners;
- compose with `LIBTV-VR-016/017/018` instead of duplicating their graph, canvas or feedback assertions;
- receive explicit coding authorization.

Do not:

- introduce a global modal manager from this audit alone;
- copy Open Canvas Radix dependencies or visual skin;
- move selection into graph history;
- use z-index as a keyboard authority;
- treat every Escape listener as equivalent;
- merge FrameOS keyboard state into the LibTV route;
- claim current LibTV source focus parity from clone-only ARIA improvements.

## 13. Current Conclusion

The high-value Open Canvas lesson is not “use its shortcuts” or “adopt Radix.” It is the contrast between explicit local editing/focus ownership and implicit framework-owned selection/destructive behavior. The clone already improves node selection and Director isolation, but it still has a split node/edge authority and no common command-context model for foreground surfaces.

The next formal design should make this chain explicit:

```text
active canvas
  -> validated node/edge/primary selection
  -> active focus zone and surface owner
  -> local/route command dispatch precedence
  -> named command or consumed event
  -> typed outcome and feedback projection
  -> deterministic focus/selection reconciliation
```

Until that contract and source gates exist, the correct state is `STATIC_AUDIT_COMPLETE`, not “keyboard/focus parity complete.”
