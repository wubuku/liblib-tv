# LibTV Editor Session, Commit And History Research Plan

> Status: `ACTIVE` / `DOCUMENTATION_ONLY`.
>
> Scope: study how fixed Open Canvas and the current LibTV clone separate editor-local drafts, local undo/redo, semantic graph commits and asynchronous submission, then turn the useful methods and counterexamples into implementation-ready LibTV guidance.
>
> Baselines: clone `d9b3433`; Open Canvas `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> Authorization boundary: no changes to `src/`, tests, runtime fixtures, either submodule, FrameOS, Director behavior or either source website.

## 1. Problem

The repository already documents keyboard ownership, graph transactions, async completion and several individual editing surfaces. It does not yet have one authority for the interval in which a user has opened an editor but has not accepted its work:

```text
capture baseline
  -> create foreground editor session
  -> mutate working draft
  -> record editor-local gesture history
  -> cancel without graph mutation
     or freeze one commit/submission descriptor
  -> append at most one semantic graph history entry
     or delegate one asynchronous operation
```

Without that authority, similar-looking controls can have incompatible behavior. A brush stroke may pollute graph undo; `Escape` may close a panel after blur has already committed; a no-op apply may consume history; a late image export may overwrite a newer node revision; and an editor may disappear before an upload failure can be retried. The clone currently contains both useful local-history implementations and visible but inert undo controls, so the gap is already implementation-relevant.

Open Canvas is useful because its fixed implementation contains concrete inline text drafts, a bitmap editor with bounded snapshots, asynchronous edited-image upload and graph autosave/conflict handling. It is a method and counterexample source, not evidence of LibTV source behavior.

## 2. Authority Boundary

### 2.1 This study owns

- foreground editor session identity and captured baseline;
- working draft ownership and dirty comparison;
- editor-local gesture/snapshot history;
- local undo/redo/reset semantics and memory budget;
- commit, apply, submit, cancel and close intent normalization;
- no-op rejection and semantic command cardinality;
- focus/IME/pointer interaction gates while an editor is active;
- baseline drift, node deletion, canvas switch and unmount invalidation;
- the handoff envelope to graph mutation or asynchronous result ingress;
- honest classification of functional, partial and inert clone controls.

### 2.2 Adjacent authorities remain authoritative

| Authority | Owns | This study delegates |
|---|---|---|
| [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../research/LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md) | active command context, IME and shortcut routing | which owner receives `Escape`, `Enter`, `Cmd/Ctrl+Z` |
| [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../research/LIBTV_GRAPH_TRANSACTION_CATALOG.md) | semantic graph command/history boundaries | accepted node/edge mutation and graph undo entry |
| [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../research/LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) | operation freshness and delayed-result convergence | accepted async submission and late completion |
| [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](../research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md) | byte/resource leases and locator materialization | bitmap/file export ownership and release |
| [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](../research/LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md) | destructive graph command planning | owner deletion and reference repair |
| [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) | canvas identity/generation and switch isolation | canvas switch/delete invalidation |
| [`LIBTV_UI_STATE_HIERARCHY.md`](../research/liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md) | conceptual UI-state strata | presentation-level open/closed/processing vocabulary |

This authority starts only after an entry surface has chosen an owner and supplied an editable baseline. It ends when cancel disposes the draft, a synchronous commit is accepted/rejected, or an immutable async submission descriptor is handed off.

## 3. Working Model To Test

Every editing surface should be classifiable into these layers:

| Layer | Typical contents | History owner |
|---|---|---|
| persisted/source baseline | node data or media revision captured on open | none in this contract |
| working draft | text, config, marks, regions, bitmap or motion-path anchors | editor session |
| editor-local history | gesture-level before/after snapshots | editor session |
| accepted semantic mutation | one normalized node/graph patch | graph transaction authority |
| submitted operation | frozen payload plus owner/version identity | async ingress authority |
| durable save | graph revision and provider persistence | persistence authority, out of scope |

The central hypothesis is that `draft mutation != graph mutation`, `local undo != graph undo`, and `editor Save != durable graph save`. The audit must record where Open Canvas and the clone uphold or violate those distinctions.

## 4. Research Questions

1. Which Open Canvas editors own a local draft, and which write directly to the graph on every interaction?
2. What is captured at editor open: node ID, source media, title, graph revision, field revision or session ID?
3. Which gestures create local history entries, and how are pointer moves coalesced into one undo step?
4. Are local histories bounded by entry count, bytes, dimensions or neither?
5. What invalidates redo: new draft mutation, source reload, reset, commit or editor reopen?
6. What are the exact blur, Enter, modified Enter and Escape semantics for title, text and rich note editors?
7. Can blur and Escape race, and can a closed editor still commit stale draft data?
8. Does cancel always mean zero graph mutation and zero async operation?
9. Does apply/save produce one graph transaction, multiple status patches or an async operation sequence?
10. What happens if the owner node is deleted, changed, undone or moved to another canvas while an editor is open?
11. What happens if an edited-image upload fails after the dialog has closed?
12. How do Open Canvas graph revision conflicts relate to, but remain distinct from, editor-local baseline drift?
13. Which current LibTV controls are fully functional, partially functional, local mock behavior or inert chrome?
14. Which clone surfaces need explicit commit semantics versus live/coalesced inspector semantics?
15. Which LibTV source-site details remain unknown and require later read-only or disposable-fixture evidence?

## 5. Evidence Queue

### 5.1 Fixed Open Canvas

Read and record exact paths for:

- `CanvasImageEditorState`, session ID creation and editor-open source capture;
- image loading cancellation and source replacement behavior;
- `ImageData` capture, 40-entry truncation, undo/redo/restore and memory implications;
- export timing, close-before-upload, upload success/failure and node patching;
- missing owner/source revision checks and any stale-session guards;
- title, text and rich-note local drafts, commit triggers and Escape handling;
- `updateNodeData` equality guard, conflict rejection and dirty-state projection;
- graph autosave revision handling and why it is not editor-local history;
- close/backdrop/route change behavior for dirty editor drafts;
- absence or presence of graph-level undo/redo.

Candidate evidence IDs: `OC-071..080`.

### 5.2 Current LibTV Clone

Read and record exact paths for:

- `TextNode` draft/blur/Escape behavior;
- `PictureEditPanel` marks, 30-entry history, pointer coalescing, cancel and submit lock;
- `SubtitleErasePanel` region history, Escape, reset and submission behavior;
- image annotate, element edit, image edit and video-processing undo/redo controls;
- camera dialogs and other local apply/cancel configurations;
- continuation, matting and depth-motion selectors;
- graph `updateNodeData`, per-canvas history and no-op behavior;
- Director motion-path draft/finish/cancel as a separate-route comparison only;
- Inspector controls that mutate immediately and therefore require explicit live-edit classification;
- open editor behavior under node deletion, graph undo, canvas switch and selection change.

Candidate issue prefix: `LIBTV-EDS-*` (`Editor Draft Session`).

### 5.3 LibTV Source-Site Unknowns

Prepare, but do not execute without a safe fixture, a later evidence script for:

- dirty close via close button, backdrop, Escape, selection change and canvas switch;
- local undo versus global undo while each editor has focus;
- redo invalidation after a new gesture;
- reset followed by cancel versus reset followed by save;
- source media replacement while an image editor is open;
- save/submission loading lock, cancellation, failure, retry and focus return;
- node deletion or graph undo while an editor/submit operation is active;
- exact graph-history cardinality after one accepted edit;
- whether title/text blur commits are source behavior or clone-only decisions.

No source mutation, private upload, provider execution or paid action is authorized in this batch.

## 6. Editing Profiles To Compare

| Profile | Candidate surfaces | Expected distinction to verify |
|---|---|---|
| inline scalar draft | title, `TextNode` body | blur/Enter commit; Escape cancel; no local undo owner beyond native text editing |
| rich text draft | Open Canvas note | DOM draft/sanitization; modified Enter; Escape restoration |
| modal configuration | camera config/movement | local form state; explicit apply/cancel; one no-op-aware patch |
| mark/region editor | picture edit, subtitle erase | gesture snapshots; local undo/redo; submit freezes a deep clone |
| bitmap editor | annotate/image edit | source lease; byte-budgeted local history; export then async materialization |
| staged selector | continuation/matting/depth motion | selection draft and validation before submit |
| motion-path draft | Director comparison | anchor draft, validity gate, finish/cancel; no LibTV route inference |
| live inspector | sliders/toggles | immediate mutation must be named and coalesced or explicitly excluded |
| async submitting editor | picture/image processing | lock, immutable descriptor, retryable failure and freshness handoff |

## 7. Planned Deliverables

| Deliverable | Lifecycle | Purpose |
|---|---|---|
| `docs/research/LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md` | dated reference | fixed Open Canvas/clone facts, positive methods, counterexamples and ranked gaps |
| `docs/research/LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md` | stable guide/reference | session envelope, state machine, local history, commit/cancel and authority handoff |
| `LIBTV-FIX-LOCAL-EDITOR-SESSION-01` | fixture design | deterministic text/config/region/bitmap sessions and graph-history oracle |
| `LIBTV-VR-022` | verifier design | pure state-machine checks plus focused browser traces |
| `OC-PATTERN-12` / `OC-ADOPT-025` / `OC-BP-012` | Open Canvas translation | reusable method, adoption boundary and implementation slices |
| `OC-TR-018` / `LIBTV-TR-044` / `DEC-038` / `LIBTV-UIX-22` | governance | traceability, decision and UI/UX mapping |
| `LIBTV-PAR-015` | parity backlog | one implementation-ready editor-session parity slice |

IDs are reserved by this active plan but become authoritative only when their target documents are written and indexed. Proposed graph IDs begin at `LIBTV-GI-085` and `LIBTV-GC-109`; final ranges depend on the audited state machine.

## 8. Work Sequence

1. Complete the authority-overlap audit and record the ownership boundary.
2. Extract fixed Open Canvas editor/session call sites into a dated evidence table.
3. Extract current clone editor/session behavior and classify visible controls honestly.
4. Build one cross-profile matrix for baseline, draft, history, commit, cancel and invalidation.
5. Rank visible parity gaps separately from correctness, concurrency and memory risks.
6. Write the formal contract only after the dated audit proves the missing authority.
7. Define deterministic fixture/verifier designs without modifying runtime or tests.
8. Sync Hub -> Guide -> Reference navigation and Open Canvas adoption/handoff/governance chains.
9. Run documentation verification and diff checks; commit and push each key documentation milestone.
10. Promote this plan into dated Open Canvas research history when the batch closes.
11. Start the next highest-value documentation loop only after checking unresolved evidence and implementation handoff gaps.

## 9. Decisions The Contract Must Resolve

- immutable editor session ID and owner envelope;
- baseline snapshot and optional owner/field/media revision;
- dirty equality and no-op apply semantics;
- local-history entry shape, gesture coalescing and byte/entry budget;
- native text undo versus custom editor undo versus graph undo precedence;
- redo invalidation and reset semantics;
- commit trigger matrix for blur, Enter, modified Enter, Apply and Save;
- Escape/close/backdrop behavior and one-layer dismissal;
- IME composition and pointer-capture completion;
- source/owner drift policy: reject, rebase, prompt or reopen;
- node delete, graph undo, canvas switch and unmount disposal;
- synchronous graph command cardinality;
- async submission descriptor freezing and input locking;
- failure/retry UI ownership after editor closure;
- exact-once resource transfer/release for bitmap drafts;
- prototype-safe behavior when no backend, bitmap engine or provider exists;
- explicit distinction among source fact, inference, Open Canvas method and clone decision.

## 10. Risk Ranking Method

The dated audit will score each gap across four independent axes rather than collapsing everything into visual parity:

| Axis | High-risk example |
|---|---|
| visible fidelity | source exposes enabled undo/save but clone control is misplaced or inert |
| semantic correctness | cancel or no-op produces graph history |
| concurrency/lifecycle | late export overwrites a newer node/canvas generation |
| resource/performance | full-resolution bitmap snapshots exceed a safe memory budget |

Recommended implementation order will prioritize a small shared semantic contract and high-value visible surfaces, while leaving source-unknown behavior behind evidence gates.

## 11. Stop Conditions

Stop an evidence path when it would require:

- changing clone code, runtime tests or fixtures;
- changing/installing dependencies or modifying a submodule;
- mutating a source-site project or uploading private media;
- invoking paid/provider execution;
- claiming LibTV behavior from Open Canvas implementation;
- inventing collaboration, persistence or backend version semantics;
- treating Open Canvas autosave revision as proof of an editor baseline contract.

Record the unknown, continue with the next safe evidence path and preserve the fact/inference/decision distinction.

## 12. Acceptance Criteria

This research batch is complete when:

- every current LibTV editing surface in scope has an explicit profile and completeness classification;
- baseline, draft, local history, graph transaction, async operation and durable save are distinct authorities;
- cancel is deterministic and proven to produce no semantic graph mutation in the proposed contract;
- no-op, local undo/redo/reset and accepted commit cardinality are explicit;
- blur/Enter/Escape/IME and pointer-gesture behavior are deterministic;
- stale owner/source/session completion cannot silently overwrite newer work in the proposed contract;
- local history has an explicit entry/byte budget and release policy;
- failure and retry remain reachable after asynchronous submission;
- fixture `LIBTV-FIX-LOCAL-EDITOR-SESSION-01` and verifier `LIBTV-VR-022` have deterministic cases;
- Open Canvas methods and counterexamples have explicit adoption decisions;
- agent navigation, traceability and implementation handoff remain discoverable;
- documentation checks pass and no runtime/submodule/WIP path is modified.

## 13. Immediate Next Action

Write the dated static audit from the fixed Open Canvas and current clone baselines. Do not begin the normative contract until the audit has tested all editing profiles above and identified the exact authority overlap with existing graph, async, media and command-context documents.
