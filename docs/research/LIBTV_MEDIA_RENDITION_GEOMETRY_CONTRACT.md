# LibTV Media Rendition, Aspect And Node Geometry Contract

> Scope: ordinary LibTV media/output identity, intrinsic metadata, generation request dimensions, semantic node frames, per-surface rendition, visible-to-intrinsic transforms, React Flow measurement freshness, output switching, editor handoff, history and verifier design.
>
> Status: `STATIC_AUDIT_COMPLETE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_FRAGMENTED` / `SOURCE_PARITY_PARTIAL`.
>
> Clone baseline: `c2278f8`; Open Canvas baseline: `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> Authorization boundary: research/design only. This contract does not authorize changes to `src/`, tests, fixtures, FrameOS, Director runtime, either submodule or source websites.

## 1. Why This Contract Exists

The ordinary clone currently uses the word “dimension” for several unrelated authorities:

```text
decoded source media dimensions
  != thumbnail dimensions
  != selected output dimensions
  != generation request aspect/resolution
  != graph node frame
  != React Flow measured rect
  != detail/editor visible media rect
  != exported output dimensions
```

The initial LibTV fixture keeps these values close enough that `object-cover` appears harmless. Generic add, derived image, Director capture and mark-editor paths prove the coincidence is not stable. The resulting bugs are visible and semantic:

- a square media descriptor can be center-cropped into a landscape node;
- a portrait Director capture can lose most of its composition;
- the detail view can reveal a different composition from the node;
- a mark drawn over a cover-cropped poster can target the wrong full-media coordinates;
- a legitimate frame change can leave selected-node overlays anchored to stale measurement;
- a generation request ratio can be mistaken for actual output dimensions.

The contract target is:

```text
stable media/output identity
  + typed intrinsic metadata with provenance
  + declared node-frame policy
  + declared surface-rendition profile
  + deterministic visible/intrinsic transform
  + frame/remeasurement freshness
  + one output/frame semantic transaction
  + exact overlay/editor/history reconciliation
```

## 2. Authority Composition

This contract owns media rendition and geometry authority only.

| Adjacent authority | Remains authoritative for |
|---|---|
| [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md) | file/asset intent, validation, materialization, locator lease, reachability and release |
| [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md) | foreground session, baseline/draft/local history, commit/cancel and async handoff |
| [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md) | host/client/flow/node/media coordinate-domain conversion and placement owner |
| [`components/LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md) | source-exact selected image toolbar/panel center/gap/zoom/natural-clipping formulas |
| [`components/LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md) | node field identity/reference/runtime roles and portability |
| [`components/LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md) | portable graph schema, strict load and runtime field exclusion |
| [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md) | semantic graph/history commands and compatibility cases |
| [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md) | framework measurement/replace/dimension change transport versus semantic commands |
| [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) | route/canvas/generation owner and switch/delete invalidation |
| [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](open-canvas-2026-08-26/LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md) | source model/mode ratio/resolution option projection |
| [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md) | typed outcome/reason and feedback owner |

The dated facts and issue register remain in [`LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md`](LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md).

## 3. Authority Model

### 3.1 `MEDIA_INTRINSIC`

The decoded full-media dimensions of one stable media identity.

```text
IntrinsicMetadata {
  width
  height
  orientation
  durationSec?        // video/audio only
  provenance
  status
  observedAt?
}
```

`width/height` are finite positive integers. Orientation metadata is either already applied to the decoded dimensions or explicitly declared; consumers may not guess whether EXIF/container rotation has been applied.

### 3.2 `THUMBNAIL_INTRINSIC`

Dimensions decoded from a thumbnail locator. They describe only that thumbnail instance. They cannot silently overwrite full-media intrinsic metadata.

Thumbnail/full-media relationships are represented by shared media identity plus different rendition locators, not by pretending both byte resources have one pixel size.

### 3.3 `MEDIA_OUTPUT`

One candidate/version identity:

```text
MediaOutputDescriptor {
  outputId
  mediaId
  fullLocator
  thumbnailLocator?
  intrinsic
  sourceKind
  createdByOperationId?
}
```

The conceptual descriptor composes with the resource-lifecycle contract. It does not prescribe concrete TypeScript names and does not require a backend.

### 3.4 `GENERATION_REQUEST`

Authoring parameters such as:

```text
aspectRatio = "16:9"
resolution = "1K"
count = 1
```

They describe requested provider behavior. They do not prove actual output dimensions, selected output dimensions or DOM frame geometry.

An opaque display string such as `16:9 · 低画质 · 1K · 1张` is a presentation projection, never the canonical request or geometry model.

### 3.5 `NODE_FRAME`

The semantic graph rectangle in flow units:

```text
NodeFrame {
  width
  height
  frameRevision
  policy
  policyInputVersion
}
```

`width/height` are finite and positive. A frame may be portable graph state if it is declared semantic. It is not a media pixel size.

### 3.6 `NODE_MEASURED`

The current React Flow/runtime observation:

```text
MeasuredNodeFrame {
  width
  height
  frameRevision
  measurementEpoch
  measuredAt
}
```

It may feed selection, handles, centering and overlays. It is runtime-only and produces no graph history by itself.

### 3.7 `SURFACE_RENDITION`

The visual policy for a specific role:

```text
RenditionProfile {
  role
  fit: COVER | CONTAIN | FILL | NONE | SCALE_DOWN
  positionX
  positionY
  clipping
  background
  coordinateIntent
}
```

