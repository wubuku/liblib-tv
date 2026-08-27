# LibTV Director Current Verifier Manifest

> Status: `CURRENT_MANIFEST_RECORDED` / `PURE_CODEC_GATE_RECORDED_PASS` /
> `OWNER_SESSION_GATE_RECORDED_PASS` /
> `BROWSER_SMOKE_RECORDED_PASS` /
> `AUTHORED_RUNTIME_GATE_RECORDED_PASS` /
> `HISTORY_GATE_RECORDED_PASS` / `POINTER_LIFECYCLE_GATE_RECORDED_PASS` /
> `REFERENCE_DELETE_GATE_RECORDED_PASS` /
> `FULL_SUITE_NOT_CURRENTLY_RUN`.
>
> Audit date: 2026-08-27.
>
> Scope: `scripts/verify-liblib-batch35.py` through Batch 50, Batch 59,
> Batch 67 pure codec verifier, Batch 68 hybrid owner/session verifier,
> Batch 69 authored/runtime verifier, Batch 70 command/history verifier,
> Batch 71 pointer-lifecycle verifier and Batch 72 reference-aware delete verifier.
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
codec verifier, five current hybrid pure/browser reliability verifiers and one
current browser smoke.
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
  session close without claiming authored/runtime、async、history/delete or
  persistence coverage.
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
| Batch 68 | structured owner key、project/session/generation、A/B/cross-canvas isolation、duplicate reset and active-delete close | `CURRENT_GATE` | Pure Node registry corpus + one headless Playwright page；writes one structured runtime audit and no screenshots/storage | Current `LIBTV-VR-024` owner/session gate；does not prove authored/runtime stability、inactive tombstone、async destination、history/delete or persistence |
| Batch 69 | authored/runtime object split、seek/playback/path stability、object/camera/pose authoring restore、close/reopen and owner/graph isolation | `CURRENT_GATE` | Static Node source gate + one headless Playwright page；writes one structured runtime audit and no screenshots/storage | Current `LIBTV-VR-024` authored/runtime gate；does not prove history/delete、async destination、durable persistence or source parity |
| Batch 70 | project-local command result、semantic history、no-op/rejection、gesture coalescing、undo/redo and reopen continuity | `CURRENT_GATE` | Pure Node source gate + one headless Playwright page；writes one structured runtime audit and no screenshots/storage | Current `LIBTV-VR-024` command/history gate；does not prove reference-aware delete、async destination、durable persistence or source parity |
| Batch 71 | Inspector、pose、camera、path and free-draw gesture lifecycle | `CURRENT_GATE` | Pure source gate + one fresh-page Playwright page；writes one structured runtime audit and no screenshots/storage | Current `LIBTV-VR-024` pointer-lifecycle gate；does not prove reference-aware delete、async destination、durable persistence or source parity |
| Batch 72 | reference-aware delete planner、closure repair、last-camera/resource policy and delete/undo/redo | `CURRENT_GATE` | Pure planner corpus + five fresh-page Playwright scenarios；writes one structured runtime audit and no screenshots/storage | Current `LIBTV-VR-024` reference-delete gate；does not prove async destination、durable persistence、copy/paste or source parity |

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

Use a same-origin host name with the Next dev server:

```bash
npm run dev -- --port 3001
LIBLIB_BASE_URL=http://localhost:3001 \
  python3 scripts/verify-liblib-batch68.py
LIBLIB_BASE_URL=http://localhost:3001 \
  python3 scripts/verify-liblib-batch69.py
LIBLIB_BASE_URL=http://localhost:3001 \
  python3 scripts/verify-liblib-batch59.py
LIBLIB_BASE_URL=http://localhost:3001 \
  python3 scripts/verify-liblib-batch70.py
LIBLIB_BASE_URL=http://localhost:3001 \
  python3 scripts/verify-liblib-batch71.py
LIBLIB_BASE_URL=http://localhost:3001 \
  python3 scripts/verify-liblib-batch72.py
```

Do not substitute `127.0.0.1` unless `allowedDevOrigins` explicitly permits it.
On 2026-08-27, Next 16.2.1 blocked the dev resource request from
`127.0.0.1`; the page returned HTTP 200 and the Director entry was visible, but
client hydration did not make the click effective. The same clean server passed
with `localhost:3001`.

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
| Server | fresh Next dev server, port 3001 |
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
| Browser corpus | A -> B -> A、same owner、close/reopen、cross canvas、duplicate reset、active delete close |
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

This result closes the focused Director reference-aware delete slice, not
inactive-owner reconciliation、async capture/export destination freshness、
durable persistence、copy/paste identity remap、real resources or source-exact UI.

## 5. Future Gate Profiles

### 5.1 Routine Director reliability batch

```text
Batch 67 pure codec gate
  + Batch 68 owner/session gate
  + Batch 69 authored/runtime gate
  + Batch 70 command/history gate
  + Batch 71 pointer-lifecycle gate
  + Batch 72 reference-delete gate
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
slice；Batch 72 supplies the reference-delete slice；Batch 59 supplies the
current WebGL/browser smoke seed.

Required future scenarios:

| Layer | Minimum checks |
|---|---|
| strict document codec | **implemented in Batch 67**：valid V1 round-trip; future/malformed/duplicate-ID/invalid-reference rejection; zero partial mutation |
| owner registry | **focused runtime in Batch 68**：open A、switch B、reopen A、cross canvas、duplicate reset、active delete close、generation freshness |
| authored/runtime split | **implemented in Batch 69**：seek/playback/path sampling does not mutate portable authored snapshot；authoring writes authored layer and restores |
| command/history | **implemented in Batch 70/71**：committed/noop/rejected/stale; one gesture one entry; undo/redo; future truncation; reopen continuity; Inspector/R3F pointer lifecycle |
| delete closure | **focused runtime in Batch 72**：object/group/camera/track/path/resource references repaired or blocked atomically；capture provenance、selection/runtime cleanup and exact delete/undo/redo are covered |
| async bridge | capture/export commits only to captured live owner/generation |
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
ASYNC_PERSISTENCE_RUNTIME_MISSING
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
- When project/session/command runtime lands, add focused `LIBTV-VR-024` tests
  rather than expanding Batch 59 into an all-purpose script.
