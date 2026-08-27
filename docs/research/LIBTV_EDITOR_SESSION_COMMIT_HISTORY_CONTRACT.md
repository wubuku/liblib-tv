# LibTV Editor Session, Commit And History Contract

> Status: `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING_OR_PARTIAL` / `SOURCE_PARITY_PARTIAL`.
>
> Scope: foreground editor baseline, working draft, local history, commit/cancel, graph/async handoff and lifecycle invalidation for the ordinary LibTV route.
>
> Evidence baseline: clone `b5ea255`; Open Canvas `cf3a906bb8c35bb940d3267497e7f394b8f42582`; dated audit [`LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md`](LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md).
>
> Authorization boundary: this is documentation and verifier design. It does not authorize runtime, test, submodule, source-site, upload, provider or persistence changes.

## 1. Contract Objective

This contract defines the state owned by a foreground editor between opening and accepting or discarding its work.

It establishes six separate authorities:

```text
owner/source baseline
  != working draft
  != editor-local history
  != semantic graph transaction
  != asynchronous operation/result
  != durable graph persistence
```

The contract must let future agents answer, before wiring any visible `撤销`, `重做`, `重置`, `保存`, `提交`, `使用` or `取消` command:

1. which editor profile is active;
2. what baseline it captured;
3. where its unaccepted draft lives;
4. whether it owns custom local history or native input history;
5. which event freezes one commit/submission;
6. what happens when the owner/source changes;
7. how many graph-history entries acceptance creates;
8. who owns failure/retry and resource cleanup;
9. what remains source-unknown.

This is a design authority for future implementation. Current runtime remains a set of partial islands documented in the dated audit.

## 2. Evidence And Product Boundary

### 2.1 `OPEN_CANVAS_FACT`

The fixed Open Canvas baseline proves:

- a random image-editor session ID and captured node/media/title;
- bounded decode dimensions/pixels and stale result suppression;
- one full bitmap snapshot per completed stroke;
- local undo/redo/restore separate from graph dirty/save state;
- component-local title/text drafts and commit-time rich-text sanitization;
- normalized no-op/conflict rejection in `updateNodeData`;
- graph dirty/revision/autosave without graph undo;
- close-before-upload and node-only async completion counterexamples;
- an entry-count-only bitmap history whose theoretical upper bound is unsafe.

These facts are indexed as `OC-071..080`. They are implementation-study evidence, not LibTV source claims.

### 2.2 `CLONE_FACT`

The current ordinary LibTV route proves:

- a functional `TextNode` local draft/blur commit island;
- functional normalized mark/region local-history islands;
- owner/canvas/node invalidation for active image modes;
- active-image shortcut capture before graph commands;
- one-step graph commands for several selectors/process placeholders;
- a generic `updateNodeData` that always pushes history without equality checks;
- enabled-looking inert commands in Annotate, Image Edit and Video Processing;
- an honest disabled empty state in Element Edit;
- dormant Camera dialogs and local-only Segment Reshoot/Image Edit simulations;
- typed Director motion-path draft behavior in a separate store/route.

These facts are indexed as `LIBTV-EDS-001..014`.

### 2.3 `SOURCE_UNKNOWN`

Current evidence does not establish exact LibTV source behavior for:

- dirty close/selection change/canvas switch;
- local versus global undo routing inside each editor;
- reset and redo semantics;
- title/text commit triggers;
- annotation record shape and saved result ownership;
- baseline/source drift while editing;
- save/submission failure, retry and cancellation;
- graph-history cardinality after an accepted source edit.

This contract chooses deterministic clone correctness defaults where required, but marks source-specific decisions in the queue rather than presenting them as parity.

### 2.4 `CLONE_DECISION`

The clone design requires:

- no unaccepted draft mutation in semantic graph history;
- no enabled-looking inert primary command;
- cancel before acceptance has zero semantic graph mutation;
- no-op acceptance has zero graph-history entries;
- one synchronous accepted edit has at most one semantic graph-history entry;
- delayed work carries immutable owner/session/source identity;
- active dirty drafts are not silently overwritten by external graph updates;
- local bitmap history has both entry and byte budgets;
- component timers are fixtures/simulations, not operation identities;
- route stores remain isolated.

## 3. Authority Composition