`positionX/Y` are normalized alignment values in `[0,1]`; centered media uses `0.5/0.5`. Exact CSS syntax is a projection.

### 3.8 `VISIBLE_MEDIA_RECT`

The current media plane inside one surface after fit/position is applied. It may extend beyond the clipped frame under cover or be smaller than the frame under contain.

### 3.9 `EDITOR_MEDIA_SPACE`

The coordinate plane in which an editor stores marks/crops:

| Intent | Meaning |
|---|---|
| `FULL_INTRINSIC` | coordinates map to full decoded media |
| `VISIBLE_RENDER` | coordinates intentionally map only to the current rendered/cropped frame |
| `EXPORT_FRAME` | coordinates map to a declared output canvas |

The intent is mandatory. A plain normalized `[0,1]` pair is insufficient.

### 3.10 `EXPORT_OUTPUT`

Actual encoded dimensions and duration. Export metadata can create a new output descriptor. It does not retroactively resize the source node unless an accepted semantic command says so.

## 4. Metadata Provenance And State

### 4.1 Provenance

| Provenance | Meaning | Trust boundary |
|---|---|---|
| `DECODED_FULL_MEDIA` | browser decoded full locator/blob | strongest local pixel observation |
| `PROVIDER_RESULT` | provider returned actual dimensions | requires provider contract |
| `SOURCE_DOCUMENT` | trusted graph/source record declares dimensions | validate on load; may be stale |
| `DECODED_THUMBNAIL` | browser decoded thumbnail | thumbnail only |
| `REQUEST_DERIVED` | inferred from requested aspect/resolution | estimate only |
| `FIXTURE_DECLARED` | deterministic local fixture metadata | verifier authority only |
| `UNKNOWN` | not established | cannot drive destructive or editor transform |

### 4.2 Metadata state

```text
UNKNOWN
  -> PROBING
  -> READY
  -> INVALID
  -> FAILED
```

- `UNKNOWN`: no validated dimensions;
- `PROBING`: an owned metadata operation is active;
- `READY`: finite positive dimensions with provenance;
- `INVALID`: supplied/decoded metadata violates schema;
- `FAILED`: probe could not obtain metadata.

`INVALID` and `FAILED` are distinct from media network/decode rendering errors when the dimensions were already known.

### 4.3 Last-known-good rule

When replacing or re-probing existing media, retain the last-known-good descriptor/frame/rendition until a fresh descriptor is accepted. Failure cannot replace valid dimensions with zero, `NaN`, request-derived guesses or thumbnail dimensions.

### 4.4 Full versus thumbnail freshness

Full and thumbnail metadata have independent locator/version identities. A newly decoded thumbnail cannot mark full media ready. A full media replacement invalidates old thumbnail/full relationship unless the incoming descriptor explicitly preserves it.

## 5. Node Frame Policy

Every media-bearing node declares one policy.

### 5.1 `SOURCE_MEDIA_SHAPED`

The frame preserves selected media aspect within product/source constraints.

Current read-only evidence proves landscape samples:

```text
1808x1024 -> 618x350
1152x576  -> 700x350
1280x720  -> 622x350
```

It does not prove portrait/square/minimum-width behavior. The contract therefore distinguishes:

- `SOURCE_BACKED_LANDSCAPE_SAMPLE`: exact recorded fixture values;
- `PROTOTYPE_ASPECT_PRESERVING_FALLBACK`: preserve aspect inside explicit bounds, marked clone-only;
- `SOURCE_UNKNOWN_ORIENTATION`: source decision required before claiming parity.

### 5.2 `REQUEST_ASPECT_SHAPED`

The frame follows generation request aspect. This matches fixed Open Canvas card behavior, not current LibTV source proof.

It is allowed only for a surface/node profile explicitly declared request-shaped. It cannot silently replace source-media-shaped behavior.

### 5.3 `TYPE_FIXED`

The frame is fixed by node/surface type. Typical uses are compact thumbnails, filmstrips and process cards. A nonmatching media ratio requires an explicit cover/contain policy.

### 5.4 `EXPLICIT_SEMANTIC_FRAME`

The frame is changed by a validated product command. No current ordinary LibTV source evidence authorizes a generic node-resize UI. The policy exists for future source evidence and already-explicit clone-owned outputs such as Director animation return.

### 5.5 Frame derivation result

Frame derivation never returns a naked width/height pair:

```text
FrameDecision =
  KEEP_EXISTING
  | APPLY_FRAME { frame, reason, sourceVersion }
  | WAIT_FOR_METADATA
  | REJECT { reason }
  | SOURCE_DECISION_REQUIRED { questionId }
```

### 5.6 Frame bounds

Frame bounds are profile data. Algorithms must:

- validate all inputs as finite positive values;
- preserve aspect under aspect-shaped policies;
- use one deterministic rounding rule;
- reject zero-area results;
- preserve the declared anchor if frame size changes;
- never derive graph dimensions directly from thumbnail pixels.

The observed `700x350` landscape envelope is evidence for current samples, not a universal maximum/minimum contract.

## 6. Rendition Profiles

### 6.1 Required role table

