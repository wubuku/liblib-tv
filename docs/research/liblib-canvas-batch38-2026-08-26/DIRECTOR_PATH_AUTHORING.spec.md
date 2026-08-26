# Director Path Authoring Specification

## 1. Serializable Contract

```ts
type DirectorMotionPathAnchorType =
  | "vertex"
  | "symmetric"
  | "asymmetric";

interface DirectorMotionPathAnchor {
  id: string;
  position: DirectorTuple3;
  type: DirectorMotionPathAnchorType;
  handleIn: DirectorTuple3;
  handleOut: DirectorTuple3;
}

interface DirectorMotionPathDraft {
  tool: "pencil" | "pen";
  trackId: string;
  objectId: string;
  planeY: number;
  anchors: DirectorMotionPathAnchor[];
}
```

Handles are relative to `anchor.position`. `path.points` remains a serializable
derived polyline used by the existing arc-length sampler.

## 2. Curve Rebuild

- Vertex-to-vertex segments remain straight and do not add unnecessary samples.
- A segment with either outgoing/incoming handle uses a cubic Bezier:
  `P0 = current.position`, `P1 = P0 + current.handleOut`,
  `P2 = next.position + next.handleIn`, `P3 = next.position`.
- Curved segments use 12 deterministic subdivisions.
- Closed paths include the final anchor-to-first-anchor curve but do not persist
  a duplicate first point.
- Every rebuild drops non-finite values and preserves at least two distinct
  points for a valid path.

## 3. Drawing

### Pencil

- Pointer-down on the horizontal drawing plane creates the first vertex anchor.
- Pointer-move appends only after a world-space distance threshold.
- Pointer-up commits when at least two distinct anchors exist; otherwise it
  cancels.

### Pen

- Pointer-down adds a vertex anchor.
- Pointer drag updates the new anchor's outgoing handle and mirrors the incoming
  handle, changing its type to symmetric.
- Pointer-up keeps the draft active.
- Explicit complete or Enter commits; Escape/cancel discards the draft.

Committing replaces only the selected track's previous path. Starting or
cancelling a draft does not mutate the existing path.

## 4. Control Editing

- Clicking an anchor selects its path, bound track, object and anchor.
- Clicking a visible handle selects only that handle while preserving the anchor.
- One TransformControls instance may be active at a time.
- Anchor drag commits world position; handle drag commits a relative tuple.
- Symmetric handle edits set the opposite handle to the exact negative tuple.
- Asymmetric edits leave the opposite handle unchanged.
- Vertex type zeroes both handles.
- Changing vertex to symmetric/asymmetric creates a deterministic tangent from
  neighboring anchors when handles are currently zero.

## 5. Inspector

- Path properties appear with the bound object's ordinary Inspector; they are
  not a floating card over the 3D scene.
- Exact source labels are used for `名称`, `启用曲线`, `锚点类型`, `顶点`,
  `对称`, `非对称` and `位置`.
- Incoming/outgoing handle labels, midpoint insertion, deletion and closed-path
  toggle are clone UX and must remain documented as such.
- Numeric edits rebuild the curve and resample the scene immediately.

## 6. Helper And Capture Boundary

- Draft path, persisted path, anchors, handles and handle guide lines render only
  in director view and outside capture.
- Helpers never appear in the returned PNG.
- A selected path control suppresses the selected object's TransformControls to
  avoid simultaneous gizmos.

## 7. Responsive Contract

- The path menu remains trigger-relative in the timeline band.
- The drawing status stays above the viewport toolbar and never overlaps the
  timeline.
- Path Inspector scrolls inside the existing right rail/drawer.
- Mobile page/body width remains bounded by the viewport.