| Authority | This contract delegates | This contract owns before delegation |
|---|---|---|
| [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md) | event target/phase, active command context, IME and shortcut dispatch | local command semantics after the editor receives the event |
| [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md) | validated semantic graph mutation and graph history | normalized no-op-aware commit intent |
| [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) | operation/result freshness, terminal convergence and late completion | immutable accepted submission descriptor |
| [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md) | byte/locator lease transfer and release | editor-owned bitmap/file draft before handoff |
| [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md) | typed outcome projection, retry/clear and announcement owner | editor outcome/disposition and reason |
| [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) | canvas identity, generation and switch/delete plan | session's captured owner/canvas generation |
| [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md) | destructive command/ref/resource impact | foreground owner invalidation response |
| [`components/LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md) | field roles, source/media/reference identity | field scope and baseline fingerprint |

This contract does not create a second graph reducer, operation registry, resource registry, focus dispatcher or persistence layer.

## 4. Vocabulary

| Term | Meaning |
|---|---|
| editor session | one foreground editing lifetime for one declared owner/field scope |
| owner | node/field/media/config target whose accepted state may change |
| baseline | immutable field/source snapshot and freshness identity captured on open/rebase |
| working draft | unaccepted editor state visible to the user |
| draft dirty | semantic draft differs from the captured baseline after normalization |
| native history | browser input/contenteditable undo behavior |
| local history | editor-owned record/gesture history that never directly changes graph history |
| graph history | semantic canvas transactions restored by global undo/redo |
| history entry | one reversible before/after local draft command |
| gesture | pointerdown through pointerup/pointercancel for one continuous interaction |
| commit intent | normalized synchronous patch/command candidate frozen from draft |
| submission descriptor | immutable async request candidate accepted by an operation owner |
| accepted | target authority has taken ownership of the command/operation |
| no-op | normalized draft produces no semantic target change |
| baseline drift | current target/source identity differs from captured baseline while session is open |
| invalidated | session owner/canvas/source can no longer accept its draft |
| disposed | local draft/history/resources/focus ownership have been released |
| durable save | external/project persistence; not editor-local Save |

## 5. Named Editor Profiles

Every foreground editor must register exactly one profile. “It has a panel” is not a profile.

| Profile | Candidate surfaces | Draft | Local history | Acceptance |
|---|---|---|---|---|
| `INLINE_SCALAR` | node title/name | one scalar field | native input | Enter/blur profile policy |
| `INLINE_MULTILINE` | TextNode body, Prompt text | multiline field | native input | modified Enter/blur/explicit submit policy |
| `RICH_TEXT` | note/caption HTML | sanitized DOM/model | native or declared custom history | modified Enter/blur/Apply |
| `MODAL_CONFIG` | camera/movement/settings dialog | structured config | optional atomic field history | explicit Apply only |
| `RECORD_EDITOR` | picture marks, subtitle regions | normalized records | custom gesture/field history | Submit/Generate |
| `BITMAP_EDITOR` | annotate/raster edit | bitmap/vector records plus source lease | custom bounded history | Save/export then graph/async handoff |
| `RANGE_SELECTOR` | continuation/time region | scalar range | usually none | Confirm |
| `REQUEST_DRAFT` | image/video generation, reshoot | prompt/references/settings | native plus optional structured history | Submit async descriptor |
| `LIVE_COALESCED_INSPECTOR` | continuous slider/toggle inspector | current live field group | coalesced graph command, not local session history by default | gesture end/blur coalescing |
| `EMPTY_EVIDENCE_GATED` | current Element Edit shell | local visual tool only | unavailable | no semantic acceptance |

### 5.1 Profile registry requirements

Each profile instance declares:

- `profileId` and profile version;
- owner type and field scope;
- baseline normalization/equality function;
- valid draft shape;
- dirty computation;
- commit trigger set;
- Escape/close/backdrop policy;
- native/custom/no local-history owner;
- local-history coalescing and budget policy;
- validation registry and stable reasons;
- synchronous graph or async operation handoff;
- focus return owner;
- owner/source/canvas invalidation policy;
- resource ownership/release policy;
- source-evidence status.

### 5.2 Invalid profile combinations

- `EMPTY_EVIDENCE_GATED` cannot expose an enabled Save/Submit/Undo/Redo command.
- `LIVE_COALESCED_INSPECTOR` cannot push one graph entry per pointermove/input event.
- `BITMAP_EDITOR` cannot store `ImageData`, `Blob`, `File` or object URL in semantic graph history.
- `REQUEST_DRAFT` cannot treat a UI timer as accepted async identity.
- `INLINE_MULTILINE` cannot use bare Enter as commit unless the profile/source contract explicitly reserves Enter.
- no profile may treat blur as commit merely because a component unmounted after cancel.

## 6. Conceptual Data Model

The following is a documentation model, not authorization to add these exact TypeScript types.

### 6.1 Session envelope

```ts
interface LibTVEditorSessionEnvelope {
  sessionId: string;
  profileId: LibTVEditorProfileId;
  profileVersion: number;
  route: "libtv";
  canvasId: string;
  canvasGeneration: number;
  ownerNodeId: string;
  fieldScope: readonly string[];
  openedAt: number;
  baseline: LibTVEditorBaseline;
  state: LibTVEditorSessionState;
}
```

`sessionId` is unique per open/reopen. It is not derived from node ID or time alone in production design. The operation handoff retains it as provenance even if a separate `operationId` becomes the async authority.

### 6.2 Baseline

```ts
interface LibTVEditorBaseline {
  ownerVersion?: number;
  fieldFingerprint: string;
  sourceMediaId?: string;
  sourceMediaVersion?: number;
  normalizedValue: unknown;
}
```

The baseline is field-scoped. An unrelated node position or status update does not automatically invalidate a Prompt draft. A source-media replacement does invalidate a bitmap editor even if the node ID is unchanged.

### 6.3 Working draft

```ts
interface LibTVEditorDraft<T> {
  value: T;
  fingerprint: string;
  dirty: boolean;
  validation: LibTVEditorValidation;
}
```

`dirty` compares normalized semantic value, not render object identity, pointer count or local selection highlight.

### 6.4 Local history

```ts
interface LibTVEditorHistory<T> {
  past: readonly LibTVEditorHistoryEntry<T>[];
  present: T;
  future: readonly LibTVEditorHistoryEntry<T>[];
  estimatedBytes: number;
  policy: LibTVEditorHistoryPolicy;
}

interface LibTVEditorHistoryEntry<T> {
  commandId: string;
  kind: string;
  before: T;
  after: T;
  estimatedBytes: number;
  committedAt: number;
}
```

An implementation may store deltas, commands or snapshots. The observable contract is before/after reversibility, ordering, budget and redo invalidation.

### 6.5 Commit intent

```ts
interface LibTVEditorCommitIntent<TPatch> {
  sessionId: string;
  profileId: LibTVEditorProfileId;
  canvasId: string;
  canvasGeneration: number;
  ownerNodeId: string;
  baselineFingerprint: string;
  sourceMediaId?: string;
  sourceMediaVersion?: number;
  patch: TPatch;
  draftFingerprint: string;
}
```

The intent is immutable and deeply detached from mutable component refs before delegation.

### 6.6 Async submission descriptor

```ts
interface LibTVEditorSubmissionDescriptor<TPayload> {
  operationId: string;
  sessionId: string;
  profileId: LibTVEditorProfileId;
  owner: LibTVOwnerGeneration;
  source: LibTVSourceVersion | null;
  payload: TPayload;
  resourceTransfers: readonly LibTVResourceTransfer[];
  acceptedAt: number;
}
```

The async authority, not the component, assigns or accepts `operationId`. A timer ID is never an operation ID.

## 7. Session State Machine

### 7.1 States

| State | Meaning |
|---|---|
| `CLOSED` | no foreground owner or local resources |
| `OPENING` | owner/baseline/source acquisition in progress |
| `OPEN_CLEAN` | draft equals baseline |
| `OPEN_DIRTY` | valid or invalid unaccepted semantic draft differs |
| `COMMITTING_SYNC` | one synchronous commit intent is being accepted |
| `SUBMITTING_ASYNC` | immutable descriptor acceptance/resource transfer in progress |
| `REJECTED_RETRYABLE` | acceptance failed; draft remains recoverable |
| `BASELINE_CONFLICT` | owner exists but scoped baseline/source drifted |
| `INVALIDATED` | owner/canvas/source no longer accepts the session |
| `ACCEPTED` | graph command or operation accepted; local disposal may follow |
| `DISPOSING` | release history/resources/listeners and return focus |

### 7.2 Transition table

| From | Event | To | Required effect |
|---|---|---|---|
| `CLOSED` | open valid owner | `OPENING` | allocate unique session; capture owner/generation |
| `OPENING` | baseline ready | `OPEN_CLEAN` | initialize draft/history; acquire declared leases |
| `OPENING` | load fails | `REJECTED_RETRYABLE` or `DISPOSING` | stable reason; no graph history; release partial leases |
| `OPEN_CLEAN` | semantic edit | `OPEN_DIRTY` | local draft only |
| `OPEN_DIRTY` | edit returns to baseline | `OPEN_CLEAN` | retain allowed local history; dirty false |
| open | local undo/redo/reset | open | mutate local draft/history only |
| open | cancel/allowed close | `DISPOSING` | zero semantic graph mutation; cancel unaccepted local work |
| open | submit invalid | same open state | field/surface reason; zero graph/operation |
| `OPEN_CLEAN` | commit | `ACCEPTED` or `DISPOSING` | no-op; zero graph history |
| `OPEN_DIRTY` | sync commit | `COMMITTING_SYNC` | freeze intent; lock duplicate acceptance |
| `COMMITTING_SYNC` | accepted | `ACCEPTED` | at most one graph-history entry |
| `COMMITTING_SYNC` | stale/invalid/conflict | `BASELINE_CONFLICT` or `REJECTED_RETRYABLE` | draft remains recoverable |
| `OPEN_DIRTY` | async submit | `SUBMITTING_ASYNC` | freeze descriptor; begin exact transfer |
| `SUBMITTING_ASYNC` | operation accepted | `ACCEPTED` | async authority now owns completion |
| `SUBMITTING_ASYNC` | acceptance failed | `REJECTED_RETRYABLE` | restore retryable draft/resources per transfer result |
| open | owner/source drift | `BASELINE_CONFLICT` or `INVALIDATED` | never silently overwrite dirty draft |
| `ACCEPTED` | profile close policy | `DISPOSING` | release only resources not transferred |
| `INVALIDATED` | reconcile | `DISPOSING` | stable owner-lost outcome; zero stale commit |
| `DISPOSING` | cleanup complete | `CLOSED` | no listeners, resources or local command owner remain |

### 7.3 Terminal rules

- `cancel` is terminal only for the editor session, not an already accepted async operation.
- `accepted_noop` can close without graph history.
- an invalidated editor cannot become accepted without a new session/baseline.
- disposal is exact once even if close, unmount and owner reconciliation occur together.
- an accepted async descriptor can outlive the editor UI; feedback/retry ownership must remain reachable elsewhere.

## 8. Baseline And Drift Contract

### 8.1 Capture

Opening captures:

- current route;
- canvas ID and generation;
- owner node ID;
- profile field scope;
- normalized scoped value fingerprint;
- source media identity/version when applicable;
- optional owner/node data version when available.

Copying only a render URL is insufficient for a bitmap editor because the same URL can be replaced/rebound without a stable version contract.

### 8.2 Drift classes

| Drift | Clean draft | Dirty draft |
|---|---|---|
| unrelated field changed | keep/rebase allowed | keep draft; update unrelated view only |
| scoped field changed to same normalized value | refresh baseline identity | preserve draft and refresh identity if safe |
| scoped field changed to different value | rebase automatically only if profile declares | enter `BASELINE_CONFLICT`; never overwrite draft |
| source media identity/version changed | reopen/reload source | invalidate or conflict; do not save over new source |
| node deleted | invalidate/dispose | invalidate/dispose; no commit |
| canvas generation changed | invalidate/dispose | invalidate/dispose; no commit |
| graph undo/redo changes owner scope | apply same drift policy | conflict/invalidate; local history is not auto-rebased |

### 8.3 Conflict dispositions

The implementation may offer, when safe and source-supported:

- discard local and reload current baseline;
- copy/export local draft before reload;
- explicit rebase for structured non-overlapping fields;
- keep open read-only for inspection;
- close with recoverable feedback.

It may not silently prefer local or remote while presenting success.

## 9. Dirty And Equality Contract

### 9.1 Semantic normalization

Equality is profile-specific:

- title may trim/fallback according to title policy;
- multiline Prompt preserves meaningful whitespace unless source contract says otherwise;
- rich text compares sanitized normalized HTML/model;
- records compare stable IDs, normalized coordinates and semantic fields;
- config compares canonical enum/number values;
- bitmap/vector edit compares operation/record fingerprint, not canvas object identity;
- range compares normalized bounded endpoints.

### 9.2 No-op

When normalized draft equals baseline:

- Apply/Save may close according to profile policy;
- no graph command/history entry is created;
- no async operation is submitted;
- no “generated/saved” success claim is emitted;
- local resources are released normally;
- focus returns to the declared owner.

### 9.3 Equality gateway

The graph command gateway repeats semantic equality before history push. Component-level dirty checks improve UX but are not the final trust boundary.

## 10. Local History Contract

### 10.1 Ownership

Local history is owned by exactly one active editor session. It is cleared/disposed at session end unless a profile explicitly serializes draft recovery outside graph history.

It does not enter `canvasStore.historyByCanvas` before accepted commit.

### 10.2 Gesture coalescing

For pointer editors:

```text
pointerdown
  -> capture interaction baseline
pointermove*
  -> mutate working present only
pointerup/pointercancel
  -> if semantic change, append one history entry
  -> clear redo
```

Pointer movement frequency and zoom do not change undo cardinality.

`pointercancel` finalizes the visible changed draft by default. A profile may restore interaction baseline instead, but must declare and verify that policy.

### 10.3 Atomic field edits

Mark descriptions, replacement choices, text attributes and other semantic record fields must be either:

- one local history entry per accepted field edit/selection; or
- explicitly native-history-owned within a focused input, then merged into the record present without claiming custom undo coverage.

The current Picture Edit behavior, where details mutate `present` but not history, is not accepted as a complete local-history contract.

### 10.4 Undo

Local undo:

- applies the previous draft state;
- moves current state to future;
- updates dirty/validation state;
- does not touch nodes, edges, selection, viewport or graph history;
- does not cancel an accepted async operation.

### 10.5 Redo

Local redo:

- applies the next future draft state;
- moves current state into past;
- is disabled after any new semantic draft command;
- is disabled after session disposal;
- is not restored by graph redo.

### 10.6 Reset

Default clone correctness policy: Reset is a reversible local command from current draft to baseline/default profile value. It clears redo like any new command.

A destructive “restore and collapse history” policy requires explicit profile/source evidence. Open Canvas `OC-074` is a counterexample/input, not the universal LibTV rule.

### 10.7 Budgets

Every custom-history profile declares:

- maximum entries;
- estimated byte budget;
- minimum baseline retention policy;
- eviction order;
- behavior when one entry exceeds budget;
- resource release on eviction;
- telemetry/diagnostic surface in development.

Bitmap estimates include width * height * bytes-per-pixel for every retained full snapshot. Entry count alone is invalid.

### 10.8 History representation

Preferred order of consideration:

1. semantic vector/record command replay;
2. compact deltas/tiles;
3. compressed snapshots;
4. bounded full snapshots only for small fixtures/media.

Open Canvas full `ImageData` snapshots are valid evidence for behavior, not a required LibTV storage representation.

## 11. Native, Local And Graph Undo Routing

When `Cmd/Ctrl+Z` or explicit Undo is invoked:

1. an active text input/contenteditable with native undo ownership handles it;
2. otherwise an active custom editor with local history handles it;
3. otherwise the ordinary LibTV graph context may handle graph undo;
4. page/browser defaults apply only when no application context claims it.

`Cmd/Ctrl+Shift+Z` / platform redo follows the same owner order. The command-context authority owns dispatch; this contract owns each local result.

An editor with no local undo must still consume a shortcut if allowing graph undo would invalidate its unaccepted draft without an explicit drift transition. It may present disabled/no-op local outcome rather than falling through.

## 12. Commit Trigger Contract

| Trigger | Allowed profiles | Rule |
|---|---|---|
| blur | `INLINE_SCALAR`, selected multiline/rich profiles only | commit only when blur is not caused by cancel/unmount and IME is inactive |
| Enter | scalar only by default | prevent default and commit once |
| modified Enter | multiline/rich | commit/submit once after composition ends |
| Apply/Use | modal config | explicit sync commit only |
| Save | bitmap/rich explicit-save | local export or sync commit; label must not imply durable persistence unless true |
| Submit/Generate | request/record editor | freeze immutable graph/async descriptor |
| Escape | all foreground profiles | one-layer policy: cancel/reject/prompt; never accidental blur commit |
| backdrop/close | modal/full-screen profiles | same declared dirty policy as close command |

### 12.1 Cancel reason guard

Before a cancel-triggered unmount/blur, the session records a close intent such as `CANCEL`, `OWNER_INVALIDATED` or `ACCEPTED`. Blur handlers consult it and cannot emit a second commit.

### 12.2 IME

- composing Enter/Escape is not treated as application commit/cancel;
- composition end updates the working draft before validation/commit;
- no local snapshot is appended for each composition update unless native history owns it;
- focus transfer waits until the accepted command completes or the session disposes.

### 12.3 Duplicate acceptance

Once `COMMITTING_SYNC` or `SUBMITTING_ASYNC` begins:

- primary accept is disabled;
- keyboard accept is ignored with a stable busy disposition;
- close/cancel follows the profile's pre/post-accept boundary;
- repeated callback delivery is idempotent by session/command/operation identity.

## 13. Synchronous Graph Handoff

### 13.1 Plan

The editor creates one immutable commit intent. The graph authority validates:

- active route/canvas/generation;
- owner existence/type;
- field/source baseline freshness;
- normalized semantic change;
- profile-specific data validity;
- references/resources if included;
- resulting graph invariants.

### 13.2 Outcome

| Outcome | Graph history | Editor result |
|---|---:|---|
| `ACCEPTED_CHANGED` | exactly one | accepted; close/retain per profile |
| `ACCEPTED_NOOP` | zero | close allowed without success overclaim |
| `REJECTED_INVALID` | zero | remain open with validation reason |
| `REJECTED_STALE` | zero | baseline conflict/reload choice |
| `REJECTED_OWNER_MISSING` | zero | invalidate/dispose |
| `REJECTED_ROUTE_OR_CANVAS` | zero | invalidate/dispose |

### 13.3 Selection and focus

Accepted sync commit preserves the owner selection unless the named graph command intentionally creates/selects a result node. Focus returns to the declared field/node/surface target after graph state settles.

Cancel does not change graph selection merely to hide the editor. Selection-driven close may already have another owner; in that case no focus restoration steals focus back.

## 14. Asynchronous Submission Handoff

### 14.1 Freeze

Before delegation, deep-freeze or deeply detach:

- normalized request fields;
- mark/region/range records;
- owner/canvas/source identities;
- resource transfer descriptors;
- visible model/provider/settings vocabulary;
- provenance/session ID.

Mutable refs or current component state cannot be read later by a timer/promise completion.

### 14.2 Acceptance boundary

An async editor may close only after:

- the operation owner accepts a unique descriptor;
- any required resource transfer has a deterministic result;
- a primary feedback/result owner remains reachable;
- retry or terminal failure can be presented without reconstructing lost local refs.

Exporting bytes alone is not operation acceptance.

### 14.3 Provisional graph state

If a source-backed profile creates a pending/result node at submit:

- the named graph transaction is explicit;
- it creates at most one semantic graph-history entry;
- transient progress patches do not create one history entry per update;
- operation identity links pending owner and result;
- undo of the graph placeholder does not imply provider cancellation;
- late completion follows async-ingress stale disposition.

### 14.4 Failure and retry

Acceptance failure retains the draft when resource ownership allows. Post-accept operation failure belongs to the operation/node/surface authority and can reopen/reconstruct an editor only from serializable descriptor data, never from a dead component closure.

## 15. Bitmap And Resource Contract

### 15.1 Source lease

The bitmap editor may own:

- decoded source bitmap;
- preview object URL;
- raster/vector working state;
- local-history buffers;
- exported `Blob`/`File` before transfer.

Each has one lease owner and exact create/transfer/release events under the media lifecycle authority.

### 15.2 Local history eviction

Evicting a bitmap snapshot releases its memory/resource immediately. Disposing the editor releases all non-transferred snapshots, decoder handles, object URLs and event/listener ownership.

### 15.3 Save/export

The editor distinguishes:

```text
local draft Save
  -> export bytes/records
  -> accept sync graph locator OR async materialization descriptor
  -> transfer ownership
  -> release local source/draft leases
```

A `blob:` URL may support a local fixture preview but cannot be presented as durable graph save or portable output.

## 16. Close, Cancel And Invalidation

### 16.1 Close policy registry

Profiles choose one explicit policy:

- `DISCARD_WITHOUT_PROMPT`: cheap/reversible local draft and source-backed behavior established;
- `PROMPT_IF_DIRTY`: expensive draft where clone product decision permits a confirmation;
- `BLOCK_WHILE_ACCEPTING`: pre-accept lock; failure returns retryable state;
- `DETACH_AFTER_ACCEPT`: operation continues under another feedback owner;
- `AUTO_COMMIT_ON_BLUR`: inline profile only with cancel guard.

No generic overlay close handler may decide this from DOM type alone.

### 16.2 Owner deletion

Deleting the owner invalidates the open session before graph mutation completes. The session cannot commit. Unaccepted resources release. An already accepted operation converges under async/delete authorities.

### 16.3 Canvas switch/delete

Canvas generation mismatch invalidates/disposes the editor. Component-local timers/promises cannot retarget the newly active canvas. No focus restoration crosses canvas/route ownership.

### 16.4 Selection change

Selection change may close a node-local editor only through its declared policy. Current image-mode reconciliation is a correct owner boundary but currently always discards because those modes have no dirty model.

### 16.5 Unmount

Unmount is cleanup, not an implicit semantic command. It cannot commit through blur, create graph history or report success.

## 17. Feedback And Accessibility

### 17.1 Primary state

An editor exposes one primary state/reason surface for:

- invalid draft;
- saving/submitting;
- baseline conflict;
- retryable acceptance failure;
- owner invalidation where still visible;
- local-history availability.

### 17.2 Command availability

- unavailable primary commands are disabled and semantically `aria-disabled`/native disabled;
- enabled commands have a working handler and observable outcome;
- an empty editor cannot show an enabled Save that does nothing;
- Undo/Redo disabled state follows the current local owner, not a decorative icon color;
- tooltips name the command but do not substitute for status/reason.

### 17.3 Announcements

Submitting, accepted, failed and conflict outcomes delegate announcement ownership to the feedback contract. Local undo/redo usually updates visible state without noisy global toast.

## 18. Honest Prototype Modes

### 18.1 Empty evidence-gated editor

Allowed:

- source-observed geometry/tools/guide;
- local tool selection;
- close/Escape and owner invalidation;
- disabled unavailable undo/redo/save/generate;
- explicit spec classification.

Disallowed:

- enabled inert command;
- fabricated result record or source behavior;
- local success copy that implies graph/provider acceptance;
- graph history from cosmetic tool selection.

### 18.2 Deterministic local simulation

A local simulation may:

- use a fake resolver/clock;
- produce request-shaped metadata and pending placeholder;
- verify operation/session/history semantics;
- report `local fixture`/prototype provenance in diagnostics/docs.

It may not treat a component timeout as a production operation identity or claim provider success media.

## 19. Required Invariants

| ID | Invariant | Current status |
|---|---|---|
| `LIBTV-EDS-I-001` | every foreground editor has unique session/profile/owner/canvas/generation identity | missing/partial |
| `LIBTV-EDS-I-002` | baseline is immutable and field/source scoped | missing |
| `LIBTV-EDS-I-003` | unaccepted draft mutation creates zero semantic graph history | partial islands |
| `LIBTV-EDS-I-004` | dirty uses profile-normalized semantic equality | missing/partial |
| `LIBTV-EDS-I-005` | cancel before acceptance creates zero graph/operation residue | partial |
| `LIBTV-EDS-I-006` | cancel/unmount cannot trigger blur commit | unverified |
| `LIBTV-EDS-I-007` | no-op acceptance creates zero graph history and zero async operation | graph gateway missing |
| `LIBTV-EDS-I-008` | one sync accepted edit creates at most one graph-history entry | partial |
| `LIBTV-EDS-I-009` | one pointer gesture creates at most one local-history entry | Picture/Subtitle positive |
| `LIBTV-EDS-I-010` | every semantic custom-editor field edit has declared undo ownership | Picture details incomplete |
| `LIBTV-EDS-I-011` | new local edit clears redo | mark/region positive |
| `LIBTV-EDS-I-012` | local undo/redo never directly mutates graph/selection/viewport | mark/region positive |
| `LIBTV-EDS-I-013` | reset policy is profile-declared and deterministic | partial |
| `LIBTV-EDS-I-014` | custom history has entry and byte/resource budgets | missing |
| `LIBTV-EDS-I-015` | history eviction/disposal releases resources exactly once | missing |
| `LIBTV-EDS-I-016` | native/local/graph undo owner precedence is deterministic | dispatch partial; semantics partial |
| `LIBTV-EDS-I-017` | IME composition cannot commit/cancel prematurely | design only |
| `LIBTV-EDS-I-018` | duplicate accept during commit/submit is idempotent | partial |
| `LIBTV-EDS-I-019` | active dirty draft is never silently overwritten by baseline drift | missing |
| `LIBTV-EDS-I-020` | source-media drift prevents bitmap save over newer source | missing |
| `LIBTV-EDS-I-021` | node delete/canvas generation change invalidates session before commit | image owner positive; others partial |
| `LIBTV-EDS-I-022` | unmount is cleanup only, never implicit semantic commit | design only |
| `LIBTV-EDS-I-023` | sync commit acceptance result controls close/retry/conflict | missing |
| `LIBTV-EDS-I-024` | async descriptor is immutable and retains session/owner/source identity | missing |
| `LIBTV-EDS-I-025` | component timer ID is not an operation identity | current timers are simulation only |
| `LIBTV-EDS-I-026` | editor closes after async acceptance only when failure/retry owner remains reachable | missing |
| `LIBTV-EDS-I-027` | graph undo never implies cancellation of accepted async work | design only |
| `LIBTV-EDS-I-028` | bitmap bytes/URLs/snapshots never enter semantic graph history | partial |
| `LIBTV-EDS-I-029` | resource transfer/release is exact once | missing |
| `LIBTV-EDS-I-030` | progress/transient patches do not inflate graph history | missing |
| `LIBTV-EDS-I-031` | enabled Save/Submit/Undo/Redo has a working observable outcome | violated by current inert chrome |
| `LIBTV-EDS-I-032` | evidence-gated empty modes keep unavailable commands disabled | Element Edit positive |
| `LIBTV-EDS-I-033` | editor Save and durable graph save are distinct in state/copy | missing/partial |
| `LIBTV-EDS-I-034` | focus return never steals focus across owner/canvas/route change | design only |
| `LIBTV-EDS-I-035` | route/store identity remains isolated | architecture positive |
| `LIBTV-EDS-I-036` | component specs match committed behavior and evidence status | TextNode violated |
| `LIBTV-EDS-I-037` | field-scoped unrelated updates do not invalidate dirty draft | design only |
| `LIBTV-EDS-I-038` | conflict resolution never silently claims success | design only |
| `LIBTV-EDS-I-039` | serialized retry data never depends on a dead component closure | missing |
| `LIBTV-EDS-I-040` | profile/source decisions remain explicitly evidence-gated | documentation authority |

## 20. Graph Invariant Projection

These IDs extend the graph catalog; this contract is their semantic authority.

| ID | Graph-level invariant |
|---|---|
| `LIBTV-GI-085` | open editor session captures immutable route/canvas/generation/owner/field/source baseline |
| `LIBTV-GI-086` | unaccepted draft and local history create zero semantic graph/history mutation |
| `LIBTV-GI-087` | cancel before acceptance creates zero semantic graph/history/operation residue |
| `LIBTV-GI-088` | one local pointer gesture is one local command independent of event frequency/zoom |
| `LIBTV-GI-089` | local undo/redo/reset never directly mutate graph/selection/viewport and new edit clears redo |
| `LIBTV-GI-090` | normalized no-op commit creates zero graph-history entry |
| `LIBTV-GI-091` | one accepted synchronous editor commit creates at most one named graph-history entry |
| `LIBTV-GI-092` | async editor handoff freezes session/owner/source identity before operation acceptance |
| `LIBTV-GI-093` | native/local/graph undo precedence follows active command context without fallthrough invalidation |
| `LIBTV-GI-094` | scoped baseline drift has explicit rebase/conflict/invalidate disposition and never overwrites dirty draft silently |
| `LIBTV-GI-095` | owner delete/canvas generation change invalidates open session before stale commit |
| `LIBTV-GI-096` | editor-local bytes/snapshots/URLs are budgeted resources outside semantic graph history |
| `LIBTV-GI-097` | submitting lock/idempotency and reachable failure/retry survive editor close policy |
| `LIBTV-GI-098` | graph undo of accepted projection does not imply cancellation of provider operation |
| `LIBTV-GI-099` | editor dirty/accepted, graph history/dirty and durable save revision remain separate states |
| `LIBTV-GI-100` | ordinary LibTV, FrameOS and Director editor/session/history owners remain route/store isolated |

## 21. Decision Queue

### `LIBTV-EDS-DQ-001`: source dirty close policy

Need disposable source evidence for close button, Escape, selection change and canvas switch.

### `LIBTV-EDS-DQ-002`: source local/global undo precedence

Need focused source observations per editor, not only shortcut documentation.

### `LIBTV-EDS-DQ-003`: source reset/redo behavior

Determine whether reset is reversible or collapses local history.

### `LIBTV-EDS-DQ-004`: source title/text commit triggers

Measure blur, Enter, modified Enter, Escape and IME behavior.

### `LIBTV-EDS-DQ-005`: annotate representation

Determine vector records, raster snapshot, mask, text objects and result media ownership.

### `LIBTV-EDS-DQ-006`: Image Edit Prompt persistence

Determine whether Prompt/references write live/coalesced node data or freeze only on Generate.

### `LIBTV-EDS-DQ-007`: bitmap history representation and production budget

Choose semantic records/deltas/tiles/compressed/full snapshot after an implementation spike; do not inherit Open Canvas's 40 full snapshots.

### `LIBTV-EDS-DQ-008`: source replacement during editor

Determine reload, reject, prompt or merge behavior.

### `LIBTV-EDS-DQ-009`: async close/failure/retry owner

Determine whether source keeps editor open, closes to node status or supports reopening request data.

### `LIBTV-EDS-DQ-010`: accepted submit graph cardinality

Determine source placeholder/result and global undo behavior with a disposable fixture.

### `LIBTV-EDS-DQ-011`: Picture detail local history

Clone correctness requires declared undo ownership; exact source grouping remains unknown.

### `LIBTV-EDS-DQ-012`: Video toolbar Undo/Redo owner

Determine whether commands target processing history, graph history or are unavailable in the observed state.

### `LIBTV-EDS-DQ-013`: dormant Camera dialog disposition

When implementation is authorized, reconnect to a proven owner or retire from current parity surface; do not silently retain canceled config.

### `LIBTV-EDS-DQ-014`: Segment Reshoot session/handoff

Determine close/cancel and request/result contract before upgrading local simulation.

### `LIBTV-EDS-DQ-015`: first authorized slice

Recommended default is pure session/history reducer + equality-aware graph commit adapter + migration of current functional Text/Picture/Subtitle islands. Source-specific Annotate activation remains separately gated.

### `LIBTV-EDS-DQ-016`: production recovery policy

Decide whether long/expensive unaccepted drafts survive accidental reload/crash. This is outside the first prototype slice and must not be confused with graph persistence.

## 22. `LIBTV-FIX-LOCAL-EDITOR-SESSION-01`

### 22.1 Purpose

Provide a deterministic, provider-free fixture for editor-session semantics. It validates local state and graph-history cardinality without implementing a real bitmap engine or backend.

### 22.2 Fixture substrate

| Part | Required behavior |
|---|---|
| fake clock | explicit `tick(ms)`; no wall-clock timer dependence |
| owner registry | canvas/generation/node/field/source versions and normalized values |
| session reducer | pure state/events/outcomes with deterministic IDs |
| graph oracle | before/after graph plus named history-entry count |
| async acceptor | controllable accept/reject/complete order and operation IDs |
| resource ledger | create/transfer/release counters and estimated bytes |
| focus oracle | active zone and return-owner log |
| feedback oracle | typed disposition/reason/primary owner log |

### 22.3 Owner aliases

| Alias | Profile | Baseline |
|---|---|---|
| `EDS-TEXT-1` | `INLINE_MULTILINE` | `content="alpha"`, field version 3 |
| `EDS-CONFIG-1` | `MODAL_CONFIG` | camera config version 2 |
| `EDS-REGION-1` | `RECORD_EDITOR` | empty regions, source video version 5 |
| `EDS-MARK-1` | `RECORD_EDITOR` | one mark with description/replacement fields |
| `EDS-BITMAP-1` | `BITMAP_EDITOR` | source media `media-a@7`, small synthetic 4x4 buffer |
| `EDS-RANGE-1` | `RANGE_SELECTOR` | `[0, 8]` within 30 seconds |
| `EDS-REQUEST-1` | `REQUEST_DRAFT` | Prompt/reference/settings version 4 |
| `EDS-EMPTY-1` | `EMPTY_EVIDENCE_GATED` | no semantic draft |

### 22.4 Small deterministic history policy

The fixture uses intentionally small budgets to force eviction:

```text
maxEntries = 4
maxEstimatedBytes = 96
retainBaseline = true
```

These values are fixture mechanics, not production recommendations.

### 22.5 Required pure cases

| Case | Events | Expected |
|---|---|---|
| `EDS-FX-001` open clean | open text owner | unique session; clean; zero graph/history |
| `EDS-FX-002` edit cancel | change text; Escape cancel | disposed; owner unchanged; zero graph history |
| `EDS-FX-003` cancel blur guard | change; mark cancel; deliver blur | no commit; zero graph history |
| `EDS-FX-004` no-op apply | config change then restore; Apply | accepted no-op; zero graph history |
| `EDS-FX-005` scalar commit | change text; commit | owner changed once; exactly one graph history |
| `EDS-FX-006` pointer coalescing | down; 20 moves; up | one local history entry; zero graph history |
| `EDS-FX-007` local undo/redo | gesture; undo; redo | draft roundtrip; graph unchanged |
| `EDS-FX-008` redo invalidation | two edits; undo; new edit | future empty |
| `EDS-FX-009` reversible reset | edit; reset; undo | draft restored to pre-reset edit |
| `EDS-FX-010` semantic field history | edit mark description/replacement | declared local/native owner; no invisible gap |
| `EDS-FX-011` sync stale reject | edit; bump scoped owner version; commit | conflict; draft retained; zero graph history |
| `EDS-FX-012` unrelated patch | edit Prompt; bump unrelated status | draft remains; commit allowed by scoped policy |
| `EDS-FX-013` source drift | bitmap edit; replace source version | invalid/conflict; no export apply |
| `EDS-FX-014` owner delete | edit; delete node; commit | invalidated/disposed; zero stale graph entry |
| `EDS-FX-015` canvas switch | edit; change generation | disposed; no cross-canvas focus/graph effect |
| `EDS-FX-016` async accept | request edit; submit; accept op | immutable descriptor; duplicate submit ignored |
| `EDS-FX-017` async accept reject | submit; reject acceptance | retryable draft/resources remain exact |
| `EDS-FX-018` post-accept late result | accept; close; switch canvas; complete | async authority marks stale/owner disposition; no retarget |
| `EDS-FX-019` budget eviction | append entries over 96 bytes | deterministic eviction; baseline retained; exact release |
| `EDS-FX-020` dispose idempotency | close + unmount + owner reconcile | one disposal; one release per lease |
| `EDS-FX-021` IME guard | composition start; Enter/Escape; end | no premature accept/cancel |
| `EDS-FX-022` local-vs-graph undo | dirty custom editor; modifier undo | local entry changes; graph history untouched |
| `EDS-FX-023` graph undo after commit | accepted sync commit; close; graph undo | graph restores baseline; session stays closed |
| `EDS-FX-024` empty command honesty | open empty mode | Save/Undo/Redo/Generate unavailable; zero handlers/outcomes |

### 22.6 Required browser scenes

When implementation is authorized, a focused harness should render:

1. TextNode edit/cancel/commit with focus return;
2. Picture or Subtitle pointer gesture with local undo/redo and unchanged graph count;
3. duplicate submit lock and one graph result;
4. owner deletion/canvas switch disposal;
5. an empty evidence-gated image mode with disabled unavailable commands;
6. a small synthetic bitmap history that crosses the fixture byte cap;
7. IME composition sequence in a multiline field;
8. graph undo after accepted commit, not while local draft owns undo.

### 22.7 Reset

Reset the fake clock, owner registry, graph/history oracle, session reducer, async acceptor, resource ledger, focus owner and feedback log. No real file, object URL, provider or source site is required.

## 23. `LIBTV-VR-022`

### 23.1 Pure verification

The verifier checks:

- session ID uniqueness and owner/generation capture;
- profile registry completeness;
- semantic dirty/no-op normalization;
- legal state transitions and terminal disposal;
- gesture coalescing and redo invalidation;
- history entry/byte budget and exact release;
- cancel blur guard;
- sync commit outcome/history cardinality;
- baseline/source/owner/canvas drift dispositions;
- async descriptor immutability/idempotency;
- native/local/graph command-owner results;
- route/store isolation.

### 23.2 Focused browser verification

Required assertions:

- visible enabled command has handler and observable state/result;
- unavailable empty-mode commands are disabled;
- local undo/redo state matches local history;
- local interactions do not change graph history until acceptance;
- one accepted sync edit changes graph history exactly once;
- cancel leaves graph/operation unchanged;
- duplicate submit does not duplicate graph result/operation;
- Escape closes one layer and cannot commit through blur;
- owner invalidation closes without cross-canvas mutation;
- focus return follows owner policy;
- no console/runtime error and no unreleased fixture lease.

### 23.3 Replacement assertions

`LIBTV-VR-022` replaces future ad hoc assertions such as:

- checking only that an Undo icon exists;
- checking only local `submitted=true` copy;
- assuming one timeout callback is one operation;
- assuming component unmount proves cancel;
- assuming graph snapshot count equals semantic command count;
- testing Picture/Subtitle local history without semantic detail fields;
- treating a rendered Save button as implemented.

### 23.4 Non-goals

The verifier does not prove:

- exact LibTV source close/reset/shortcut semantics;
- real raster quality or vector annotation engine;
- provider execution/cancellation;
- graph persistence/autosave;
- remote collaboration conflict resolution;
- production bitmap budget values.

## 24. Graph Transaction Cases

| ID | Scenario | Expected |
|---|---|---|
| `LIBTV-GC-109` open editor | valid owner/baseline | unique clean session; zero graph/history |
| `LIBTV-GC-110` inline changed commit | dirty text/config | one normalized owner patch; one history |
| `LIBTV-GC-111` Escape cancel | dirty local draft | zero graph/history/operation residue |
| `LIBTV-GC-112` no-op apply | normalized draft equals baseline | close/no-op; zero graph history |
| `LIBTV-GC-113` pointer gesture | many move events | one local entry; zero graph history |
| `LIBTV-GC-114` local undo/redo | active custom history | local draft only; graph unchanged |
| `LIBTV-GC-115` redo invalidation | undo then new draft command | future cleared; graph unchanged |
| `LIBTV-GC-116` reset then cancel | reversible local reset | owner remains original; zero graph history |
| `LIBTV-GC-117` record editor accept | valid marks/regions | one frozen payload; one named graph/operation handoff |
| `LIBTV-GC-118` async submit accept | valid request draft | one immutable operation; duplicate accept ignored |
| `LIBTV-GC-119` async acceptance failure | resolver rejects before acceptance | retryable draft; no accepted operation/history leak |
| `LIBTV-GC-120` late completion | owner/source/canvas changed | async stale disposition; no current-owner overwrite |
| `LIBTV-GC-121` owner delete | dirty open editor | invalidate/dispose; zero stale commit; exact release |
| `LIBTV-GC-122` canvas switch | dirty/submitting session | no retarget; focus/resource/operation follow declared owner |
| `LIBTV-GC-123` baseline drift | scoped external field change | conflict/rebase policy; never silent draft replacement |
| `LIBTV-GC-124` bitmap budget | history exceeds bytes/entries | deterministic eviction and exact release |
| `LIBTV-GC-125` graph undo after accepted commit | session closed | graph restores previous semantic state; no local session revival |
| `LIBTV-GC-126` route isolation | FrameOS/Director event | no ordinary LibTV session/history/graph effect |

## 25. Implementation Slices After Authorization

### Slice A: pure profile/session/history model

- discriminated profile registry;
- pure state reducer and stable outcomes;
- normalization/dirty/no-op helpers;
- local-history budget/coalescing helpers;
- fixture cases without React/runtime store changes.

### Slice B: equality-aware graph commit adapter

- current owner/generation/fingerprint validation;
- named sync command result;
- zero history for no-op/reject;
- one history for accepted change;
- no migration of unrelated graph commands yet.

### Slice C: migrate current functional islands

- correct TextNode cancel/blur/commit guard;
- make Picture semantic detail edits history-owned;
- align Subtitle submit/idempotency with one acceptance path;
- retain current visuals/geometry and source evidence boundaries.

### Slice D: command honesty pass

- classify every visible editor Save/Submit/Undo/Redo;
- disable evidence-gated unavailable commands;
- do not activate Annotate/Image Edit/Video Processing behavior without profile/result evidence;
- add stable component docs/selectors.

### Slice E: deterministic request handoff

- replace component timer identity with fake operation acceptor in fixture;
- freeze owner/source/session descriptor;
- integrate existing async/feedback contracts;
- keep provider absent.

### Slice F: source-evidence-gated Annotate vertical slice

- only after record/result/source behavior evidence;
- prefer semantic vector records for local history where possible;
- enforce byte/resource budget for any raster snapshots;
- one save/export handoff with media lifecycle ownership.

### Slice G: secondary profiles

- Image Edit Prompt/reference persistence;
- Segment Reshoot cancel/handoff;
- Camera dialog owner/reopen baseline;
- video processing Undo/Redo owner.

### Slice H: production adapters

- real provider/materializer/cancellation;
- durable draft recovery if approved;
- collaboration/persistence versioning.

These remain separately authorized and are not implied by the design contract.

## 26. Source Evidence Acquisition

Use a disposable source node/project and smallest reversible action set:

1. record initial graph/selection/editor DOM;
2. open one editor and make one local reversible draft edit;
3. inspect command enabled states without saving first;
4. test local undo/redo/reset;
5. test Escape/close and confirm graph unchanged;
6. reopen and test one accepted edit only when mutation is explicitly authorized;
7. inspect result/selection/global undo cardinality;
8. test failure/retry only through a safe non-paid invalid fixture;
9. reset/delete only disposable artifacts;
10. record source fact separately from clone decision.

Stop before private upload, paid/provider execution, shared-project deletion or ambiguous persistence mutation.

## 27. Open Canvas Adoption Result

| Method | Decision | LibTV adaptation |
|---|---|---|
| random foreground session identity | `ADAPT_TO_LIBTV` | retain through graph/async provenance with owner/source versions |
| local draft separate from graph | `ADOPT_METHOD` | apply profile registry across current editors |
| one bitmap snapshot per stroke | `ADAPT_TO_LIBTV` | preserve observable gesture history; choose safer representation/budget |
| redo truncation | `ADOPT_METHOD` | all custom-history profiles |
| normalized no-op/conflict guard | `ADOPT_METHOD` | graph commit gateway; acceptance-aware close |
| bounded decoded dimensions/pixels | `ADOPT_METHOD` | media/bitmap profile registry |
| stale load projection suppression | `ADAPT_TO_LIBTV` | add caller-owned abort and source version |
| rich-text sanitization at commit | `ADOPT_METHOD` | declared rich profile |
| export/upload timing logs | `ADOPT_METHOD` | fixture/diagnostic provenance |
| 40 full `ImageData` entries | `REJECT_TRANSPLANT` | byte/resource budget and compact history |
| close before upload acceptance | `REJECT_TRANSPLANT` | close only after accepted handoff/reachable retry |
| node-ID-only completion | `REJECT_TRANSPLANT` | operation/session/source/canvas freshness |
| active-draft effect resync | `REJECT_TRANSPLANT` | explicit clean rebase or dirty conflict |
| autosave revision as editor history | `REJECT_TRANSPLANT` | separate persistence/graph/local authorities |
| monolithic canvas-shell editor owner | `REJECT_TRANSPLANT` | route/session adapters with explicit ownership |

## 28. Stop And Maintenance Conditions

Stop implementation/evidence work when it would require:

- runtime/test/submodule changes without explicit authorization;
- source mutation outside a disposable fixture;
- private media upload or paid provider execution;
- inventing exact source dirty-close/reset/history behavior;
- placing editor-local buffers in semantic graph history;
- merging ordinary LibTV, FrameOS and Director stores;
- introducing persistence/collaboration semantics under the name “editor Save”;
- enabling primary commands before an observable result owner exists.

Maintain this contract when:

- a new editor surface/profile is added;
- command trigger/close/undo behavior changes;
- graph command acceptance/history semantics change;
- async/media authorities change their handoff envelope;
- a source fixture resolves a decision queue item;
- the Open Canvas SHA changes and `OC-071..080` are re-audited;
- fixture/verifier IDs or graph invariant/case ranges change.

## 29. Completion Criteria

This design contract is complete because it defines:

- profile registry and invalid combinations;
- immutable session/baseline/draft/commit/submission concepts;
- full open/edit/commit/submit/conflict/invalidate/dispose state machine;
- baseline drift and field-scoped equality rules;
- native/local/graph undo precedence;
- gesture coalescing, redo/reset and byte/resource budgets;
- blur/Enter/Escape/IME/duplicate acceptance behavior;
- synchronous graph and asynchronous operation handoff;
- bitmap/resource ownership and exact release;
- close/cancel/selection/delete/canvas/unmount lifecycle;
- honest empty/simulation modes and command availability;
- 40 invariants, 16 graph invariants and 18 graph cases;
- deterministic fixture `LIBTV-FIX-LOCAL-EDITOR-SESSION-01`;
- verifier `LIBTV-VR-022`;
- implementation slices and source evidence gates;
- Open Canvas adoption/rejection decisions.

Runtime, fixture code, verifier code, real Annotate behavior, provider work and exact LibTV source parity remain unimplemented or evidence-gated by design.