| Role | Default method | Current authority | Source status |
|---|---|---|---|
| `CANVAS_PRIMARY_IMAGE` | media-shaped frame + centered cover for recorded landscape fixtures | current source/clone fixture | partial |
| `CANVAS_PRIMARY_VIDEO_POSTER` | stable node frame; fit source-unknown | clone cover only | gated |
| `CANVAS_PRIMARY_VIDEO_MEDIA` | stable node frame; fit source-unknown | clone Director contain island | gated |
| `OUTPUT_CANDIDATE` | fixed comparable cells + cover | Open Canvas method | adapt |
| `REFERENCE_THUMBNAIL` | fixed compact cells + cover/object-position profile | clone/source surface-specific | partial |
| `DETAIL_INSPECTOR` | contain full media within bounded viewport | Open Canvas + clone method | image partial |
| `EDITOR_FULL_MEDIA` | contain or explicit transform exposing full media | correctness floor | source visual gated |
| `EDITOR_VISIBLE_RENDER` | exact node rendition + recorded cover transform | only when operation targets visible crop | product decision |
| `FILMSTRIP_TEMPORAL` | fixed cells + cover | clone/source method | surface-specific |
| `STATUS_PLACEHOLDER` | preserve stable frame | Open Canvas/clone method | adopt |
| `EXPORT_PREVIEW` | reflect actual output aspect; contain unless source says otherwise | clone Director method | route-local |

### 6.2 `cover` is nondestructive presentation

`cover` does not mutate media or produce crop metadata. It is a display transform. A destructive crop requires an editor session, explicit crop intent and accepted output/graph handoff.

### 6.3 `contain` is not automatic parity

`contain` protects full-content visibility, but it can introduce letterboxing and change source-like scanning density. Use it for detail/full-media/editor roles unless source evidence defines another policy. Do not replace current source-backed node `cover` with `contain` by global rule.

### 6.4 Object position

Current source image samples use centered `50% 50%`. A focal point, face-aware crop or `object-top` requires profile/source evidence.

If object position becomes user-adjustable, it is semantic rendition state and follows graph/history rules. A profile default is derived and does not consume history.

## 7. Fit Transform

Let intrinsic media size be `(Mw, Mh)` and frame inner size be `(Fw, Fh)`.

### 7.1 Scale

```text
coverScale   = max(Fw / Mw, Fh / Mh)
containScale = min(Fw / Mw, Fh / Mh)
```

For `COVER` or `CONTAIN`:

```text
renderWidth  = Mw * scale
renderHeight = Mh * scale
offsetX      = (Fw - renderWidth)  * positionX
offsetY      = (Fh - renderHeight) * positionY
```

Cover offsets are zero or negative on the cropped axis. Contain offsets are zero or positive on the letterboxed axis.

### 7.2 Visible point to intrinsic point

For a frame-local point `(Vx, Vy)`:

```text
Ix = (Vx - offsetX) / scale
Iy = (Vy - offsetY) / scale
Nx = Ix / Mw
Ny = Iy / Mh
```

The result is clamped only if the editor intent explicitly clamps to full media. Invalid scale/size returns a typed rejection; it never becomes `(0,0)`.

### 7.3 Intrinsic point to visible point

```text
Vx = Ix * scale + offsetX
Vy = Iy * scale + offsetY
```

Round-trip error must remain within the verifier tolerance. DOM/device-pixel rounding is applied only at the rendering boundary.

### 7.4 Borders and content box

Fit calculations use the actual media content box, excluding node border and external labels. The current source sample has a `622x350` bordered frame and a `620x348` image content box. Using outer frame dimensions for editor normalization introduces a systematic border error.

### 7.5 Media orientation

The transform consumes dimensions after orientation resolution. CSS transforms, EXIF orientation and container rotation cannot be applied twice.

### 7.6 Transform identity

An editor baseline conceptually captures:

```text
mediaId + outputId + intrinsicVersion
  + nodeId + frameRevision
  + renditionRevision + contentBox
  + fit + position
```

Any change to these values invalidates or explicitly rebases the transform.

## 8. Output Selection And Mixed Ratios

### 8.1 Selection identity

```text
MediaSelection {
  outputId
  selectedIndex
  selectionRevision
}
```

Index is a presentation/order locator. `outputId` is stable identity. Restore/load reconciles index from identity when possible; it does not attach a different output merely because the old index remains in range.

### 8.2 Output collection normalization

Normalization must:

1. validate each output identity and full locator;
2. reject duplicate output IDs;
3. reconcile duplicate locators according to resource identity policy;
4. validate per-output metadata independently;
5. preserve original order unless a named command changes it;
6. resolve selected output by identity, then safe fallback;
7. never carry dimensions/thumbnail from the previously selected output.

### 8.3 Mixed-ratio switch policy

Every primary surface declares exactly one:

| Policy | Frame behavior | Rendition behavior |
|---|---|---|
| `REFLOW_FRAME_TO_OUTPUT` | derive a new semantic frame from selected output | usually source-shaped cover/contain |
| `PRESERVE_FRAME_COVER` | keep semantic frame | visible crop changes explicitly |
| `PRESERVE_FRAME_CONTAIN` | keep semantic frame | full media visible with letterbox |
| `REJECT_MIXED_RATIO` | keep current selection/frame | typed unavailable result |
| `SOURCE_DECISION_REQUIRED` | no product change | evidence gate |

Current Open Canvas implements a structural `PRESERVE_FRAME_COVER` through request-aspect cards. Current LibTV source mixed-ratio switching is unknown. The clone may not claim either as source parity.

### 8.4 Atomic semantic switch

When selection is persisted semantic state:

