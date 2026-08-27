# LibTV Editor Session And History Static Audit

> Status: `COMPLETE` / `FIXED_STATIC_AUDIT`.
>
> Scope: fixed Open Canvas editor-session methods and current ordinary LibTV clone draft/history/commit behavior.
>
> Clone baseline: `0a1c0a3`; Open Canvas baseline: `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> Authorization boundary: documentation and read-only static inspection only; no runtime, test, submodule, source-site or provider mutation.

## 1. Why This Audit Exists

The clone already has several controls named `撤销`, `重做`, `重置`, `保存`, `提交`, `使用` and `取消`. Those labels do not reveal which state they act on:

- native input editing history;
- an editor-local draft;
- an editor-local gesture history;
- the canvas graph transaction log;
- a delayed provider operation;
- durable graph persistence.

The distinction is visible to users. If local `Cmd/Ctrl+Z` moves a canvas node, if `Escape` commits through blur, if `保存` closes before an upload can fail, or if a no-op apply consumes a graph undo entry, the UI may look source-like while behaving unlike a coherent editor.

This dated audit records fixed facts before the normative contract is written. Open Canvas is used as an implementation study, not as evidence of LibTV source behavior.

Machine-readable evidence is retained in [`open-canvas-2026-08-26/editor-session-static-evidence-2026-08-27.json`](open-canvas-2026-08-26/editor-session-static-evidence-2026-08-27.json).

## 2. Authority Boundary

This audit owns evidence and gap classification only. It does not replace these existing authorities:

| Existing authority | Existing responsibility | This audit adds |
|---|---|---|
| [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md) | active key/focus/IME command owner | what local undo/cancel/commit should mean after dispatch |
| [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md) | semantic graph command and history boundaries | where a local editor ends and one graph command begins |
| [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) | delayed result identity/freshness | frozen editor submission handoff |
| [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md) | bytes, locators and lease ownership | bitmap draft/export boundary |
| [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) | canvas identity and generation isolation | open-editor invalidation conditions |
| [`LIBTV_UI_STATE_HIERARCHY.md`](liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md) | conceptual UI-state strata | concrete draft/history/commit ownership |

The future normative authority is reserved as `LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`.

## 3. Evidence Method

### 3.1 Evidence classes

| Label | Meaning |
|---|---|
| `OPEN_CANVAS_FACT` | directly present at the fixed Open Canvas SHA |
| `CLONE_FACT` | directly present in committed clone code |
| `INFERENCE` | consequence supported by those facts but not directly exercised |
| `ADOPT_METHOD` | useful Open Canvas method after adding LibTV safeguards |
| `REJECT_TRANSPLANT` | implementation detail that should not be copied as-is |
| `SOURCE_UNKNOWN` | behavior not safely established on the LibTV source site |

### 3.2 Fixed Open Canvas paths

- `shared/blocks/canvas/canvas-studio-shell.tsx`
- `shared/stores/canvas-store.ts`

No separate editor module or matching test/spec was found at the fixed SHA. The image editor and its caller both live inside the large canvas shell.

### 3.3 Fixed clone paths

- `src/components/nodes/TextNode.tsx`
- `src/components/ImageEditPanel.tsx`
- `src/components/ImageAnnotateToolbar.tsx`
- `src/components/ImageElementEditToolbar.tsx`
- `src/components/PictureEditPanel.tsx`
- `src/components/SubtitleErasePanel.tsx`
- `src/components/VideoContinuationSelector.tsx`
- `src/components/SegmentReshootPanel.tsx`
- `src/components/CameraConfigDialog.tsx`
- `src/components/CameraMovementDialog.tsx`
- `src/components/nodes/ImageNode.tsx`
- `src/components/nodes/VideoNode.tsx`
- `src/components/VideoProcessingToolbar.tsx`
- `src/store/canvasStore.ts`
- `src/store/directorStore.ts`
- `src/store/uiStore.ts`
- `src/app/page.tsx`

### 3.4 What was not exercised

- no local browser workflow was mutated;
- no LibTV source editor was opened or saved for this audit;
- no file/image was uploaded;
- no provider operation was started;
- no source project graph was changed;
- no submodule checkout or dependency was changed.

## 4. Executive Findings

### 4.1 The missing unit is an editor session, not another generic history stack

The useful common shape is:

```text
session identity + owner identity + captured baseline
  -> working draft
  -> optional local gesture history
  -> cancel OR accepted commit/submission
