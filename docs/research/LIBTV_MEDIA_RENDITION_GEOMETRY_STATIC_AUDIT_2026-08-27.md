# LibTV Media Rendition, Aspect And Node Geometry Static Audit

> Status: `COMPLETE` / `FIXED_STATIC_AND_READ_ONLY_SOURCE_AUDIT`.
>
> Scope: fixed Open Canvas media/aspect/frame/rendition methods and counterexamples, current ordinary LibTV clone behavior, and authenticated read-only LibTV source measurements relevant to future UI/UX cloning.
>
> Clone baseline: `fd90b18`; Open Canvas baseline: `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> Source observation: 2026-08-27 at the shared LibTV project URL, existing media only.
>
> Authorization boundary: documentation only. No runtime/test/submodule changes; no upload, generation, edit, save, delete, paid action or source data mutation.

## 1. Why This Audit Exists

The clone has correct source-shaped image-node fixtures and source-shaped selected-node overlay formulas. It does not yet have one authority for the values called width, height, resolution or aspect ratio.

A media node can simultaneously have:

- a decoded source size;
- a thumbnail size;
- an output/version identity;
- a generation request ratio and resolution;
- a graph node width and height;
- a current React Flow measured rect;
- a visible crop produced by `object-fit` and `object-position`;
- normalized editor coordinates;
- an export size.

The values often happen to agree in the initial fixture. That agreement is not guaranteed by the generic creation and derived-output paths. When they diverge, a selected-node toolbar can be correctly centered over the measured node while the media is incorrectly cropped inside it. This audit separates those failures before a normative contract is written.

## 2. Authority Boundary

This document owns dated facts, counterexamples, issue IDs and gap ranking. It does not define the final runtime schema.

| Existing authority | Existing responsibility | This audit adds |
|---|---|---|
| [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md) | host/client/flow/media coordinate domains | which rect/dimension source a rendition profile may consume |
| [`components/LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md) | exact selected-node toolbar/panel formulas | how undeclared node-frame changes can invalidate otherwise correct anchors |
| [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md) | file/asset/locator/lease lifecycle | metadata produced by probe and retained per media/output |
| [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md) | foreground draft/history/commit | editor media-space baseline and crop transform input |
| [`components/LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md) | semantic/reference/runtime field roles | dimension/rendition field classes and collisions |
| [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](open-canvas-2026-08-26/LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md) | model ratio/resolution options | why request parameters are not intrinsic/render geometry |

The future normative authority is reserved as `LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`.

## 3. Evidence Method

### 3.1 Evidence classes

| Label | Meaning |
|---|---|
| `OPEN_CANVAS_FACT` | directly present at the fixed submodule SHA |
| `OPEN_CANVAS_COUNTEREXAMPLE` | fixed upstream structure that should not be transplanted |
| `CLONE_FACT` | directly present in committed clone code |
| `LIBTV_SOURCE_FACT` | current authenticated DOM/computed-style/rect observation without mutation |
| `INFERENCE` | consequence supported by facts but not directly exercised |
| `CLONE_DECISION` | recommended future policy, not current behavior |
| `SOURCE_UNKNOWN` | exact LibTV behavior not safely established |

### 3.2 Fixed Open Canvas paths

- `shared/lib/canvas/types.ts`
- `shared/lib/canvas/serialization.ts`
- `shared/lib/canvas/model-options.ts`
- `shared/blocks/canvas/canvas-media-control.tsx`
- `shared/blocks/canvas/canvas-studio-shell.tsx`
- `shared/services/canvas/local-canvas-runner.ts`

### 3.3 Fixed clone paths

- `src/components/nodes/ImageNode.tsx`
- `src/components/nodes/VideoNode.tsx`
- `src/components/ImagePreviewOverlay.tsx`
- `src/components/ImageAnnotateSurface.tsx`
- `src/components/PictureEditPanel.tsx`
- `src/components/SubtitleErasePanel.tsx`
- `src/components/nodes/ShotBreakdownNode.tsx`
- `src/components/nodes/ShotBreakdownResultNode.tsx`
- `src/store/canvasStore.ts`
- `src/store/uiStore.ts`

### 3.4 Source read-only actions

The browser work was limited to:

1. reading the existing canvas DOM and computed styles;
2. measuring existing node/media rects at the current `28%` zoom;
3. selecting the already-existing `分镜 #2` image node;
4. measuring its node, top toolbar and lower panel rects;
5. checking the current DOM for known React Flow resizer selectors.

No source media, prompt, graph, panel setting or persisted project value was changed.

The machine-readable path/measurement inventory is [`open-canvas-2026-08-26/media-rendition-geometry-static-evidence-2026-08-27.json`](open-canvas-2026-08-26/media-rendition-geometry-static-evidence-2026-08-27.json).

## 4. Executive Findings

### 4.1 Current LibTV source makes node frames media-shaped in the observed landscape samples

Five existing image nodes use centered `object-cover`, but their logical frames are not one fixed 16:9 box:

| Label | Media label ratio | Logical node | Node ratio | Thumbnail decode | Result |
|---|---:|---:|---:|---:|---|
| `1808x1024` | `1.765625` | `618x350` | `1.765714` | `200x113` | ratio-preserving within integer/border/thumbnail rounding |
| `1152x576` | `2.0` | `700x350` | `2.0` | `200x100` | exact ratio |
| `1808x1024` | `1.765625` | `618x350` | `1.765714` | `200x113` | same rule as first sample |
| `1152x576` | `2.0` | `700x350` | `2.0` | `200x100` | exact ratio |
| `1280x720` | `1.777778` | `622x350` | `1.777143` | `200x112` | ratio-preserving within integer/thumbnail rounding |

`LIBTV_SOURCE_FACT`: all rendered media elements had `object-fit: cover` and `object-position: 50% 50%`. The selected `1280x720` node had a logical `622x350` frame, not the clone's generic `512x288` default.

`INFERENCE`: current landscape samples are consistent with a `350`-high media-shaped frame whose width is rounded from the media ratio. This audit does not generalize that formula to portrait, square, extreme-ratio, pending or video nodes.

### 4.2 Open Canvas uses request-shaped cards, not media-shaped nodes

`OPEN_CANVAS_FACT`: image cards are fixed at `340px` width, video cards at `356px`; their preview wrappers derive CSS `aspect-ratio` from `nodeData.aspectRatio`. The selected media descriptor does not store intrinsic dimensions.

This is a coherent card-editor choice but not a LibTV parity method. Open Canvas can keep the same card frame while switching output identity because `object-cover` absorbs mismatch. Current LibTV evidence instead ties each observed image-node frame closely to its media label ratio.

### 4.3 The clone has both a strong source-shaped fixture and unsafe generic paths

Positive clone facts:

- initial shared-project image/video nodes preserve source-like graph frame ratios;
- panorama explicitly couples `700x350` media metadata, graph frame and `2:1` request label;
- Director animation export derives graph node dimensions from `16:9`, `9:16` or `1:1` and renders the actual video with `contain`;
- image detail preview uses `contain` rather than repeating the canvas crop.

Conflicting clone facts:

- a new default image stores `512x512` media data in a `512x288` graph frame;
- most derived image actions inherit source media dimensions but silently return to a `512x288` graph frame;
- a Director still capture stores its real aspect/dimensions but always uses the generic landscape image frame;
- picture-edit/subtitle normalized coordinates are computed over the full node rect while the underlying poster is `cover`;
- image preview trusts node-data dimensions and does not verify decoded intrinsic dimensions;
- poster-only and actual-video paths inside the same video node switch between `cover` and `contain` without a named profile.

### 4.4 Passive React Flow measurement is not a resize contract

The fixed Open Canvas source and current observed LibTV DOM contain no `NodeResizer`, known node-resizer selector or explicit node-resize callback. Both systems read measured dimensions for centering/overlay calculations.

The correct conclusion is:

```text
measured rect = current rendering observation
measured rect != user resize intent
serialized width/height != proof of a visible resize feature
```

Any future explicit node resize remains source-evidence-gated.

### 4.5 Highest-value design conclusion

Before adding output histories, real upload or generic resize, the clone needs a deterministic rendition authority that can answer:

```text
which media/output is selected?
what are its intrinsic dimensions and provenance?
which semantic node frame should contain it?
which fit/crop/object-position applies on this surface?
which transform maps visible pixels to full media space?
when must React Flow and selected overlays remeasure?
```

This is primarily a visible-fidelity and interaction-correctness slice. It can be implemented later with local fixtures and no provider/backend.

## 5. Dimension Authority Vocabulary

| Authority | Meaning | Example | Must not be used as |
|---|---|---|---|
| `MEDIA_INTRINSIC` | decoded full media pixel dimensions | `1808x1024` | graph frame without policy |
| `THUMBNAIL_INTRINSIC` | decoded thumbnail dimensions | `200x113` | full asset dimensions |
| `MEDIA_OUTPUT` | one candidate/version identity and metadata | image candidate 3 | generation request |
| `GENERATION_REQUEST` | requested provider aspect/resolution | `16:9`, `1K` | proof of actual output size |
| `NODE_FRAME` | semantic graph width/height | `622x350` | media pixels |
| `NODE_MEASURED` | current React Flow rendered dimensions | custom-node rect | persisted user intent |
| `SURFACE_RENDITION` | fit/crop/object-position for a role | node `cover`, detail `contain` | destructive crop |
| `VISIBLE_MEDIA_RECT` | rendered content/letterbox/crop rect | poster area | full intrinsic plane |
| `EDITOR_MEDIA_SPACE` | normalized/intrinsic coordinates for marks | `[0,1]` point | raw node-local coordinates |
| `EXPORT_OUTPUT` | encoded output dimensions | `1080x1920` | current node frame unless commanded |

## 6. Fixed Open Canvas Evidence Chain

### 6.1 `OC-081`: media identity is richer than a URL but poorer than a rendition descriptor

`CanvasNodeMedia` includes:

```text
url + source + assetId? + mimeType? + thumbnailUrl? + durationSec? + size?
```

It does not include width, height, orientation, focal point, crop, poster dimensions or metadata provenance. Image/video node data separately include output arrays, selected index, generation aspect and resolution.

Useful method: selected output identity is explicit and normalized.

Counterexample: a media entry cannot carry enough information to decide whether selecting it should reflow, crop or letterbox the node.

### 6.2 `OC-082` and `OC-089`: metadata probe is useful, retention is asymmetric

Image upload:

```text
decode exact dimensions
  -> choose closest model-supported ratio
  -> upload
  -> retain media locator/size
  -> patch generation aspect setting
```

Video upload:

```text
load metadata
  -> retain duration
  -> upload
  -> leave existing generation aspect setting unchanged
```

Positive methods:

- the image bitmap is closed;
- fallback object URLs are revoked on success/error;
- invalid model options are normalized before projection;
- media and request settings remain separate fields.

Rejected transplant details:

- throwing from `createImageBitmap` does not fall through to the object-URL decoder;
- exact intrinsic image dimensions are discarded after choosing a lossy nearest ratio;
- video dimensions are not probed or retained;
- image and video upload use different aspect-reconciliation policies without a declared reason.

### 6.3 `OC-083`: preview frame follows request aspect

Open Canvas uses fixed type widths and a preview wrapper with:

```text
style={{ aspectRatio: getAspectRatioCssValue(data.aspectRatio) }}
```

Running/queued overlays occupy the same wrapper, so status does not collapse the preview frame. This stable placeholder geometry is useful.

The conflict is equally clear: `data.aspectRatio` is model/request state, while `primaryImage`/`primaryVideo` is selected media state. The code does not prove they match.

### 6.4 `OC-084` and `OC-090`: surface-role rendition is explicit but metadata reconciliation is not

| Surface | Upstream rendition | Role |
|---|---|---|
| image/video node | full wrapper + `object-cover` | scanable graph card |
| four-output picker | grid + `object-cover` | candidate comparison |
| media settings thumbnail | `4:3` image / `16:9` video + `cover` | compact control |
| full-screen active image | max bounds + `object-contain` | inspect full output |
| full-screen candidate strip | square + `object-cover` | navigation identity |

This role distinction is worth adopting. Exact upstream dimensions and visual styling are not.

Because thumbnails and full assets may use different URLs while the descriptor has no dimensions/crop metadata, the renderer cannot prove that a thumbnail's apparent crop represents the full asset. That is a descriptor gap, not evidence that current upstream thumbnails are wrong.

### 6.5 `OC-085`: selected output identity is normalized

Open Canvas:

- clamps invalid image/video indexes;
- reconciles `image`/`video` to the selected history entry;
- deduplicates history by `assetId` or URL;
- updates both selected index and primary media on switch;
- opens the detail viewer with the full output list and active index.

This is a strong interaction method. It still needs per-output intrinsic/rendition metadata before mixed-ratio switching can be deterministic.

### 6.6 `OC-086`: edited output can drift from the frame

The image editor reports `canvasWidth`/`canvasHeight` in logging, exports/uploads a new media item, appends it to `imageOutputs` and selects it. The graph patch does not update `aspectRatio`, and `CanvasNodeMedia` cannot retain those exported dimensions.

`INFERENCE`: if the edit changes aspect, the new output remains inside the old request-aspect wrapper and is center-cropped. This audit proves the structural possibility, not a reproduced visual incident.

### 6.7 `OC-087` and `OC-088`: measured geometry is an anchor input

The graph serializer preserves optional `node.width`/`node.height`; runtime `measured` dimensions are excluded. Double-click centering and selected action/editor overlays use:

```text
measured -> node width/height -> fixed fallback
```

This is useful for current-frame anchoring. It does not provide:

- a media-ready geometry epoch;
- stale-measurement invalidation;
- explicit remeasurement after output/ratio switch;
- a semantic resize command;
- source-exact LibTV gaps or clamp behavior.

## 7. Current LibTV Source Read-Only Evidence

### 7.1 Rendered image structure

For selected `分镜 #2`:

```text
react-flow node       622 x 350, overflow visible
  node shell          622 x 350
    media frame       622 x 350, 1px border, overflow hidden
      image content   620 x 348, object-cover, center
```

The image URL was a `resize,w_400,m_lfit/format,webp` thumbnail. Its decoded `200x112` ratio differs slightly from the displayed `1280x720` label due to integer thumbnail rounding, while the node frame remains near 16:9.

This explains why `cover` can coexist with a media-shaped node: it absorbs thumbnail and border rounding without necessarily imposing a different creative crop.

### 7.2 Selected overlay relation

At viewport transform `scale(0.282798)`:

| Surface | Screen rect |
|---|---|
| node | `x=699.2784, y=116.0244, w=175.9002, h=98.9792` |
| top toolbar | `x=240.9766, y=50.2344, w=1092.5, h=49` |
| lower panel | `x=457.2286, y=219.5284, w=660, h=273.7969` |

Both floating surfaces were centered on the node's screen center to subpixel rounding. The panel was a prompt/reference variant with a `274px`-class height, not evidence that every selected image panel has this height.

The source's frame ratio therefore participates in overlay placement: a wrong clone node frame changes node top/bottom/center even when the overlay formula itself is correct.

### 7.3 Current source unknowns

The shared project did not safely establish:

- portrait or square ordinary image-node frame policy;
- ready video node media fit and poster/full-video transition;
- mixed-ratio generated-output/version switching;
- whether a focal point or non-centered object position exists;
- media decode error and metadata-ready reflow;
- explicit user node resize in another mode/node type;
- destructive crop versus display crop behavior;
- image preview/detail exact fit for all types.

These remain source-evidence questions. Open Canvas cannot answer them for LibTV.

## 8. Current Clone Inventory

### 8.1 Source-shaped initial fixture

| Node media data | Graph frame | Generation label | Rendition |
|---:|---:|---|---|
| `1808x1024` | `618x350` | `16:9` string | cover |
| `1152x576` | `700x350` | `2:1` string | cover |
| `1280x720` | `622x350` | `16:9` string | cover |
| video `1280x720` label | `622x350` | separate video panel state | failed placeholder |

These values intentionally match current source samples. The generation label can still differ slightly from exact media ratio (`1808:1024` is not exactly `16:9`), proving that the graph frame currently follows media dimensions more closely than the request string.

### 8.2 Generic image creation conflict

`getDefaultNodeDimensions("image")` returns `512x288`; `getDefaultNodeData("image")` returns media dimensions `512x512`. `ImageNode` fills the graph frame with `object-cover`.

Result:

```text
declared square media
  -> landscape graph frame
  -> centered display crop
  -> preview later uses square data ratio and contain
```

The user sees different compositions in the node and detail view, but no policy names that difference.

### 8.3 Derived image conflict

Rotate, multi-angle, lighting, grid, HD and split actions inherit source `width/height/imageUrl`, yet `addDerivedNode` uses generic `512x288` image dimensions unless options override them. A `2:1` or `1808:1024` source can therefore become a 16:9 derived frame before any real model result exists.

Panorama is the positive exception: media data, graph frame and generation label all use `700x350` / `2:1`.

### 8.4 Director output comparison

Still capture:

```text
capture aspect/dimensions retained
  -> graph frame always generic image 512x288
  -> ImageNode cover
```

Animation export:

```text
export aspect/dimensions retained
  -> graph frame selected by aspect
  -> actual video contain
```

The animation path is the stronger local method. It should not be generalized into ordinary LibTV source fact, but it demonstrates that aspect-aware frame selection can be deterministic without a backend.

### 8.5 Video poster and video element

The ordinary ready poster uses `object-cover`; a Director animation's actual `<video>` uses `object-contain`. These can both be valid surface policies, but they currently depend on an incidental metadata branch rather than an explicit rendition profile.

Failed/pending/empty states keep the graph node frame, which is a positive geometry-stability property.

### 8.6 Detail preview trusts graph metadata

`ImagePreviewOverlay` computes its wrapper ratio from `preview.width / preview.height` and uses `object-contain`. The state comes directly from `ImageNodeData`; no decode-time check reconciles stale or invalid dimensions.

If node data and the actual asset differ, the outer wrapper and inner contained image can disagree. Width/height of zero also produces an invalid ratio without a typed failure path.

### 8.7 Media editors currently bind to the cropped node plane

`PictureEditPanel` and region-mode `SubtitleErasePanel` normalize client points using an `absolute inset-0` node overlay. `ImageAnnotateSurface` likewise sizes a blank canvas from the rendered node rect.

When the underlying media is `object-cover`, the stored coordinates describe the visible cropped plane. There is no declared transform for:

```text
visible node rect
  -> cover crop offsets
  -> full intrinsic media coordinates
```

This is harmless only while media and node ratios agree. The generic/Director conflicts show that the assumption already fails structurally.

### 8.8 Fixed-ratio secondary surfaces

- Shot Breakdown source uses `294/165` and cover;
- Shot Breakdown result cards use `aspect-video` and cover;
- continuation/reshoot filmstrips use fixed temporal cells and cover;
- reference/history/library thumbnails use small fixed frames and cover, sometimes `object-top`.

Fixed thumbnail/filmstrip crop is usually appropriate because those surfaces optimize scanning. It must remain a surface role, not leak into node/editor/export geometry.

## 9. Clone Issue Register

| ID | Finding | Visible consequence | Risk | Priority |
|---|---|---|---|---:|
| `LIBTV-MRG-001` | media data and graph frame both expose generic width/height | agents cannot tell which pair owns rendering | correctness | P0 |
| `LIBTV-MRG-002` | node cover versus detail contain trusts unverified data dimensions | composition changes without a named policy | fidelity | P0 |
| `LIBTV-MRG-003` | default square image enters landscape node | immediate hidden crop | fidelity/correctness | P0 |
| `LIBTV-MRG-004` | derived image inherits media data but resets graph frame | output/tool transitions can jump crop/anchor | fidelity/geometry | P0 |
| `LIBTV-MRG-005` | portrait/square Director capture uses landscape image frame | severe crop of produced media | fidelity | P0 |
| `LIBTV-MRG-006` | animation export has aspect-aware frame + contain | reusable local method | positive | preserve |
| `LIBTV-MRG-007` | video poster/video branch changes fit implicitly | playback can reveal different composition | fidelity | P1 |
| `LIBTV-MRG-008` | editor marks normalize against cropped node plane | model request can target wrong full-media region | semantic | P0 |
| `LIBTV-MRG-009` | annotation canvas has no intrinsic transform | saved/replayed marks cannot be defined | semantic | P0 |
| `LIBTV-MRG-010` | no ordinary per-output metadata/selection model | mixed-ratio versions cannot be reconciled | identity | P1 |
| `LIBTV-MRG-011` | generation settings are opaque strings | display text can be mistaken for geometry | correctness | P1 |
| `LIBTV-MRG-012` | no media-ready geometry epoch/reconciliation | overlays may consume stale measurement | lifecycle | P0 |
| `LIBTV-MRG-013` | Shot surfaces hard-code near-16:9 cover | non-16:9 results silently crop | fidelity | P2 |
| `LIBTV-MRG-014` | initial fixture preserves source-shaped ratios | useful method not shared by generic paths | consistency | preserve |

## 10. What To Adopt From Open Canvas

### 10.1 Adopt as method

- separate selected output identity from primary rendered media;
- clamp/reconcile selected output indexes;
- use stable media descriptors rather than raw browser objects;
- probe metadata before projecting media into graph state;
- keep node/thumbnail/detail surface roles explicit;
- use `cover` for scanable candidates and `contain` for full-content inspection when source evidence agrees;
- keep pending/error overlays inside a stable preview frame;
- use current measured rect for current-frame anchors;
- exclude passive measured dimensions from semantic persistence.

### 10.2 Adapt before use

- retain exact intrinsic dimensions and provenance per media/output;
- probe video dimensions, not duration alone;
- name request-aspect-driven versus media-aspect-driven frame policies;
- reconcile edited/mixed-ratio output selection deterministically;
- add crop-transform metadata when editor coordinates map through `cover`;
- add media-ready/frame epochs before delayed anchor use;
- preserve LibTV source's media-shaped node behavior where evidence supports it.

### 10.3 Reject transplant

- fixed Open Canvas card widths and rounded-card visual language;
- request aspect as automatic LibTV node-frame authority;
- per-output descriptors without dimensions;
- silent center crop after edited output selection;
- image/video metadata asymmetry;
- treating serialized width/height as proof of user resize;
- Open Canvas overlay offsets, clamp behavior or provider/model options.

## 11. Value Ranking For Future Implementation

| Slice | User value | Backend need | Source confidence | Recommendation |
|---|---:|---:|---:|---|
| local mixed-ratio fixture + explicit frame/rendition profiles | 5 | 0 | 4 | first |
| fix generic/derived/Director frame-media mismatches | 5 | 0 | 4 | first authorized batch |
| define visible-to-intrinsic crop transform for mark editors | 5 | 0 | 3 | design with first slice, implement after fixture |
| metadata-ready/decode-error geometry state | 4 | 0 | 3 | second |
| selected output identity + per-output metadata | 4 | 0 for fixture | 2 | after source/version evidence |
| generic user node resize | 2 | 0 | 1 | do not implement without source evidence |
| provider-derived exact output metadata | 3 | real integration | 1 | out of prototype scope |

## 12. Proposed Contract Inputs

The normative contract should be able to express, conceptually:

```text
MediaDescriptor {
  mediaId
  fullLocator
  thumbnailLocator?
  intrinsic: { width, height, provenance, status }
}

MediaSelection {
  outputId
  mediaId
  selectedIndex
}

NodeFramePolicy =
  SOURCE_MEDIA_SHAPED
  | REQUEST_ASPECT_SHAPED
  | TYPE_FIXED
  | EXPLICIT_SEMANTIC_FRAME

RenditionProfile {
  surfaceRole
  fit
  objectPosition
  visibleMediaTransform
}
```

Names and exact runtime representation remain a design decision. This audit only proves the missing distinctions.

## 13. Fixture And Verifier Requirements

`LIBTV-FIX-LOCAL-MEDIA-RENDITION-01` should contain deterministic local media for:

- `16:9`, `2:1`, `1:1`, `9:16` and one odd ratio;
- matching and mismatching thumbnails;
- valid, missing, zero and conflicting dimensions;
- image and video-ready poster/full media pairs;
- at least three outputs on one node with different ratios;
- pending, error, empty and ready states;
- source-shaped, request-shaped and fixed-thumbnail surface profiles;
- one editor mark with a known full-media target through cover crop.

`LIBTV-VR-023` should prove:

1. graph frame and visible media rect are stable and finite;
2. node `cover` crop matches the declared transform;
3. detail `contain` reveals full media without changing graph state;
4. output switch updates media identity/metadata atomically;
5. frame reflow, when allowed, triggers current measurement before overlay assertions;
6. toolbar/panel remain centered and preserve their source-contract gaps;
7. editor point round-trips through visible/intrinsic space;
8. pending/error/decode failure do not collapse geometry;
9. passive React Flow measurement creates no graph history;
10. no generic resize control appears unless separately source-authorized;
11. desktop/mobile and multiple zooms remain free of document overflow;
12. console/page/request errors are checked separately from visual assertions.

## 14. Source Evidence Queue

Reserve `OC-EQ-009` and `LIBTV-FIX-SOURCE-MEDIA-RENDITION-01` for:

- landscape, square and portrait ordinary image nodes;
- ready video poster versus playback element;
- generated output/version candidates with mixed ratios;
- node/detail/thumbnail fit and object position;
- selected overlay remeasurement after a legitimate output/frame change;
- presence/absence and semantics of node resize affordances;
- load/decode/error geometry behavior;
- mark/crop coordinate behavior on a deliberately nonmatching frame.

The shared project remains read-only. Ratio-diverse upload/generation/edit scenarios require a disposable source fixture and explicit action authorization.

## 15. Next Documentation Actions

1. Write `LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md` using these fixed facts.
2. Classify affected identity/document fields without changing runtime schemas.
3. Add the fixture/verifier design and graph invariants only after the contract state machine is stable.
4. Publish `OC-PATTERN-13`, `OC-ADOPT-026`, `OC-TR-019`, `OC-BP-013`, `LIBTV-UIX-23`, `DEC-039`, `LIBTV-TR-045` and `LIBTV-PAR-016`.
5. Add `OC-EQ-009` without upgrading unknown source behavior into clone decisions.
6. Preserve this audit as a dated reference when the active plan is promoted.

No item in this section authorizes runtime or test changes.