```text
validate selected output + metadata
  -> decide frame policy
  -> compute rendition/transform
  -> validate overlay/editor consequences
  -> one graph transaction:
       selected output
       primary media projection
       optional frame update
       optional semantic object position
  -> runtime measurement pending
  -> current measurement accepted
  -> overlays/editors reconcile
```

Invalid/no-op/source-unknown/stale selection causes zero graph/history residue.

### 8.5 Edited output

An edited/exported output carries actual dimensions from the export canvas. Appending it without dimensions, or selecting it while preserving an incompatible frame by accident, is a contract violation.

## 9. Measurement Freshness

### 9.1 Revisions

The conceptual owner model includes:

```text
frameRevision
renditionRevision
measurementEpoch
```

- semantic frame changes increment `frameRevision`;
- fit/position/content-box changes increment `renditionRevision` when they affect transforms;
- React Flow/DOM measurement accepted for a frame produces a new `measurementEpoch` tagged with that `frameRevision`.

### 9.2 Measurement state

```text
STABLE
  -> FRAME_COMMIT
  -> MEASUREMENT_PENDING
  -> STABLE

MEASUREMENT_PENDING
  -> INVALIDATED     // owner/canvas/output changed again
```

### 9.3 Stale measurement

A measurement is stale when any of these differ:

- route/canvas/generation;
- node identity;
- frame revision;
- current DOM owner/mount epoch;
- finite positive expected dimensions.

Stale measurement cannot reposition current overlays, commit graph dimensions or rebase an editor transform.

### 9.4 Overlay behavior while pending

The implementation chooses one declared presentation policy:

- keep the last stable surface frozen for the same owner and mark it pending;
- hide the surface until fresh measurement;
- place from a validated predicted frame, then verify against measurement.

It cannot late-read active selection and apply a stale node rect to a new owner.

### 9.5 Passive measurement

Framework `dimensions`/measurement changes that only report current DOM geometry are T0/T1 runtime transport. They:

- create no semantic graph history;
- do not imply user resize;
- do not update media intrinsic dimensions;
- do not rewrite generation request fields;
- may update runtime measurement cache for the current frame revision.

### 9.6 Explicit resize

If future source evidence proves a resize gesture, it requires:

- a named gesture owner;
- start/update/end/cancel/stale lifecycle;
- aspect-lock/min/max policy;
- anchor preservation policy;
- one semantic history entry at end;
- output/rendition/editor transform reconciliation;
- current overlay measurement verification.

No generic resize UI is authorized by this contract.

## 10. Media Load And Status Geometry

### 10.1 Geometry-stable status

`EMPTY`, `PENDING`, `RUNNING`, `ERROR` and `READY` presentations occupy the declared node frame. Status content may change; frame collapse is prohibited unless the product/source contract explicitly changes node type/frame.

### 10.2 Metadata before media render

If trusted full metadata is ready before the media element renders, a source-shaped frame may be planned immediately. If metadata is unknown, retain the declared placeholder frame and enter `WAIT_FOR_METADATA`; do not guess from request text unless the policy is explicitly request-shaped.

### 10.3 Decode failure

Decode failure:

- preserves last-known-good frame/media when replacing;
- shows owner-local error through feedback authority;
- does not write zero dimensions;
- leaves editor/export commands unavailable when no valid full-media transform exists;
- does not clear a valid thumbnail unless its owner also failed.

### 10.4 Thumbnail/full swap

Swapping thumbnail to full media must preserve the semantic frame and rendition transform intent. A small rounding difference in decoded thumbnail ratio cannot cause graph-frame history or overlay jumps.

### 10.5 Poster/full video swap

Poster and full video are separate rendition resources. Their intrinsic ratios must be validated. If they differ, the profile explicitly chooses which one owns the frame and how playback changes fit; incidental React branch behavior is insufficient.

## 11. Editor Integration

### 11.1 Editor open gate

An editor that stores media coordinates opens only with:

- stable route/canvas/generation/node/output owner;
- full media identity;
- valid intrinsic metadata or declared export-frame space;
- stable frame/rendition revision;
- measured content box or deterministic validated equivalent;
- declared coordinate intent.

Otherwise the control is disabled/unavailable or the editor waits in a visible loading state.

### 11.2 Full-media editor

For subject edit, subtitle removal, annotation or crop sent against the full source asset, marks are stored in `FULL_INTRINSIC` space. Pointer events pass through the fit transform before normalization.

Storing normalized coordinates directly from the cover-cropped node rect is prohibited unless the operation explicitly targets `VISIBLE_RENDER`.

### 11.3 Visible-render editor

If a product intentionally edits only the current visible crop, the baseline records the full transform and an export/crop descriptor. The result is not described as editing the untouched full media.

### 11.4 Drift

Output selection, media replacement, frame change, fit/position change, node delete, canvas switch or owner unmount while an editor is dirty follows the editor-session drift policy. It cannot silently rebind existing marks to the new transform.

### 11.5 Commit handoff

An accepted editor commit carries:

```text
media/output baseline identity
  + intrinsic/frame/rendition revisions
  + coordinate intent
  + normalized intrinsic/export-frame payload
```

Async completion still delegates freshness and resource transfer to the async/media contracts.

## 12. History And Graph Semantics

### 12.1 History table