```

`INFERENCE`: putting every keystroke or brush point into canvas history would solve none of the lifecycle questions and would make graph undo unusable. The contract must define a foreground editor session that may or may not own a local history stack.

### 4.2 Open Canvas cleanly demonstrates local history, but not safe async acceptance

`OPEN_CANVAS_FACT`: its bitmap editor captures one full `ImageData` snapshot after each completed stroke, owns local undo/redo/restore and does not write those gestures into graph state. This is the strongest reusable method in this audit.

`OPEN_CANVAS_FACT`: the same editor closes immediately after JPEG export and starts upload through a caller that does not carry the editor `sessionId`, source version or graph revision. Upload failure is projected onto the node after the editor is gone.

`INFERENCE`: local-history separation is worth adopting; close-before-accepted-handoff and stale completion are not.

### 4.3 The clone contains three different maturity levels that must remain explicit

1. **Functional local editors**: Picture Edit and Subtitle Region have real local gesture history and one graph handoff.
2. **Honest empty modes**: Element Edit disables unavailable Undo/Generate and owns no graph state.
3. **Enabled-looking inert commands**: Annotate `保存`, Image Edit `撤销`, Video Processing `撤销/重做` and local-only generation feedback visibly overstate behavior.

Treating all three as “implemented” hides the highest-value parity work.

### 4.4 Graph history is already vulnerable to duplicate or live patches

`CLONE_FACT`: `canvasStore.updateNodeData` pushes one full graph snapshot whenever the target exists, even if the patch does not change normalized data. It has no transaction name, equality guard or coalescing key.

`INFERENCE`: wiring a slider, text keystroke or brush event directly to this gateway would produce excessive graph history. Editor-session commit semantics must be defined before activating more controls.

### 4.5 Existing documentation has already drifted

`CLONE_FACT`: [`components/TextNode.spec.md`](components/TextNode.spec.md) says text changes remain local and are not propagated to `canvasStore`, while current `TextNode.tsx` calls `updateNodeData` on changed blur commit. The same spec describes Escape as blur save although the component attempts cancel.

This is a concrete discoverability defect, not merely a future design question. The formal-contract batch must correct the component spec.

## 5. Fixed Open Canvas Evidence Ledger

| ID | Fact | Reuse disposition |
|---|---|---|
| `OC-071` | random editor `sessionId`; captures node, media and title; no source/graph revision | `ADOPT_METHOD` with freshness fields |
| `OC-072` | bounded decode, URL candidates, timeout, stale projection suppression; cleanup does not abort active fetch | adopt bounds; add real cancellation |
| `OC-073` | full bitmap snapshot after load/stroke; redo truncation; max 40 entries | adopt gesture boundary; reject entry-only budget |
| `OC-074` | Restore returns to snapshot zero and destroys redo | evidence-gated product choice |
| `OC-075` | export JPEG then close before upload handoff | retain instrumentation; `REJECT_TRANSPLANT` close order |
| `OC-076` | upload appends output by node ID with no session/source freshness | delegate to async-ingress authority |
| `OC-077` | title/text local drafts, no-op check, blur/Enter commit, Escape restore | adopt profile with baseline drift policy |
| `OC-078` | note DOM draft, sanitize on commit, Escape restore | adopt sanitization boundary only |
| `OC-079` | store rejects equal/conflicted patch; handlers ignore acceptance result | adopt guard; require acceptance-aware close |
| `OC-080` | graph dirty/revision/autosave exists without graph undo | preserve three separate authorities |

## 6. Open Canvas Bitmap Editor

### 6.1 Session envelope

Opening from the selected image constructs:

```text
CanvasImageEditorState
  sessionId: random UUID/fallback
  nodeId
  media
  title
