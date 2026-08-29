# LibTV Director Current Verifier Manifest

> Status: `CURRENT_MANIFEST_RECORDED` / `PURE_CODEC_GATE_RECORDED_PASS` /
> `OWNER_SESSION_GATE_RECORDED_PASS` /
> `BROWSER_SMOKE_RECORDED_PASS` /
> `AUTHORED_RUNTIME_GATE_RECORDED_PASS` /
> `HISTORY_GATE_RECORDED_PASS` / `POINTER_LIFECYCLE_GATE_RECORDED_PASS` /
> `REFERENCE_DELETE_GATE_RECORDED_PASS` / `ASYNC_AUTHORITY_GATE_RECORDED_PASS` /
> `PERSISTENCE_GATE_RECORDED_PASS` /
> `CLIPBOARD_REMAP_GATE_RECORDED_PASS` /
> `OWNER_REACHABILITY_GATE_RECORDED_PASS` /
> `POINTER_CANCELLATION_GATE_RECORDED_PASS` /
> `IMPORT_EXPORT_GATE_RECORDED_PASS` /
> `LOCAL_RESOURCE_MATERIALIZATION_GATE_RECORDED_PASS` /
> `COMMAND_FEEDBACK_GATE_RECORDED_PASS` /
> `LOCK_EDITABILITY_GATE_RECORDED_PASS` /
> `SELECTION_CRUD_GATE_RECORDED_PASS` /
> `CURRENT_GATE_SERIAL_REGRESSION_RECORDED_PASS` /
> `FULL_HISTORICAL_SUITE_NOT_CURRENTLY_RUN`.
>
> Audit date: 2026-08-29.
>
> Scope: `scripts/verify-liblib-batch35.py` through Batch 50, Batch 59,
> Batch 67 pure codec verifier, Batch 68 hybrid owner/session verifier,
> Batch 69 authored/runtime verifier, Batch 70 command/history verifier,
> Batch 71 pointer-lifecycle verifier, Batch 72 reference-aware delete verifier,
> Batch 73 async-authority verifier, Batch 74 persistence verifier and Batch 75
> clipboard identity-remap verifier, Batch 76 owner-reachability verifier, and
> Batch 78 pointer-cancellation verifier, Batch 79 whole-project duplicate verifier,
> Batch 80 durable tombstone verifier, Batch 81 strict project import/export
> verifier, Batch 82 local resource materialization verifier, Batch 83 command
> feedback verifier and Batch 84 lock/editability verifier, including the R3F
> Canvas teardown regression exposed by the Batch 68 cross-owner sequence, and
> Batch 85 selection/CRUD discoverability verifier.
>
> Fixture authority:
> [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md).
>
> Director design authority:
> [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)
> and
> [`LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md).

## 1. Purpose

The repository has 17 historical Director-focused Playwright scripts, one pure
codec verifier, eighteen current hybrid pure/browser reliability verifiers and
one current browser smoke.
The historical browser scripts preserve valuable
bounded clone behavior, but they were created batch by batch and do not form a
single current gate on their own:

- Batch 35-50 overwrite tracked historical screenshots;
- Batch 40 performs a real browser `MediaRecorder` export;
- Batch 47/48 touch the Director local-model storage key;
- most scripts prove a dated clone contract, not current LibTV source parity;
- none of the historical browser scripts covers project identity, strict
  document decode, owner generation, Director history or reference-aware delete;
- Batch 67 covers the strict V1 document slice；
- Batch 68 covers structured owner keys、per-owner in-memory project records、
  open/switch/close generation、A/B/cross-canvas isolation and active-delete
  tombstone compatibility；Batch 76 owns current all-canvas reachability and
  two-phase shell/runtime cleanup.
- Batch 69 covers authored/runtime object authority、timeline/path projection
  stability、object/camera/pose authoring restore and existing owner/graph
  isolation.
- Batch 70 covers project-local command results、semantic mutation history、
  no-op/rejection outcomes、gesture coalescing、undo/redo、redo truncation、
  close/reopen history continuity and ordinary graph/history isolation.
- Batch 71 covers Inspector numeric/range、pose、camera、path anchor/Bezier、
  path transform and pencil/pen pointer lifecycle with commit/cancel/
  pointercancel cleanup and ordinary graph/history isolation.
- Batch 72 covers pure reference-aware delete planning、object/group/camera/track/
  path/capture/resource closure、last-camera rejection、selection/runtime repair、
  keyboard routing、exact delete/undo/redo and ordinary graph/history isolation.
- Batch 73 covers capture/export/phone async operation identity、owner/session/
  generation and source/request fingerprint freshness、attempt supersession、
  duplicate/terminal conflict handling、graph result projection and resource
  transfer/release exactly once.
- Batch 74 covers browser-local versioned persistence envelope、strict restore、
  owner/project/generation/fingerprint guards、stale save ignore、corrupt/future/
  mismatch rejection、runtime/UI/resource-byte exclusion、reload recovery and
  storage-failure session continuity.
- Batch 75 covers project-scoped session clipboard、typed closure、two-pass
  identity/reference remap、camera detach/freeze、stable resource alias、
  deterministic repeated placement、one-entry history、shortcut priority and
  reload non-persistence.
- Batch 76 covers all-canvas live owner collection、inactive source/canvas
  one-time tombstone、active shell/session/runtime two-phase cleanup、
  deterministic/idempotent reconciliation、tombstoned reopen rejection、
  delayed async stale、graph undo boundary and retained persistence.
- Batch 78 covers Curve Editor begin-result ownership、pointer id filtering、
  pointerup commit、pointercancel/blur/hidden/unmount cancellation、Phone Vcam
  pointer capture release and reuse、Timeline scrub stale-pointer prevention。
- Batch 79 covers whole-project graph/Director identity remap and clean target
  authority；
- Batch 80 covers durable tombstone、reload resurrection guard、capture sidecar
  cleanup and local resource reachability；
- Batch 81 covers strict project JSON import/export、owner/project rebind、
  transient/runtime exclusion、one-entry history、undo/redo and zero-partial
  file workflow。
- Batch 82 covers typed local resource descriptor/provenance、loading/ready/
  failed/canceled/released lifecycle、attempt freshness、retry/cancel/release、
  finite OBJ/FBX local materialization、proxy retention on parse failure and
  model-library status feedback。
- Batch 83 covers typed Director command outcome/reason projection、visible
  fixed-header status surface、ARIA status semantics、committed-success noise
  suppression、meaningful no-op visibility、mobile geometry and zero-diagnostic
  feedback rendering。
- Batch 84 covers Director object-tree lock/visibility controls、locked-target
  Inspector/Viewport/Timeline/Curve edit protection、typed
  `DIRECTOR_TARGET_LOCKED` rejection、zero document/history mutation and unlock
  recovery。
- Batch 85 covers Director object-tree selection context、single/multi-selection
  count projection、project-scoped copy、reference-aware batch delete、clear
  selection zero-history behavior and mobile discoverability。

This manifest defines which script is cheap and safe enough for a current smoke,
which scripts are candidates for a future merge gate, and which remain manual
historical regressions.

## 2. Classification

| Class | Meaning | Default execution |
|---|---|---|
| `CURRENT_GATE` | Current HEAD was run in this batch; low-cost and bounded enough for routine use | Run for every Director reliability batch |
| `MERGE_CANDIDATE` | High-value current behavior, but artifact/storage/runtime side effects must be isolated first | Run manually when the affected slice changes |
| `HISTORICAL_ONLY` | Preserves a dated clone capability and screenshots; too broad, expensive or superseded for routine gating | Run only for targeted regression or release audit |
| `SOURCE_STALE` | Assertions use source-shaped vocabulary or behavior without fresh authenticated evidence | Never interpret a pass as current source parity |

`SOURCE_STALE` is an evidence label and can coexist with an execution class.

## 3. Script Inventory

| Script | Primary capability | Execution class | Artifact/storage/runtime cost | Current interpretation |
|---|---|---|---|---|
| Batch 35 | R3F workspace, camera framing, still capture, graph return, undo/redo | `HISTORICAL_ONLY` | 6 tracked screenshots; graph mutation; desktop/mobile WebGL | Foundational clone regression; entry/WebGL is now more cheaply covered by Batch 59 |
| Batch 36 | typed timeline, keyframes, playback | `HISTORICAL_ONLY` | 4 tracked screenshots; timer/playback | Dated timeline contract; does not prove authored/runtime separation |
| Batch 37 | preset paths and speed curves | `HISTORICAL_ONLY` | 5 tracked screenshots; WebGL sampling | Dated path contract; no project/history authority |
| Batch 38 | pencil/pen path authoring and anchors | `HISTORICAL_ONLY` | 5 tracked screenshots; pointer simulation | Dated authoring contract; gesture updates are not coalesced Director history |
| Batch 39 | path transform/reset | `HISTORICAL_ONLY` | 5 tracked screenshots; repeated store writes | Dated transform contract; does not prove one gesture/one history entry |
| Batch 40 | real animation export and video graph return | `HISTORICAL_ONLY` | 5 tracked screenshots; real `MediaRecorder`; object URL and graph mutation | Expensive manual export regression; async owner freshness remains uncovered |
| Batch 41 | phone virtual camera and take import | `HISTORICAL_ONLY` | 5 tracked screenshots; timed recording/import | Dated phone workflow; runtime/session/document separation remains uncovered |
| Batch 42 | character pose and pose tracks | `HISTORICAL_ONLY` | 4 tracked screenshots; WebGL pixel comparisons | Dated pose contract; slider gesture history remains uncovered |
| Batch 43 | camera look-at/follow modes | `HISTORICAL_ONLY` | 5 tracked screenshots; multiple WebGL samples | Dated relation contract; general camera delete/repair remains uncovered |
| Batch 44 | preset camera motion replace/append | `HISTORICAL_ONLY` | 6 tracked screenshots; repeated scenario setup | Dated camera preset contract; no command/history authority |
| Batch 45 | groups, crowd and group tracks | `HISTORICAL_ONLY` | 6 tracked screenshots; multi-selection/playback | Dated aggregate contract; group delete closure remains uncovered |
| Batch 46 | capture gallery, viewer, bulk graph return | `MERGE_CANDIDATE` | 5 tracked screenshots; capture and graph mutation | Valuable resource/graph bridge coverage once artifacts can be redirected |
| Batch 47 | proxy model library categories and insertion | `HISTORICAL_ONLY` | 4 tracked screenshots; clears local-model storage | Compatibility coverage largely superseded by Batch 59 search/preview/add smoke |
| Batch 48 | local model import, persistence, refresh and cleanup | `MERGE_CANDIDATE` | 4 tracked screenshots; localStorage mutation and reload | High-value resource lifecycle regression; requires isolated BrowserContext and explicit cleanup |
| Batch 49 | viewport coordinate gizmo and camera recovery | `MERGE_CANDIDATE` | 5 tracked screenshots; dual WebGL pixel checks | High-value renderer/camera smoke once artifact output is isolated |
| Batch 50 | workspace collapse, mobile drawers and keyboard boundary | `MERGE_CANDIDATE` | 4 tracked screenshots; desktop/mobile focus checks | High-value shell/focus regression once artifact output is isolated |
| Batch 59 | asset search, preview-only selection, explicit insertion, WebGL and graph isolation | `CURRENT_GATE` | Writes only its deterministic tracked runtime audit; no page screenshot writes | Current low-cost Director smoke and present `LIBTV-VR-024` browser seed |
| Batch 67 | V1 document snapshot, strict decode/normalize/encode and invalid/future/reference corpus | `CURRENT_GATE` | Pure Node 24 process; no browser, storage, graph or screenshot artifact | Current `LIBTV-VR-024` project-codec gate; does not prove project registry or store integration |
| Batch 68 | structured owner key、project/session/generation、A/B/cross-canvas isolation、duplicate reset and active-delete tombstone compatibility | `CURRENT_GATE` | Pure Node registry corpus + one headless Playwright page；writes one structured runtime audit and no screenshots/storage | Current `LIBTV-VR-024` owner/session gate；Batch 76 now owns all-canvas reachability and two-phase cleanup |
| Batch 69 | authored/runtime object split、seek/playback/path stability、object/camera/pose authoring restore、close/reopen and owner/graph isolation | `CURRENT_GATE` | Static Node source gate + one headless Playwright page；writes one structured runtime audit and no screenshots/storage | Current `LIBTV-VR-024` authored/runtime gate；does not prove history/delete、async destination、durable persistence or source parity |
| Batch 70 | project-local command result、semantic history、no-op/rejection、gesture coalescing、undo/redo and reopen continuity | `CURRENT_GATE` | Pure Node source gate + one headless Playwright page；writes one structured runtime audit and no screenshots/storage | Current `LIBTV-VR-024` command/history gate；does not prove reference-aware delete、async destination、durable persistence or source parity |
| Batch 71 | Inspector、pose、camera、path and free-draw gesture lifecycle | `CURRENT_GATE` | Pure source gate + one fresh-page Playwright page；writes one structured runtime audit and no screenshots/storage | Current `LIBTV-VR-024` pointer-lifecycle gate；does not prove reference-aware delete、async destination、durable persistence or source parity |
| Batch 72 | reference-aware delete planner、closure repair、last-camera/resource policy and delete/undo/redo | `CURRENT_GATE` | Pure planner corpus + five fresh-page Playwright scenarios；writes one structured runtime audit and no screenshots/storage | Current `LIBTV-VR-024` reference-delete gate；does not prove async destination、durable persistence、copy/paste or source parity |
| Batch 73 | Director capture/export/phone async authority、attempt supersession、stale/duplicate/invalid completion and resource ownership | `CURRENT_GATE` | Pure Node authority corpus + one fresh-page Playwright page；writes one structured runtime audit and no screenshots | Current `LIBTV-VR-024` async-authority gate；does not prove ordinary canvas async ingress、durable persistence、copy/paste or source parity |
| Batch 74 | Director browser-local durable project persistence、strict envelope restore、stale save and storage failure | `CURRENT_GATE` | Pure Node persistence corpus + fresh-page Playwright BrowserContext；writes one structured runtime audit and no screenshots | Current `LIBTV-VR-024` persistence gate；does not prove ordinary canvas persistence、remote storage、real resources or source parity |
| Batch 75 | Director project-scoped clipboard identity remap and guarded keyboard routing | `CURRENT_GATE` | 12-scenario pure packet/planner corpus + fresh-page Playwright BrowserContext；writes one structured runtime audit and no screenshots | Current `LIBTV-VR-024` clipboard-remap gate；does not prove LibTV source copy/paste UI、system/cross-project clipboard、whole-project duplicate or real resource transfer |
| Batch 76 | Director all-canvas owner reachability reconciliation and tombstone cleanup | `CURRENT_GATE` | 9-scenario pure planner corpus + A/B/cross-canvas fresh-page Playwright；writes one structured runtime audit and no screenshots | Current `LIBTV-VR-024` owner-reachability gate；does not prove durable tombstone、storage/resource deletion、undo restore、whole-project duplicate or source parity |
| Batch 78 | Director Curve/Phone Vcam/Timeline pointer cancellation, cleanup and R3F teardown | `CURRENT_GATE` | Static source contract + seven fresh-page Playwright scenarios + cross-owner/canvas teardown regression；writes one structured runtime audit and no screenshots | Current `LIBTV-VR-024` pointer-cancellation gate；does not prove source-exact Director pointer behavior、real phone sensors、touchpad hardware or source parity |

| Batch 79 | Director whole-project duplicate | `CURRENT_GATE` | Pure Node two-pass planner corpus + fresh-page Playwright duplicate/isolation scenario；writes `runtime-audit.json` and no screenshots | Current `LIBTV-VR-024` whole-project duplicate gate；does not prove LibTV source duplicate semantics、remote persistence、capture bytes or real resource loading |
| Batch 80 | Director durable tombstone、storage/resource cleanup | `CURRENT_GATE` | Pure Node strict tombstone corpus + fresh-page active/inactive owner cleanup、capture sidecar、local resource reachability and reload reopen guard；writes `runtime-audit.json` and no screenshots | Current `LIBTV-VR-024` durable-tombstone gate；does not prove LibTV source delete/recovery UI、remote persistence or real resource materialization |
| Batch 81 | Director strict project JSON import/export | `CURRENT_GATE` | Pure V1 document/rebind corpus + fresh-page BrowserContext download/file-input workflow；writes `runtime-audit.json` and no screenshots | Current `LIBTV-VR-024` import/export gate；does not prove LibTV source file format/UI、remote sync or real resource materialization |
| Batch 82 | Director local resource lifecycle and finite OBJ/FBX materialization | `CURRENT_GATE` | Pure lifecycle corpus + fresh-page local-model materialization workflow；writes `runtime-audit.json` and no screenshots | Current `LIBTV-VR-024` local-resource gate；proves clone-owned session materialization only，不证明生产 loader/cache、remote persistence 或 LibTV source resource semantics |
| Batch 83 | Director command result feedback projection | `CURRENT_GATE` | Pure reason/disposition mapping + fresh-page rejection/commit/no-op/ARIA/mobile workflow；writes `runtime-audit.json` and no screenshots | Current `LIBTV-VR-024` command-feedback gate；proves clone-owned foreground feedback only，不证明 LibTV source feedback taxonomy、文案、ARIA、颜色或 placement |
| Batch 84 | Director object-tree lock/visibility and locked-target edit protection | `CURRENT_GATE` | Pure source contract + fresh-page Playwright lock/Inspector/Viewport/history/mobile workflow；writes `runtime-audit.json` and no screenshots | Current `LIBTV-VR-024` lock/editability gate；proves clone-owned lock protection and `DIRECTOR_TARGET_LOCKED` zero-mutation rejection，不证明 LibTV source Director lock UI、文案或 CSS |
| Batch 85 | Director object-tree selection context and CRUD discoverability | `CURRENT_GATE` | Pure source contract + fresh-page Playwright single/multi-selection/copy/clear/batch-delete/mobile workflow；writes `runtime-audit.json` and no screenshots | Current `LIBTV-VR-024` selection/CRUD gate；proves clone-owned selection action bar and existing command reuse，不证明 LibTV source Director selection bar、文案或 CSS |

All historical source-shaped scripts and the new reliability gates remain
`SOURCE_STALE_OR_UNKNOWN` for exact LibTV Director DOM/CSS、project persistence、
delete semantics and undo/redo behavior. Their passes only prove clone-owned
contracts.

## 4. Current Gates

### 4.1 Commands

Run the pure codec gate without a dev server:

```bash
python3 scripts/verify-liblib-batch67.py
```

Use the repository-standard `4317` port and a same-origin host name with the
Next dev server. The following is the complete current-gate sequence; keep it
serial because several scripts use browser-local state or WebGL:

```bash
npm run dev
for batch in 59 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83; do
  LIBLIB_BASE_URL=http://localhost:4317 \
    python3 "scripts/verify-liblib-batch${batch}.py" || exit 1
done
```

Do not substitute `127.0.0.1` unless `allowedDevOrigins` explicitly permits it.
On 2026-08-27, Next 16.2.1 blocked the dev resource request from
`127.0.0.1`; the page returned HTTP 200 and the Director entry was visible, but
client hydration did not make the click effective. The same clean server passed
with `localhost:4317`.

### 4.2 Current recorded results

Batch 67 pure codec:

| Field | Result |
|---|---|
| Date | 2026-08-27 |
| Clone HEAD | `1bc1043` |
| Runtime | Node 24 type stripping through Python wrapper |
| Valid corpus | 3 objects、1 group、4 track kinds、edited path、resource and capture descriptor |
| Invalid corpus | 17 malformed/future/unknown/duplicate/dangling/non-finite cases |
| Additional assertions | deterministic round-trip、zero partial、input isolation、runtime/media-byte exclusion、order preservation |
| Artifact/storage/browser cost | none |

Batch 59 browser smoke:

| Field | Result |
|---|---|
| Date | 2026-08-27 |
| Clone HEAD | `d4bbb41` before Batch 66 closeout |
| Server | fresh Next dev server, port 4317 |
| Browser | Playwright Chromium, headless |
| Desktop | `1440x900`, WebGL nonblank, search/preview/add/tree/Inspector/graph isolation passed |
| Mobile | `390x844`, WebGL nonblank, panel bounds/no-overflow passed |
| Browser diagnostics | zero console/page/request errors on the passing same-origin run |
| Artifact | existing deterministic `liblib-canvas-batch59-2026-08-27/runtime-audit.json`; no content drift |
| Worktree after run | clean |

This result is a current smoke, not a current full Director regression.

Batch 68 owner/session gate:

| Field | Result |
|---|---|
| Date | 2026-08-27 |
| Implementation checkpoint | `7aafbc9` |
| Pure corpus | 3 owner keys/projects；create/focus/restore/stale/tombstone；deep sidecar/document isolation；zero partial |
| Browser corpus | A -> B -> A、same owner、close/reopen、cross canvas、duplicate reset、active delete tombstone |
| Runtime reset | playback、playhead、path draft、view/transform/thirds/panel/phone state do not bleed |
| Graph boundary | session lifecycle adds zero ordinary graph/history mutation |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 68 `runtime-audit.json` only；zero screenshots |

This result closes the synchronous owner/session slice, not the remaining
authored/runtime、async、history/delete or persistence slices.

Batch 69 authored/runtime gate:

| Field | Result |
|---|---|
| Date | 2026-08-27 |
| Implementation checkpoint | `985e33a` |
| Pure corpus | authored state discoverability、snapshot source、projection writer source and phone runtime-only assertions |
| Browser corpus | repeated seek/playback、keyframe selection、speed curve、motion path、camera preset、object/camera/pose authoring、close/reopen、A/B owner and graph isolation |
| Runtime boundary | authored fingerprint unchanged during sampling；reopen restores authored baseline and time-zero runtime |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 69 `runtime-audit.json` only；zero screenshots |

This result closes the authored/runtime projection slice, not Director
command/history、reference-aware delete、async destination、durable persistence
or source-exact UI.

Batch 70 command/history gate:

| Field | Result |
|---|---|
| Date | 2026-08-27 |
| Implementation checkpoint | Batch 70 closeout commit |
| Pure corpus | typed command/history kernel、no-op/invalid/missing-target reason source assertions |
| Browser corpus | semantic one-entry mutation、same-value/no-op、invalid value、missing target、undo/redo、future truncation、repeated gesture、A/B owner isolation、close/reopen generation continuity、ordinary graph isolation |
| Runtime boundary | history is project-local；`generation` remains session freshness but does not invalidate same-project history after reopen |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 70 `runtime-audit.json` only；zero screenshots |

This result closes the synchronous Director command/history/gesture slice, not
reference-aware delete、async capture/export destination freshness、durable
persistence、real resources or source-exact UI.

Batch 71 pointer-lifecycle gate:

| Field | Result |
|---|---|
| Date | 2026-08-27 |
| Implementation checkpoint | `3a511a9` |
| Pure corpus | gesture helper、Inspector、R3F path controls and pencil/pen commit/cancel wiring |
| Browser corpus | numeric、pose、camera、path anchor/transform、pencil/pen completion/cancel/pointercancel and ordinary graph/history isolation |
| Runtime boundary | continuous input is coalesced to at most one project history entry; cancel and interruption restore the baseline and clear active gesture |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 71 `runtime-audit.json` only；zero screenshots |

This result closes the focused Director pointer lifecycle slice, not
reference-aware delete、async capture/export destination freshness、durable
persistence、real resources or source-exact UI.

Batch 72 reference-delete gate:

| Field | Result |
|---|---|
| Date | 2026-08-27 |
| Implementation checkpoint | `faf9c2d` |
| Pure corpus | object/group/camera/track/path/capture/resource closure、camera fallback、last-camera rejection、resource block/cascade、input immutability |
| Browser corpus | Delete/Backspace、exact delete/undo/redo、reference repair、capture provenance、ordinary graph preservation、local resource storage cleanup |
| Runtime boundary | accepted delete is one project history entry；reject/noop is zero mutation；selection/timeline/draft/phone/preset/capture runtime is reconciled |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 72 `runtime-audit.json` only；zero screenshots；stable semantic ordinary graph node ID |

This result closes the focused Director reference-aware delete slice. It does
not by itself cover async destination freshness、durable persistence、
copy/paste identity remap、real resources or source-exact UI；owner reachability
is covered separately by Batch 76.

Batch 73 async-authority gate:

| Field | Result |
|---|---|
| Date | 2026-08-27 |
| Implementation checkpoint | `ec81801` |
| Pure corpus | current progress/terminal、owner/session/generation stale、source fingerprint drift、retry supersession、duplicate terminal、terminal conflict、invalid envelope、resource transfer/release exactly once |
| Browser corpus | capture archive completion without ordinary graph mutation；animation export one node + one edge；authority snapshot；zero diagnostics |
| Runtime boundary | capture/export/phone completion uses captured owner and source/request identity；stale/invalid/duplicate completion is zero mutation；export object URL transfers or releases exactly once |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 73 `runtime-audit.json` only；zero screenshots |

This result closes the focused Director async-authority slice, not ordinary
canvas async ingress、durable persistence、inactive-owner tombstone/copy-paste
remap、real provider/resource loading or source-exact UI.

Batch 74 persistence gate:

| Field | Result |
|---|---|
| Date | 2026-08-27 |
| Implementation checkpoint | `d68285b` |
| Pure corpus | missing、strict envelope round-trip、capture byte exclusion、stale save completion、corrupt/future/owner/project rejection、write failure and unavailable storage |
| Browser corpus | authored edit -> reload restore、new session generation、A/B owner key isolation、runtime/UI exclusion、corrupt payload preservation、simulated quota/session-only continuity、ordinary graph isolation |
| Runtime boundary | only canonical V1 document is stored；selection/playhead/panel/phone runtime、capture bytes、Blob/File/Object URL and Three.js refs are excluded；invalid load never replaces raw payload |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 74 `runtime-audit.json` only；zero screenshots |

This result closes the clone-owned Director browser-local persistence slice, not
ordinary canvas graph persistence、remote/cloud storage、durable history、real
resource materialization、whole-project duplicate or source-exact LibTV
persistence；owner reachability is covered separately by Batch 76.

Batch 75 clipboard-remap gate:

| Field | Result |
|---|---|
| Date | 2026-08-27 focused run and serial regression |
| Implementation checkpoint | `27c6127` |
| Pure corpus | 12 scenarios covering object/group/track/path/keyframe/anchor closure/remap、internal/external camera refs、resource alias/conflict、stale/empty/allocation failure and runtime/capture exclusion |
| Browser corpus | guarded `Control+C/V`、one paste one history、selection、exact undo/redo、offset `0.6/1.2/1.8`、A-B-A isolation、reload non-persistence and ordinary graph isolation |
| Runtime boundary | clipboard is project-scoped and memory-only；accepted paste commits canonical document once；cross-project/resource conflict/gesture conflict is zero mutation |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 75 `runtime-audit.json` only；zero screenshots |

This result closes the clone-owned same-project Director clipboard identity-remap
slice, not system clipboard MIME、cross-project transfer、whole-project duplicate、
resource-byte transfer、ordinary canvas clipboard or source-exact LibTV behavior.

Batch 76 owner-reachability gate:

| Field | Result |
|---|---|
| Date | 2026-08-27 focused run and serial regression |
| Implementation checkpoint | `10b9251` |
| Pure corpus | 9 scenarios covering all-canvas collection、inactive source/canvas delete、active invalidation、invalid/duplicate normalization、deterministic ordering、idempotency、tombstoned reopen reject and delayed async stale |
| Browser corpus | active A、inactive B、cross-canvas C；inactive source delete、inactive canvas delete、active source cleanup、rename/switch/unrelated isolation、repeated reconcile、graph undo and retained persistence |
| Runtime boundary | active shell closes before R3F/store projection cleanup；registry/session tombstone invalidates async synchronously；inactive owner does not disturb foreground；ordinary delete remains one graph history |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 76 `runtime-audit.json` only；zero screenshots |

This result closes clone-owned memory owner reachability reconciliation, not
durable tombstone storage、resource cleanup、graph-undo project restore、
whole-project duplicate or source-exact LibTV deletion/recovery behavior.

Batch 78 pointer-cancellation gate:

| Field | Result |
|---|---|
| Date | 2026-08-28 |
| Implementation checkpoint | current Batch 78 closeout commit |
| Browser corpus | Curve commit/cancel/pointercancel/blur/hidden/begin-rejected；Phone Vcam pointercancel/blur/close/reuse；Timeline scrub pointercancel/hidden/reuse/stale-move prevention |
| Runtime boundary | Curve cancel restores baseline and leaves zero history；Phone pose remains runtime-only；Timeline cancel removes stale listeners and leaves Director/graph history untouched |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 78 `runtime-audit.json` and `current-gate-regression.json`；zero screenshots |

This result closes the clone-owned pointer cancellation slice adjacent to Batch 71
and Batch 77. It does not prove source-exact LibTV Director cancellation behavior,
real phone sensors, touchpad hardware or source/provider parity.

Batch 82 local-resource materialization gate:

| Field | Result |
|---|---|
| Date | 2026-08-29 |
| Implementation checkpoint | `8c959de` |
| Pure corpus | typed descriptor/provenance、idle/loading/ready/failed/canceled/released transitions、stale request、retry、lease retain/release |
| Browser corpus | valid local OBJ materialization、parse failure with proxy retention、new-attempt retry、unsupported extension zero mutation、cancel/release、model-library status feedback |
| Runtime boundary | local materialization is session-only；portable project JSON excludes File/Blob/data URL/Object3D/capture bytes；failure never fabricates ready |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 82 `runtime-audit.json` only；zero screenshots |

Batch 83 command-feedback gate:

| Field | Result |
|---|---|
| Date | 2026-08-29 |
| Implementation checkpoint | `6c1d4c1` |
| Pure corpus | committed hidden、rejected/stale/conflict reason mapping、meaningful no-op mapping、bounded unknown fallback |
| Browser corpus | rejected visible、committed generic feedback hidden、no-op visible with zero history delta、ARIA status semantics、mobile fixed-header geometry |
| Runtime boundary | feedback is presentation-only；does not enter Director document/history；ordinary LibTV and FrameOS feedback remain separate |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 83 `runtime-audit.json` only；zero screenshots |

This result closes the clone-owned command-feedback projection slice. It does not
prove LibTV source feedback taxonomy、exact copy/color/placement、ordinary canvas
unified feedback or source-exact LibTV behavior.

Batch 84 lock/editability gate:

| Field | Result |
|---|---|
| Date | 2026-08-29 |
| Implementation checkpoint | current Batch 84 closeout commit |
| Pure corpus | object-tree lock contract、locked target guard、Inspector/Viewport/Timeline/Curve source coverage |
| Browser corpus | object-tree lock/unlock、Inspector disabled controls、direct transform rejection、zero-history rejection、visibility toggle、unlock recovery and mobile discoverability |
| Runtime boundary | locked objects remain selectable, hideable/showable and deletable；property/transform/camera/pose/group/path/keyframe/curve editing is rejected or disabled |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 84 `runtime-audit.json` only；zero screenshots |

This result closes the clone-owned Director lock/editability slice. It does not
prove LibTV source Director lock UI、exact copy/color/placement、keyboard policy
or source-exact Director behavior.

Batch 85 selection/CRUD discoverability gate:

| Field | Result |
|---|---|
| Date | 2026-08-29 |
| Implementation checkpoint | current Batch 85 closeout commit |
| Pure corpus | selection action bar selectors、selection count projection、copy/delete/clear command wiring and source boundary |
| Browser corpus | single selection、clear zero-history、project clipboard copy、Shift multi-selection、batch delete、mobile tree discovery |
| Runtime boundary | clear is UI-only；copy remains project-scoped；delete remains reference-aware；role grouping remains character-only |
| Diagnostics | zero console/page/request errors |
| Artifact | Batch 85 `runtime-audit.json` only；zero screenshots |

This result closes the clone-owned Director selection/CRUD discoverability slice. It
does not prove LibTV source Director selection bar、exact labels、keyboard policy
or source-exact behavior.

### 4.3 Current-gate serial regression

On 2026-08-29, using the single `localhost:4317` Next dev server, the
following current gates were run serially and all passed:

```text
Batch 59, Batch 67, Batch 68, Batch 69, Batch 70, Batch 71, Batch 72,
Batch 73, Batch 74, Batch 75, Batch 76, Batch 77, Batch 78, Batch 79, Batch 80,
Batch 81, Batch 82, Batch 83, Batch 84, Batch 85
```

The run included the Batch 68 owner-switch/cross-canvas/duplicate/delete sequence
that had previously exposed five R3F `null.addEventListener` pageerrors. After the
Batch 78 event-source fallback fix, Batch 68 and the full current-gate sequence
reported zero console/page/request errors. Batch 80 first exposed a stale `.glb`
fixture against the current `.obj/.fbx` model-input boundary; Batch 83 replaced
only that verifier fixture with a minimal valid `.obj`, after which Batch 80,
Batch 81, Batch 82 and Batch 83 passed. Batch 81 additionally verified strict
project file transfer and ordinary graph/history isolation. The final serial
result is recorded in
[`liblib-canvas-batch83-2026-08-29/current-gate-regression.json`](liblib-canvas-batch83-2026-08-29/current-gate-regression.json).
This is a clone reliability result, not LibTV source parity.

## 5. Future Gate Profiles

### 5.1 Routine Director reliability batch

```text
Batch 67 pure codec gate
  + Batch 68 owner/session gate
  + Batch 69 authored/runtime gate
  + Batch 70 command/history gate
  + Batch 71 pointer-lifecycle gate
  + Batch 72 reference-delete gate
  + Batch 73 async-authority gate
  + Batch 74 persistence gate
  + Batch 75 clipboard-remap gate
  + Batch 76 owner-reachability gate
  + Batch 78 pointer-cancellation gate
  + Batch 82 local-resource materialization gate
  + Batch 83 command-feedback gate
  + Batch 84 lock/editability gate
  + Batch 85 selection/CRUD gate
  + Batch 59 current browser smoke
  + focused tests for the changed reliability slice
  + npm run check
```

### 5.2 Targeted merge candidate

Choose only the affected candidates:

```text
resource persistence change -> Batch 48
capture/graph bridge change -> Batch 46
R3F camera/viewport change -> Batch 49
shell/focus/keyboard change -> Batch 50
```

Before promotion to an automated gate, each candidate must:

1. accept an isolated artifact directory or disable historical screenshot writes;
2. own BrowserContext/storage setup and teardown;
3. record runtime and failure diagnostics as structured output;
4. avoid depending on another script's residual store or localStorage state;
5. distinguish current clone checks from source-exact assertions.

### 5.3 Manual full historical audit

The 17 scripts may be run serially for a release audit, but only after:

- recording the expected runtime and MediaRecorder cost;
- snapshotting tracked artifacts;
- using `localhost` with the dev server;
- clearing Director storage between storage-sensitive scripts;
- restoring unchanged historical screenshots/audits before commit;
- recording each failure as product, environment, fixture or historical mismatch.

The full historical audit is not the default merge gate.

## 6. `LIBTV-VR-024` Scope

`LIBTV-VR-024` is the Director project/session/command authority verifier family.
Batch 67 supplies the pure codec slice；Batch 68 supplies the owner/session
runtime slice；Batch 69 supplies the authored/runtime projection slice；Batch 70
supplies the command/history slice；Batch 71 supplies the pointer-lifecycle
slice；Batch 72 supplies the reference-delete slice；Batch 73 supplies the
async-authority slice；Batch 74 supplies the browser-local persistence slice；
Batch 75 supplies the clipboard identity-remap slice；Batch 76 supplies the
owner-reachability slice；Batch 78 supplies the pointer-cancellation slice；
Batch 79 supplies the whole-project duplicate slice；
Batch 80 supplies the durable tombstone/storage/resource cleanup slice；
Batch 81 supplies the strict project import/export slice；
Batch 82 supplies the finite local resource materialization slice；
Batch 83 supplies the typed command feedback projection slice；
Batch 84 supplies the locked-target editability slice；
Batch 85 supplies the selection/CRUD discoverability slice；
Batch 59 supplies the current WebGL/browser smoke seed.

Required future scenarios:

| Layer | Minimum checks |
|---|---|
| strict document codec | **implemented in Batch 67**：valid V1 round-trip; future/malformed/duplicate-ID/invalid-reference rejection; zero partial mutation |
| owner registry | **focused runtime in Batch 68/76**：open A、switch B、reopen A、cross canvas、duplicate reset、active delete tombstone、all-canvas reachability、inactive source/canvas tombstone、generation freshness and idempotency |
| authored/runtime split | **implemented in Batch 69**：seek/playback/path sampling does not mutate portable authored snapshot；authoring writes authored layer and restores |
| command/history | **implemented in Batch 70/71**：committed/noop/rejected/stale; one gesture one entry; undo/redo; future truncation; reopen continuity; Inspector/R3F pointer lifecycle |
| delete closure | **focused runtime in Batch 72**：object/group/camera/track/path/resource references repaired or blocked atomically；capture provenance、selection/runtime cleanup and exact delete/undo/redo are covered |
| async bridge | **focused runtime in Batch 73**：capture/export/phone completion carries operation/attempt/result identity；owner/session/generation and source/request freshness are checked；stale/invalid/duplicate results have zero-mutation disposition；export resource transfer/release is exactly once |
| durable project persistence | **focused runtime in Batch 74**：versioned owner-scoped envelope、strict V1 restore、project/generation/fingerprint guards、stale save ignore、corrupt/future/mismatch zero-replacement、runtime/UI/resource-byte exclusion and session-only write failure |
| clipboard identity remap | **focused runtime in Batch 75**：project-scoped typed packet、group/object/track/path closure、all project-local ID remap、internal/external camera policy、stable resource alias、deterministic offset、one-entry paste、reload/system boundary |
| owner reachability reconciliation | **focused runtime in Batch 76**：all-canvas live owner authority、inactive/active invalidation、two-phase shell/runtime cleanup、repeated idempotency、tombstoned reopen rejection、stale async、graph undo and retained persistence boundary |
| pointer cancellation and stale-input cleanup | **focused runtime in Batch 78**：Curve begin-result ownership、pointerup commit、pointercancel/blur/hidden/unmount cancel、Phone Vcam capture release/reuse、Timeline scrub stale-pointer prevention |
| whole-project duplicate | **focused runtime in Batch 79**：graph/parent/edge 与 Director project/entity two-pass remap、multi-owner isolation、fresh-document policy、stable resource descriptor、non-portable reject、clean target authority and source/target persistence isolation |
| durable tombstone and cleanup | **focused runtime in Batch 80**：strict tombstone envelope、save resurrection guard、stale/malformed/write-failure boundary、active/inactive owner cleanup、capture sidecar clear、shared/unshared local resource reachability、reload reopen rejection and graph/Director history isolation |
| strict project import/export | **focused runtime in Batch 81**：strict V1 JSON export/import、owner/project rebind、internal reference preservation、capture/runtime/UI exclusion、one-entry history、undo/redo、same-document no-op、invalid zero-partial、download/file-input round trip and ordinary graph/history isolation |
| finite local resource materialization | **focused runtime in Batch 82**：typed descriptor/provenance、attempt freshness、retry/cancel/release、valid local OBJ/FBX loader path、parse-failure proxy retention、unsupported-extension zero mutation and UI status feedback |
| command outcome feedback projection | **focused runtime in Batch 83**：typed disposition/reason mapping、visible Director primary surface、ARIA status semantics、committed-success suppression、meaningful no-op visibility、mobile geometry and zero-history feedback boundary |
| locked Director editability | **focused runtime in Batch 84**：object-tree lock/visibility controls、locked-target Inspector/Viewport/Timeline/Curve protection、typed rejection、zero document/history mutation and unlock recovery |
| Director selection/CRUD discoverability | **focused runtime in Batch 85**：selection action bar、single/multi-selection count、project clipboard copy、reference-aware batch delete、clear zero-history and mobile discovery |
| route isolation | ordinary graph history and Director project history remain independent |

Until these scenarios exist, `LIBTV-VR-024` status is:

```text
DESIGN_SPEC_COMPLETE
PROJECT_CODEC_FOCUSED_PASS
OWNER_SESSION_FOCUSED_PASS
CURRENT_BROWSER_SEED_PASS
AUTHORED_RUNTIME_FOCUSED_PASS
HISTORY_FOCUSED_PASS
POINTER_LIFECYCLE_FOCUSED_PASS
REFERENCE_DELETE_FOCUSED_PASS
ASYNC_AUTHORITY_FOCUSED_PASS
PERSISTENCE_FOCUSED_PASS
CLIPBOARD_REMAP_FOCUSED_PASS
OWNER_REACHABILITY_FOCUSED_PASS
POINTER_CANCELLATION_FOCUSED_PASS
WHOLE_PROJECT_DUPLICATE_FOCUSED_PASS
DURABLE_TOMBSTONE_FOCUSED_PASS
IMPORT_EXPORT_FOCUSED_PASS
LOCAL_RESOURCE_MATERIALIZATION_FOCUSED_PASS
COMMAND_FEEDBACK_FOCUSED_PASS
SOURCE_PARITY_UNKNOWN_OR_PARTIAL
```

## 7. Maintenance Rules

- A historical script pass never upgrades source parity.
- A current gate must record date, HEAD, server host/port, artifact delta and
  worktree state.
- Do not rewrite historical screenshot files merely to refresh timestamps.
- New Director verifiers join this manifest before joining any shell loop.
- When a merge candidate gains isolated artifacts and deterministic cleanup,
  promote it in a dedicated batch and update `HARNESS.md`,
  [`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md) and the relevant component
  contracts.
- When a new Director reliability slice lands, add a focused `LIBTV-VR-024`
  test rather than expanding Batch 59 into an all-purpose script. Batch 73 is
  the current async-authority example；ordinary canvas async remains a separate
  `LIBTV-VR-015` implementation.