| Event | Semantic graph history |
|---|---:|
| decode full/thumbnail metadata into runtime cache only | 0 |
| React Flow passive measurement | 0 |
| hover/play/pause/detail preview open/close | 0 |
| local editor pointer move/local history | 0 |
| derived profile calculation with no state change | 0 |
| accepted persisted output selection | exactly 1 |
| accepted output selection plus frame reflow | exactly 1 combined |
| accepted explicit semantic frame resize | exactly 1 at gesture end |
| invalid/no-op/stale/source-unknown selection | 0 |
| thumbnail/full resource swap with same media identity | 0 |
| accepted user focal/object-position change | exactly 1 if persisted semantic state |

### 12.2 Media metadata persistence

Whether intrinsic metadata is portable graph state or reconstructible asset metadata is a graph-document decision. Runtime decoded caches and measurement epochs never enter portable snapshots.

If metadata is persisted, load validates it and retains provenance. It does not trust arbitrary strings/numbers through coercion.

### 12.3 Frame and position transaction

When frame size changes, anchor preservation is part of the same semantic transaction. Current source evidence does not prove whether top-left or center is authoritative for explicit reflow. The local fixture must test the chosen policy and label it clone-only until source-confirmed.

### 12.4 Selection and overlay

Output/frame commands preserve node selection unless a source/product command says otherwise. Surface lifecycle waits for fresh measurement but does not clear the selection merely to force remount.

## 13. Field Role Guidance

| Concept | Role | Portable by default |
|---|---|---:|
| `mediaId/outputId` | semantic/reference identity | yes, subject to resource contract |
| full/thumbnail locator | external/reference locator | conditional |
| actual intrinsic dimensions + provenance | semantic asset metadata or reconstructible descriptor | schema decision |
| generation ratio/resolution | semantic authoring value | yes |
| display generation string | presentation projection | no canonical authority |
| node frame width/height | semantic graph geometry when declared | yes |
| React Flow measured width/height | runtime derived | no |
| frame/rendition revision | runtime or semantic version according to schema | contract-specific |
| default fit/object-position | derived presentation policy | no |
| user-adjusted focal/object-position | semantic rendition value | yes if feature exists |
| visible media transform | runtime derived | no |
| editor intrinsic marks | semantic draft/result payload | through editor/command contract |
| export actual dimensions | output metadata | yes with output descriptor |

Current ordinary clone fields named `width/height/resolution/generationSettings` must be classified before migration. Names alone do not determine the role.

## 14. Invariants

### 14.1 Identity and metadata

| ID | Invariant |
|---|---|
| `LIBTV-MRG-I-001` | every rendered primary media resolves one stable media identity |
| `LIBTV-MRG-I-002` | every selected candidate resolves one stable output identity; index alone is insufficient |
| `LIBTV-MRG-I-003` | full and thumbnail locators have independent decoded dimensions |
| `LIBTV-MRG-I-004` | intrinsic width/height are finite positive integers with provenance |
| `LIBTV-MRG-I-005` | request-derived ratio never impersonates actual intrinsic metadata |
| `LIBTV-MRG-I-006` | replacing/re-probing preserves last-known-good until fresh acceptance |
| `LIBTV-MRG-I-007` | metadata failure never commits zero/NaN/Infinity dimensions |
| `LIBTV-MRG-I-008` | selected output never retains dimensions/thumbnail from a different output |

### 14.2 Frame and rendition

| ID | Invariant |
|---|---|
| `LIBTV-MRG-I-009` | every media-bearing node declares one frame policy |
| `LIBTV-MRG-I-010` | every rendered media surface declares one rendition role/profile |
| `LIBTV-MRG-I-011` | semantic node frame and media intrinsic dimensions remain distinct values |
| `LIBTV-MRG-I-012` | aspect-shaped frame derivation preserves ratio under deterministic rounding |
| `LIBTV-MRG-I-013` | thumbnail pixels never directly determine graph frame |
| `LIBTV-MRG-I-014` | cover crop is presentation-only unless an explicit crop command commits output metadata |
| `LIBTV-MRG-I-015` | object-position default is profile-derived; user change is semantic only when feature-authorized |
| `LIBTV-MRG-I-016` | empty/pending/running/error/ready preserve declared frame unless a named command changes it |

### 14.3 Transform and editor

| ID | Invariant |
|---|---|
| `LIBTV-MRG-I-017` | visible/intrinsic transforms use the media content box, excluding borders/external chrome |
| `LIBTV-MRG-I-018` | cover/contain scale and offsets are finite and derived from valid dimensions |
| `LIBTV-MRG-I-019` | visible-to-intrinsic-to-visible round trip stays within verifier tolerance |
| `LIBTV-MRG-I-020` | editor coordinate intent is explicit: full intrinsic, visible render or export frame |
| `LIBTV-MRG-I-021` | full-media editor marks are not normalized directly against an undeclared cover-cropped node rect |
| `LIBTV-MRG-I-022` | editor baseline captures media/output/frame/rendition identity and revision |
| `LIBTV-MRG-I-023` | transform drift cannot silently rebind dirty marks |
| `LIBTV-MRG-I-024` | invalid transform keeps editor action unavailable and produces no graph residue |

### 14.4 Output switching

| ID | Invariant |
|---|---|
| `LIBTV-MRG-I-025` | output collection rejects duplicate output identity and validates metadata per entry |
| `LIBTV-MRG-I-026` | restore resolves selected output by identity before index fallback |
| `LIBTV-MRG-I-027` | mixed-ratio switching declares reflow, cover, contain, reject or source-decision policy |
| `LIBTV-MRG-I-028` | output selection and optional frame change commit atomically |
| `LIBTV-MRG-I-029` | invalid/no-op/stale/source-unknown switch has zero graph/history/overlay residue |
| `LIBTV-MRG-I-030` | edited/exported output retains actual dimensions before it can become selected |