```

The random ID resets the dialog's `isDismissedAfterSave` guard when a new session opens. It is not passed into `CanvasImageEditorSavePayload`, the upload caller or the graph patch.

`ADOPT_METHOD`: a fresh session identity is useful even for a node-local editor.

`REJECT_TRANSPLANT`: an identity that disappears before async handoff cannot protect completion. A LibTV envelope needs at least owner canvas/generation, node ID, source-media identity/version and session/operation ID where delayed work exists.

### 6.2 Source acquisition and cancellation

The fixed path:

```text
media URL/thumbnail
  -> normalize direct/proxy candidate order
  -> fetch candidate with 20s timeout
  -> verify response blob is image/*
  -> createImageBitmap or object-URL Image fallback
  -> cap to 4096px dimension and 16,000,000 pixels
  -> draw baseline
  -> capture snapshot zero
```

Positive methods:

- remote fetch has a timeout;
- the fallback object URL is revoked in `finally`;
- `ImageBitmap.close()` releases decoder resources;
- decoded dimensions are capped before local history begins;
- effect cleanup suppresses a late draw into a closed/replaced session.

Counterexamples:

- cleanup sets a local `canceled` boolean but cannot abort the controller hidden inside `fetchImageEditorBlob`;
- the first candidate can continue consuming network until timeout after close;
- source dependencies compare URL fields, not a stable source revision;
- owner deletion is handled only later by the caller's node lookup;
- source replacement during editing has no explicit rebase/reject state.

### 6.3 Local history algorithm

The editor keeps:

```text
historyRef: ImageData[]
historyIndexRef: number
render mirrors: historyIndex + historyLength
```

Each completed stroke calls `captureSnapshot()` once. Pointer moves render directly into the current canvas and are not individual undo entries. A new snapshot slices entries after the current index, so it invalidates redo. Undo/redo apply a full snapshot with `putImageData`.

This is the correct interaction granularity: one continuous stroke is one local command.

### 6.4 Memory ceiling is not safe

The editor caps decoded pixels at 16 million and history length at 40. A full RGBA `ImageData` at that pixel limit is approximately:

```text
16,000,000 pixels * 4 bytes = 64,000,000 bytes
64,000,000 * 40 snapshots = 2,560,000,000 bytes
```

That is about 2.38 GiB before JS/canvas overhead. Real usage may be lower, but entry count alone is not an adequate memory budget.

`CLONE_DECISION` for the future contract: local bitmap history needs both an entry cap and an estimated byte cap, with deterministic oldest-entry eviction that preserves the active baseline or an equivalent replay strategy.

### 6.5 Restore semantics

Restore applies baseline snapshot zero, truncates the history array to one item and sets index zero. Undo and redo are then disabled.

This is not equivalent to a reversible “reset” command. It is a destructive local-history reset. LibTV source evidence must determine whether its `重置` behaves this way; until then the future fixture should test both reversible and destructive profiles without claiming source parity.

### 6.6 Save and async upload

The editor:

1. exports JPEG at quality `0.92`;
2. constructs a sanitized filename;
3. marks itself dismissed;
4. closes the dialog;
5. invokes `onSave`;
6. displays “uploading”.

The caller:

1. reads the node by captured ID;
2. copies the current output array;
3. patches node status to running;
4. uploads asynchronously;
5. appends uploaded media and patches success;
6. or patches node error on failure.

The method has useful timing logs for export, upload and graph apply. It lacks:

- operation/session ID in the payload;
- source-media/version freshness;
- canvas identity/generation;
- accepted-running-patch check;
- cancellation;
- immutable comparison against a newer output list;
- reachable retry UI after close;
- explicit release if the node disappears after remote upload.

The formal contract must freeze an async descriptor and delegate it to `LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`; it must not duplicate the generic late-result state machine.

## 7. Open Canvas Inline Editors

### 7.1 Title

- double/click enters edit mode;
- local `draftTitle` is seeded from display title;
- blur or Enter trims and commits changed data;
- blank falls back to the current/untitled label;
- Escape restores display title and exits;
- an effect resynchronizes the draft whenever display title changes.

Strength: no changed value means no graph mutation.

Gap: the sync effect does not distinguish idle from actively dirty editing. A remote/server/local graph update can overwrite the user's draft without a drift decision.

### 7.2 Plain text

- local `draftTextBody` is seeded from node `plainText`;
- blur or `Cmd/Ctrl+Enter` commits a changed value;
- Escape restores node data and exits;
- an effect resynchronizes whenever node `plainText` changes.

This confirms that a multiline editor needs a different Enter policy from a scalar title. It does not define native text-history versus graph-history routing beyond the browser input behavior.

### 7.3 Rich note

The note editor uses `contentEditable` as its draft container. It sanitizes HTML on blur or modified Enter; Escape restores the original node HTML before exiting. Bold/italic/underline use `document.execCommand`.

The useful boundary is sanitization at commit. The implementation has no custom draft snapshot, no baseline revision and no local-history ledger. It should not be generalized as the standard editor-session model.

### 7.4 Commit acceptance gap

Open Canvas `updateNodeData` returns a mutation result. It rejects:

- graph revision conflict;
- normalized no-op patch;
- absent/invalid target through unchanged mapping.

The inline handlers do not branch on that result and exit editing anyway. The image-save path also ignores the running-patch result and can continue upload while the store is in conflict.

`CLONE_DECISION`: a close-after-commit editor needs an explicit result:

```text
accepted -> close and restore focus
no-op -> close without graph history
rejected_stale/conflict -> remain open or present recoverable resolution
owner_missing -> dispose without applying
```

## 8. Persistence Is A Separate Authority

Open Canvas records `revision`, `savedGraphString`, `isDirty`, `saveStatus`, `saveError` and `conflictDetected`. Its save path serializes the current graph, validates it, writes with a revision precondition, can attempt a three-way merge and marks whether newer local changes remain dirty after a response.

The fixed shared code has no canvas graph undo/redo stack. Search found custom Undo/Redo only in the bitmap editor.

This is a valuable negative result:

- local bitmap undo is not graph undo;
- graph dirty is not editor dirty;
- revision conflict is not editor baseline drift;
- successful editor Save is not durable graph persistence.

The LibTV clone does have graph undo/redo, so adopting Open Canvas's editor pattern requires an explicit handoff that Open Canvas itself does not demonstrate.

## 9. Current Clone Surface Inventory

| ID | Surface | Draft owner | Local history | Commit/handoff | Completeness |
|---|---|---|---|---|---|
| `LIBTV-EDS-001` | `TextNode` | component nullable string | native textarea only | changed blur -> `updateNodeData` | functional, edge-risk/spec drift |
| `LIBTV-EDS-002` | Image generation panel | component Prompt/references | none; Undo inert | local submitted flag only | presentational mock |
| `LIBTV-EDS-003` | Image Annotate | UI owner + node-local tool settings | none; Undo/Redo disabled | enabled-looking Save inert | high-value incomplete |
| `LIBTV-EDS-004` | Image Element Edit | UI owner + local tool/brush | none; Undo disabled | Generate disabled | honest empty shell |
| `LIBTV-EDS-005` | Picture Edit | component marks/details | 30 mark snapshots | delayed one graph transaction | functional local history, partial fields |
| `LIBTV-EDS-006` | Subtitle Region | component regions | 30 region snapshots | immediate one graph transaction | functional local history |
| `LIBTV-EDS-007` | Continuation range | component range/drag | none | immediate one graph transaction | sound scalar draft |
| `LIBTV-EDS-008` | Segment Reshoot | component selections/intent | none | local submitted flag | non-dismissable mock |
| `LIBTV-EDS-009` | Matting/Depth/Picture submit | node component timer state | profile-dependent | delayed graph placeholder | deterministic simulation only |
| `LIBTV-EDS-010` | Camera dialogs | dormant component local config | none | optional callback; no caller found | dead prototype |
| `LIBTV-EDS-011` | Video top toolbar | none | Undo/Redo inert | none | misleading chrome |
| `LIBTV-EDS-012` | canvas graph gateway | full graph snapshot | 50 per canvas | every existing-node patch | no equality/coalescing |
| `LIBTV-EDS-013` | active image modes | `uiStore` owner envelope | blocks graph shortcuts | close/dispose only | strong owner invalidation |
| `LIBTV-EDS-014` | Director motion path | separate typed store draft | no route-shared graph history | finish/cancel | useful comparison only |

## 10. Clone Detail Findings

### 10.1 TextNode

Current code is stronger than its spec:

- entering edit sets `draft=data.content`;
- blur calls `updateNodeData` only if changed;
- Escape attempts to set `draft=null` without graph mutation.

Open risks:

- no session/baseline version exists;
- external data changes while editing have no explicit policy;
- Escape and unmount-triggered blur ordering is not guarded by a cancel ref/reason;
- graph undo clears selection and may unmount an editor;
- the current spec gives agents the wrong implementation guidance.

### 10.2 Image generation panel

`ImageEditPanel` seeds Prompt/references from node data but never writes them back. AutoLink modifies only local arrays/strings. Submit sets a local boolean and reports a local task. Reselecting/unmounting can recreate the component from unchanged node data and lose the draft.

The visible `撤销` button has no handler and is not disabled. This is not local history, graph history or native input history.

The correct future profile is not yet proven. It could be:

- a persistent node-form with live/coalesced graph fields;
- a local generation request draft committed on submit;
- a hybrid where Prompt is node data and transient AutoLink ghosts remain local.

Existing AutoLink research supports the hybrid distinction, but source commit timing still needs evidence.

### 10.3 Image Annotate

Positive foundation:

- `uiStore` carries canvas/node/media owner identity;
- selection/canvas/node reconciliation closes invalid owners;
- the page captures image-mode shortcuts before graph commands;
- active mode replaces the standard node toolbar/panel.

Missing semantics:

- no annotation record model;
- no pointer gesture draft;
- no local history;
- no dirty state;
- no Save callback;
- no graph/async/media handoff;
- Save looks enabled despite doing nothing.

This is the highest-salience incomplete editor in the current clone. It should not be activated by simply wiring Save to `updateNodeData`; the annotation representation and source/result ownership must be defined first.

### 10.4 Image Element Edit

This surface is intentionally safer:

- it declares itself an empty source-backed mode;
- Undo and Generate are disabled;
- selection/owner/canvas invalidation closes it;
- close produces no graph history.

It should remain an honest empty state until evidence establishes selections, records, generation payload and result ownership.

### 10.5 Picture Edit

Positive methods:

- normalized coordinates make draft data independent of zoom;
- pointermove updates the working draft without adding history;
- pointerup/cancel commits one before/after snapshot;
- no-op snapshots are rejected;
- new edits clear redo;
- local history is capped at 30;
- submit deep-clones the marks;
- graph creation is delegated to one store command.

Gap: `description` and `replacement` changes use `replaceMarks`, which updates `present` without pushing a past entry or clearing redo. Therefore “all meaningful editor changes are undoable” is false. A user can alter semantic details and then Undo can jump to a previous geometry snapshot instead of undoing the last detail edit.

Submitting is simulated by a 520ms timer. Close and history buttons are disabled while submitting; Escape still reaches `onCancel`, but the parent refuses cancel when `pictureEditSubmitting` is true. The timer is cleared only when the owning `VideoNode` unmounts.

### 10.6 Subtitle Erase

Region mode mirrors the useful mark-history pattern and correctly treats one draw/move/resize gesture as one local command. Reset is a reversible history entry rather than destructive history collapse.

Confirm deep-clones regions and the parent immediately closes the editor before calling `createSubtitleErase`. There is no panel-level submitting or duplicate-acceptance token. The current synchronous store call is deterministic, but this profile cannot be reused unchanged for a real asynchronous request.

Smart subtitle mode has no region draft and can submit immediately. It is a separate profile, not a zero-region version of the region editor.

### 10.7 Continuation, Depth Motion and Smart Matting

- Continuation owns local range state and confirms one semantic graph command. No custom history is necessary for two scalar handles.
- Depth Motion keeps selected resolution in `VideoNode`, resets to `720P` on open, locks controls during a timer and then creates one graph placeholder.
- Smart Matting has no editable draft; its only foreground state is submitting.

These show why one editor-session contract needs profiles. Not every editor needs local undo, but every explicit Apply/Submit still needs owner identity, no-op/idempotency and accepted handoff semantics.

### 10.8 Segment Reshoot

The panel keeps selection, intent, expansion and submitted feedback locally. Submit does not create graph data or an async descriptor. The component receives only `zoom`, so it has no explicit cancel callback and no owner/session envelope.

This should be classified as a local interaction prototype, not a partially connected provider workflow.

### 10.9 Camera dialogs

No caller was found for either dialog. Both accept optional `onApply`, use local config and close on backdrop/header cancel. Their local state is created even while `isOpen=false`, so canceled values remain in memory and reappear on reopen if a caller mounts them persistently.

These are useful examples of why “Cancel closes UI” is insufficient. Cancel should restore/recreate baseline, not merely hide the same dirty draft. Because the dialogs are dormant, the future contract should not assign them current parity priority.

### 10.10 Global command ownership

The page already protects active image modes from graph shortcuts:

- Escape closes the top image layer;
- Delete/Backspace/Tab/Space and modifier undo/redo are stopped;
- selection change closes annotate/element edit;
- node/canvas invalidation closes owner-bound modes.

This is a strong adjacent method. The missing part is what a local undo or dirty close should do once those commands are correctly routed.

### 10.11 Graph history gateway

`updateNodeData`:

1. finds the active canvas and target node;
2. merges the patch into node data;
3. pushes the entire pre-change graph into per-canvas history;
4. clears redo.

It does not compare old/new values. Graph undo/redo restore graph snapshots and clear selection.

Consequences:

- a no-op patch can consume one of 50 history entries;
- high-frequency live controls are unsafe without coalescing;
- a foreground editor can disappear after graph undo clears selection;
- local editor state is not restored by graph redo unless it was graph data;
- a commit gateway needs semantic equality before history push.

## 11. Cross-Profile State Matrix

| Event | Inline text | Mark/region | Bitmap | Scalar selector | Async submitting |
|---|---|---|---|---|---|
| open | capture field baseline | empty/captured marks | capture source media/version | derive initial range/config | capture owner/input baseline |
| edit | native input draft | normalized records | raster/vector records | local scalar state | local request fields |
| local history | native browser | gesture snapshots | gesture/snapshot log | usually unnecessary | draft-only before submit |
| reset | restore baseline or local command | reversible local command | source-evidence decision | restore defaults/baseline | clear unsubmitted fields |
| cancel | zero graph mutation | zero graph mutation | dispose resources; zero graph mutation | zero graph mutation | before acceptance only |
| commit | one no-op-aware field command | freeze deep clone, one graph/async handoff | export/freeze, then async handoff | one semantic command | immutable operation descriptor |
| owner drift | reject/rebase/prompt | invalidate or explicit rebase | invalidate and release | invalidate | delegate freshness check |
| graph undo | after commit only | after accepted commit only | after accepted result projection | after commit only | must not mean cancel remote work |

## 12. Ranked Gaps

### P0: semantics needed before activating more UI

1. No shared foreground session envelope or baseline-drift policy.
2. `updateNodeData` has no equality/coalescing contract.
3. Async editor submission has no explicit frozen descriptor at the UI boundary.
4. Enabled-looking inert Save/Undo/Redo commands overstate parity.

### P1: high-value existing-surface corrections

1. Define Image Annotate representation/history/save boundary before enabling behavior.
2. Add every semantic Picture Edit field change to local history or explicitly exclude it.
3. Give Image Edit Prompt/reference state an explicit persistence/submission profile.
4. Correct `TextNode.spec.md` to current fact and future edge rules.
5. Define close/cancel behavior during timers and real async operations.

### P2: consistency and dormant surfaces

1. Classify/remove or reconnect dead Camera dialogs when implementation is authorized.
2. Give Segment Reshoot a cancel/handoff contract.
3. Decide whether video toolbar Undo/Redo are graph commands, local processing history or unavailable chrome.
4. Keep Director motion-path lessons as a comparison without merging stores.

## 13. Open Canvas Adoption Decisions To Carry Forward

### Adopt

- unique foreground session identity;
- local draft separate from graph data;
- one snapshot per completed pointer gesture;
- redo truncation after a new local command;
- normalized no-op guard before graph mutation;
- decoded media dimension/pixel limits;
- source-load stale projection suppression;
- commit-time rich text sanitization;
- save/export timing instrumentation.

### Adopt only with safeguards

- bounded bitmap snapshots: add byte budget and deterministic release;
- external draft resynchronization: add baseline-drift policy;
- source candidate fetch: expose an abort owner;
- close after save: require accepted async handoff and reachable failure/retry;
- graph conflict guard: make editor close depend on commit result.

### Reject as transplant

- full-image history bounded only by 40 entries;
- session ID that is dropped before async completion;
- source/result patching by node ID alone;
- closing before upload acceptance and failure ownership;
- silently replacing an active draft when upstream data changes;
- treating autosave revision as editor-local history;
- using the monolithic canvas shell as the long-term editor ownership boundary.

## 14. Source-Site Evidence Queue

The following remain `SOURCE_UNKNOWN` and should be measured only with a disposable/safe fixture:

| Question | Safe observation |
|---|---|
| dirty close | create reversible local draft, test close/Escape/selection change, discard fixture afterward |
| local vs graph undo | focus editor, make one local gesture, invoke toolbar/shortcut, inspect graph unchanged |
| redo invalidation | undo one gesture, make another, inspect redo enabled state |
| reset semantics | reset then undo/redo; reset then cancel/save |
| commit cardinality | compare graph/output before and after one accepted edit |
| source replacement drift | open editor, change owner source through a safe fixture, observe reject/reload/prompt |
| submit failure/retry | use an intentionally invalid disposable input without provider cost where possible |
| node delete/canvas switch | only on a disposable node/project and only with explicit mutation authorization |
| text commit trigger | observe blur, Enter, modified Enter and Escape on disposable text |
| annotate representation | inspect DOM/canvas records after a reversible mark without saving |

This batch does not execute the queue. Open Canvas facts must not fill those LibTV source gaps.

## 15. Contract Inputs Proven By This Audit

The future stable contract now has enough evidence to define:

- one typed editor-session envelope;
- explicit state machine from clean draft through dirty, submitting, rejected and disposed;
- profile-specific commit triggers;
- local history entry/coalescing/budget rules;
- native/local/graph undo precedence;
- no-op and commit-acceptance results;
- baseline/owner/source invalidation;
- synchronous graph versus asynchronous operation handoff;
- bitmap resource release;
- deterministic fixture and verifier cases;
- honest placeholder/inert-control classification.

The contract must not claim exact LibTV source close, reset, text-commit or stale-source behavior until the source evidence queue is executed safely.

## 16. Immediate Documentation Actions

1. Write `LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md` from the proven boundary.
2. Define `LIBTV-FIX-LOCAL-EDITOR-SESSION-01` and `LIBTV-VR-022` without runtime changes.
3. Correct the stale `TextNode` component specification.
4. Add editor-session cases to the graph invariant/case catalogs and verification ledger.
5. Publish `OC-PATTERN-12`, `OC-ADOPT-025`, `OC-TR-018` and `OC-BP-012`.
6. Add a ranked implementation handoff that keeps source-unknown semantics evidence-gated.
7. Preserve this audit as dated evidence after the active plan is promoted.

## 17. Completion Boundary

The static audit is complete because:

- the fixed Open Canvas editor, store and save paths were traced end to end;
- all current high-salience clone editor surfaces were classified;
- local draft, local history, graph history, async operation and persistence were separated;
- positive methods and counterexamples were recorded with stable IDs;
- visible parity gaps were ranked separately from semantic/concurrency/performance risks;
- source unknowns were retained rather than inferred from Open Canvas;
- no runtime, test, submodule or source-site state was changed.

The next step is normative documentation, not more unstructured static searching.