### 14.5 Measurement and overlays

| ID | Invariant |
|---|---|
| `LIBTV-MRG-I-031` | accepted measurement is tagged with current owner and frame revision |
| `LIBTV-MRG-I-032` | stale measurement cannot reposition current overlays or rebase current editor |
| `LIBTV-MRG-I-033` | passive measurement creates zero semantic graph history |
| `LIBTV-MRG-I-034` | passive measurement is never interpreted as user resize intent |
| `LIBTV-MRG-I-035` | legitimate frame change enters measurement-pending before current overlay assertion |
| `LIBTV-MRG-I-036` | selected toolbar/panel use the same current node owner/frame but retain their separate source coordinate formulas |

### 14.6 History, lifecycle and honesty

| ID | Invariant |
|---|---|
| `LIBTV-MRG-I-037` | accepted persisted output/frame/focal command consumes at most one graph history entry |
| `LIBTV-MRG-I-038` | detail preview, playback, thumbnail swap and local editor trial consume zero graph history |
| `LIBTV-MRG-I-039` | canvas switch/delete/unmount invalidates pending metadata/measurement/editor owner |
| `LIBTV-MRG-I-040` | route isolation prevents ordinary rendition state from mutating FrameOS/Director owners |
| `LIBTV-MRG-I-041` | missing provider/backend remains honest; local fixture metadata is not called durable provider output |
| `LIBTV-MRG-I-042` | generic node resize remains unavailable until source/product evidence and a named command exist |

## 15. Graph Invariant Additions

Add the following conceptual invariants to the graph catalog:

| ID | Requirement |
|---|---|
| `LIBTV-GI-101` | media/output identity is distinct from URL/index |
| `LIBTV-GI-102` | intrinsic, request, node-frame, measured and export dimensions are distinct authorities |
| `LIBTV-GI-103` | intrinsic metadata is finite, positive and provenance-tagged |
| `LIBTV-GI-104` | full and thumbnail dimensions cannot overwrite one another |
| `LIBTV-GI-105` | every media node has an explicit frame policy |
| `LIBTV-GI-106` | every media surface has an explicit rendition profile |
| `LIBTV-GI-107` | cover/contain transform uses content box and round-trips |
| `LIBTV-GI-108` | editor coordinate intent and transform baseline are explicit |
| `LIBTV-GI-109` | selected output resolves by stable identity and owns its metadata |
| `LIBTV-GI-110` | mixed-ratio output policy is declared before selection commit |
| `LIBTV-GI-111` | output selection and optional frame change are atomic |
| `LIBTV-GI-112` | frame revision and measurement epoch prevent stale anchor use |
| `LIBTV-GI-113` | passive measurement has zero semantic history and no resize meaning |
| `LIBTV-GI-114` | status/media-resource transitions preserve declared semantic frame |
| `LIBTV-GI-115` | last-known-good media/frame survives failed replacement/probe |
| `LIBTV-GI-116` | route/canvas/generation isolation applies to metadata, measurement and rendition owners |

## 16. Compatibility Cases

| ID | Scenario | Required result |
|---|---|---|
| `LIBTV-GC-127` matching landscape source | valid intrinsic + source-shaped frame | source-backed frame and centered cover; no hidden creative crop beyond rounding |
| `LIBTV-GC-128` default square image | `512x512` media enters ordinary image | explicit square/aspect-preserving frame or declared non-source fallback; no silent `512x288` crop |
| `LIBTV-GC-129` portrait Director capture | `9:16` actual output | aspect-aware frame/full-content rendition; no generic landscape crop |
| `LIBTV-GC-130` same-ratio output switch | selected identity changes | one atomic selection commit; frame may remain; fresh metadata projected |
| `LIBTV-GC-131` mixed-ratio output reflow | declared reflow policy | selection+frame one transaction; measurement pending then overlays reconcile |
| `LIBTV-GC-132` mixed-ratio preserve cover | declared cover policy | frame stable; crop transform updates; full detail remains reachable |
| `LIBTV-GC-133` mixed-ratio preserve contain | declared contain policy | frame stable; letterbox explicit; no hidden crop |
| `LIBTV-GC-134` mixed-ratio source unknown | no source policy | zero mutation; typed source-decision result |
| `LIBTV-GC-135` thumbnail ratio rounding | thumbnail differs slightly from full metadata | no graph-frame/history jump |
| `LIBTV-GC-136` thumbnail/full mismatch | materially different ratios | use full authority for editor/output; thumbnail remains scan rendition only |
| `LIBTV-GC-137` metadata probe failure | new media invalid/fails | preserve last-known-good or stable placeholder; no zero dimensions |
| `LIBTV-GC-138` status transition | pending -> error -> retry -> ready | declared frame remains stable unless accepted frame command occurs |
| `LIBTV-GC-139` cover editor mapping | known crop and full-media intent | pointer maps through crop offsets to intrinsic coordinates |
| `LIBTV-GC-140` editor drift | output/frame changes while dirty | explicit conflict/invalidate/rebase; no silent mark retarget |
| `LIBTV-GC-141` passive measurement | React Flow reports new measured rect for current frame | runtime cache only; zero graph history |
| `LIBTV-GC-142` stale measurement | old frame revision completes after new switch | ignored; current overlay/editor unchanged |
| `LIBTV-GC-143` detail preview | open/close contain inspector | graph/selection/frame/history unchanged; full media visible |
| `LIBTV-GC-144` absent resize product | user searches/uses normal node | no enabled resize affordance or fabricated resize command |
| `LIBTV-GC-145` route isolation | FrameOS/Director media event | no ordinary LibTV rendition/graph/overlay effect |

## 17. Proposed Command Results

```text
MediaRenditionDisposition =
  ACCEPTED
  | NOOP
  | INVALID_METADATA
  | METADATA_PENDING
  | OUTPUT_NOT_FOUND
  | MIXED_RATIO_UNDECIDED
  | STALE_OWNER
  | STALE_MEASUREMENT
  | EDITOR_CONFLICT
  | UNAVAILABLE
```

Command outcomes compose with the existing feedback contract. Localized strings do not become disposition identity.

## 18. `LIBTV-FIX-LOCAL-MEDIA-RENDITION-01`

### 18.1 Purpose

A deterministic, provider-free corpus for visual and pure-model checks. The fixture does not require graph/runtime implementation in this documentation batch.

### 18.2 Media corpus

Use locally generated or committed non-sensitive assets with unmistakable pixel markers:

| Asset | Dimensions | Visual oracle |
|---|---:|---|
| `landscape-16x9` | `1600x900` | labeled corners + center cross |
| `landscape-2x1` | `1600x800` | four color quadrants |
| `odd-landscape` | `1808x1024` | 32px border + axis rulers |
| `square` | `1000x1000` | concentric square + corner IDs |
| `portrait-9x16` | `900x1600` | top/middle/bottom labels |
| `thumbnail-rounded` | `200x112` | derived from 16:9 full media |
| `thumbnail-mismatch` | `200x200` | explicit crop label |
| `video-poster` | `1280x720` | poster marker |
| `video-frame` | `1280x720` | distinct playback marker |

No fixture locator is called uploaded, synced or provider-generated.

### 18.3 Fixture nodes

```text
MRG-A source-shaped matching landscape
MRG-B square generic creation
MRG-C portrait Director-like still output
MRG-D three-output node: 16:9, 1:1, 9:16
MRG-E thumbnail/full mismatch
MRG-F ready video poster/full media pair
MRG-G pending/error/retry placeholder
MRG-H cover-cropped editor target with known intrinsic marker
```

### 18.4 Deterministic owner data

Each fixture declares:

- route/canvas/generation/node/media/output identity;
- full/thumbnail intrinsic metadata and provenance;
- frame/rendition revisions;
- frame policy and rendition profile;
- expected visible media transform;
- expected graph-history cardinality;
- source-backed, clone-decision or research-only classification.

### 18.5 Reset

Reset restores:

- original output order/selection;
- original semantic frames/positions;
- no pending metadata/measurement/editor owner;
- empty graph undo/redo for the fixture canvas;
- closed detail/editor surfaces;
- deterministic viewport and zoom;
- no object URLs, timers or external requests.

## 19. `LIBTV-VR-023`

### 19.1 Pure model checks

- metadata schema/provenance validation;
- frame policy derivation and rounding;
- cover/contain scale, offset and round trip;
- border/content-box exclusion;
- output identity/index normalization;
- mixed-ratio decision table;
- selection+frame transaction planning;
- measurement freshness reducer;
- editor drift and coordinate-intent validation;
- history cardinality and no-op/stale rejection.

### 19.2 Browser checks

For each relevant fixture/profile:

1. read node outer/content/media rects in one frame;
2. read decoded media natural/video dimensions;
3. assert computed `object-fit/object-position` and clipping;
4. use color/corner markers or canvas-pixel checks to prove crop/letterbox;
5. switch output and assert atomic identity/frame state;
6. wait for current `frameRevision` measurement before overlay rect assertion;
7. assert selected toolbar/panel center and source-contract gaps;
8. open detail view and prove full-media visibility;
9. map a known editor point through visible/intrinsic/visible round trip;
10. verify pending/error/retry frame stability;
11. assert graph history count separately from local/editor state;
12. assert zero console/page/request errors.

### 19.3 Viewports

Minimum matrix:

- desktop source-comparable viewport;
- `390x844` mobile natural clipping;
- at least `28%`, source-comparable mid zoom and `100%`;
- left/right/top/bottom edge placement for selected overlays;
- portrait and wide media.

### 19.4 Pixel tolerance

Rect tolerances and pixel tolerances are separate:

- geometry tolerance accounts for browser subpixels/current zoom;
- crop oracle checks unmistakable marker visibility, not screenshot similarity alone;
- transformed point round trip uses normalized epsilon independent of device pixel ratio.

### 19.5 Replacement scope

`LIBTV-VR-023` replaces future ad hoc assertions such as:

- checking only that an `<img>` exists;
- assuming `object-cover` means the correct crop;
- asserting node `width/height` while ignoring media data dimensions;
- opening detail view without checking composition difference;
- checking overlay position before fresh measurement;
- treating a resize cursor/control as proof of semantic resize.

It composes with `VR-002`, `VR-020`, `VR-021`, `VR-022` and source visual checks. It does not replace exact overlay, ingress, editor, graph or model contracts.

## 20. Source Decision Queue

| ID | Question | Safe evidence |
|---|---|---|
| `LIBTV-MRG-DQ-001` | portrait ordinary image frame bounds/min width | disposable ratio-diverse source fixture |
| `LIBTV-MRG-DQ-002` | square ordinary image frame policy | disposable/source-existing square node |
| `LIBTV-MRG-DQ-003` | extreme ratio clamp/max/min behavior | disposable fixture only |
| `LIBTV-MRG-DQ-004` | ready video poster and playback fit | existing ready video or disposable fixture |
| `LIBTV-MRG-DQ-005` | mixed-ratio output/version switch policy | disposable generated-history/output fixture |
| `LIBTV-MRG-DQ-006` | whether node reflows on output switch | same-frame rect trace |
| `LIBTV-MRG-DQ-007` | focal/object-position behavior | computed styles + controlled media |
| `LIBTV-MRG-DQ-008` | image/video detail inspector fit | read-only existing media |
| `LIBTV-MRG-DQ-009` | metadata load/decode failure geometry | disposable network/media fixture |
| `LIBTV-MRG-DQ-010` | whether any ordinary node is user-resizable | read-only modes + disposable gesture if present |
| `LIBTV-MRG-DQ-011` | resize anchor/history semantics | only after DQ-010 confirms affordance |
| `LIBTV-MRG-DQ-012` | full-media versus visible-render mark coordinates | disposable marked media + submitted/result evidence |
| `LIBTV-MRG-DQ-013` | thumbnail/full crop relationship | inspect locators and both surfaces |
| `LIBTV-MRG-DQ-014` | watermark scaling/position across ratios | ratio-diverse existing/disposable media |

These questions become `OC-EQ-009` / `LIBTV-FIX-SOURCE-MEDIA-RENDITION-01`. Shared source remains read-only.

## 21. Implementation Slices If Coding Is Authorized Later

### Slice A: classify dimensions without visual change

- introduce typed conceptual helpers/field classification;
- make initial fixture/generic/derived frame conflicts observable in diagnostics;
- no provider, output history or resize UI.

### Slice B: deterministic frame/rendition policy

- preserve current source-backed landscape fixtures;
- make generic square and portrait outputs aspect-aware;
- declare node/detail/thumbnail/video profiles;
- keep overlay formulas unchanged and wait for fresh measurement.

### Slice C: editor transform correctness

- compute content-box cover/contain transform;
- capture editor baseline revision;
- map marks to declared full-media/export plane;
- verify through colored marker fixture.

### Slice D: local mixed-ratio output fixture

- add stable output identities/per-output metadata in fixture scope;
- exercise reflow/cover/contain/source-gated policies;
- keep real provider/history integration out of scope.

### Slice E: source-driven refinement

- only after `OC-EQ-009` evidence;
- adopt exact portrait/square/video/output-switch/resize behavior;
- update source fixtures and `VR-023` rather than adding exceptions.

Each slice requires explicit coding authorization and a scoped implementation plan.

## 22. Rejected Designs

- one shared `width/height` pair for media pixels and graph frame;
- parsing generation display strings to determine geometry;
- using thumbnail natural dimensions as full media truth;
- applying global `object-cover` or global `object-contain` to all roles;
- fixing the generic square-image conflict only by changing the label;
- letting `ImagePreviewOverlay` trust zero/stale dimensions without a gate;
- normalizing editor marks directly against cover-cropped outer node rect;
- output switch by array index without stable output identity;
- selected output update without per-output dimensions;
- changing node frame after output switch in a second graph transaction;
- treating React Flow measured changes as semantic resize/history;
- introducing `NodeResizer` because width/height fields exist;
- moving/clamping overlays to hide stale node geometry;
- copying Open Canvas fixed card widths/request-aspect policy into LibTV;
- merging ordinary LibTV, FrameOS and Director rendition owners.

## 23. Acceptance Gate

The design is implementation-ready at documentation level when:

- dimension authorities and field roles are explicit;
- full/thumbnail/output identities and metadata provenance are distinct;
- frame and rendition profiles are declared per surface;
- cover/contain transforms are deterministic and editor-safe;
- mixed-ratio output switching has explicit policy/results;
- passive measurement and semantic resize are separated;
- status/load/decode transitions preserve geometry and last-known-good state;
- graph/history/lifecycle rules compose with existing contracts;
- 42 invariants and `GC-127..145` are indexed;
- `LIBTV-FIX-LOCAL-MEDIA-RENDITION-01` and `LIBTV-VR-023` are discoverable;
- exact source unknowns remain in `OC-EQ-009` rather than clone claims;
- no runtime, test, fixture or source mutation is implied.

## 24. Current Maturity

| Layer | Status |
|---|---|
| fixed Open Canvas evidence | complete for `OC-081..090` |
| clone static audit | complete for `LIBTV-MRG-001..014` |
| current LibTV landscape image source measurement | partial recorded |
| portrait/square/video/mixed-output/resize source evidence | gated |
| formal authority model | design complete |
| runtime metadata/output schema | fragmented/missing |
| source-shaped initial landscape frames | present |
| generic/derived/Director still frame consistency | known gaps |
| visible/intrinsic editor transform | missing |
| local deterministic fixture | designed, not implemented |
| verifier | designed, not implemented |

This contract is sufficient to guide a future authorized implementation without inventing source behavior. It is not evidence that the runtime already satisfies the invariants.
