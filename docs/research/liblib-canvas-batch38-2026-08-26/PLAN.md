# Batch 38 计划：导演台自由路径创作与锚点编辑

## 1. 缺口与价值排序

| Candidate | Current clone | Source evidence | Value | Decision |
|---|---|---|---:|---|
| 铅笔路径拖绘 | absent | direct label + guide | 5 | implement |
| 钢笔路径逐点创建 | absent | direct label + guide | 5 | implement |
| 钢笔 click-drag 对称柄 | absent | anchor-type vocabulary | 5 | implement as calibration |
| anchor selection/translation | passive dots only | editable path model | 5 | implement |
| 顶点/对称/非对称 | absent | exact direct labels | 5 | implement functionally |
| independent asymmetric handles | absent | direct label | 5 | implement |
| anchor insert/delete | absent | inferred editor necessity | 4 | implement and mark clone UX |
| open/closed path toggle | preset-only | not directly labeled | 3 | implement as compact clone command |
| path name edit | fixed fallback | exact `名称` | 4 | implement |
| path transform offset | absent | exact position/rotation/scale/reset | 4 | defer to next path batch |
| animation video export | screenshot only | direct guide | 5 | after path authoring stabilizes |

## 2. Source Fact / Replication Fact / Clone Decision

### LibTV source fact

- The path option panel contains preset, pencil and pen creation.
- A drawn path can be previewed through playback.
- Path anchors expose vertex, symmetric and asymmetric types.
- Path properties include name, enabled, position, rotation, scale and reset.

### Existing replication fact

- The fixed upstream project supplies R3F selection and TransformControls
  patterns but no path domain.
- Batch 37 already supplies serializable paths, arc-length sampling, playback,
  orient-to-path, speed curves and helper-free capture.

### Clone decision

- Add serializable path anchors with relative incoming/outgoing handles.
- Keep `path.points` as a derived sampled polyline so the Batch 37 playback
  pipeline remains stable.
- Pencil drag appends decimated vertex anchors and commits on pointer-up.
- Pen pointer-down adds an anchor; dragging assigns symmetric handles. Explicit
  complete or Enter commits; Escape cancels.
- Anchor type changes rebuild actual sampled geometry. `对称` mirrors handles;
  `非对称` allows independent handles; `顶点` clears handles.
- R3F TransformControls moves one selected anchor or handle and commits on
  mouse-up. While a path control is selected, object gizmos are hidden.

## 3. State Boundary

```text
DirectorMotionPath
  preset: line | ring | rectangle | pencil | pen
  anchors[]
    id / position / type / handleIn / handleOut
  points[]  <- derived sampled polyline

DirectorTimelineState
  selectedMotionPathId
  selectedMotionPathAnchorId
  selectedMotionPathHandle: in | out | null
  motionPathDraft
    tool / trackId / objectId / planeY / anchors[]

R3F runtime
  transparent drawing plane
  path line + anchor meshes + handle meshes
  one temporary TransformControls attachment
```

No Three.js `Vector3`, `Object3D`, geometry or pointer event enters Zustand.

## 4. Implementation Steps

1. Add pure cubic path sampling, handle defaults and tuple helpers.
2. Extend the serializable path/store contract and migrate preset fixtures to
   anchors while preserving existing `points` semantics.
3. Add pencil/pen draft lifecycle and one-path-per-track commit replacement.
4. Add R3F drawing plane, draft preview, anchor/handle selection and transform
   commits.
5. Add exact source-labeled free-draw menu entries and drawing status overlay.
6. Add path/anchor Inspector controls with functional type, position, handle,
   insert, delete, closed and name edits.
7. Add Batch 38 Playwright for both tools, handle semantics, live sampling,
   cancellation, helper-free capture and compact layout.
8. Inspect generated screenshots once, update stable docs, run Batch 35-38
   regressions and production quality gates.

## 5. Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-motion-path-free-draw]` | free-draw menu group |
| `[data-director-motion-path-draw-tool]` | pencil/pen command |
| `[data-director-path-drawing]` | drawing status overlay |
| `[data-director-path-drawing-tool]` | active pencil/pen state |
| `[data-director-path-drawing-complete]` | explicit pen completion |
| `[data-director-path-drawing-cancel]` | cancel draft |
| `[data-director-motion-path-anchor-id]` | semantic persisted anchor |
| `[data-director-motion-path-anchor-type]` | current anchor type |
| `[data-director-motion-path-handle]` | semantic incoming/outgoing handle |
| `[data-director-motion-path-inspector]` | selected path properties |
| `[data-director-path-name]` | path name input |
| `[data-director-path-anchor-type-option]` | vertex/symmetric/asymmetric command |
| `[data-director-path-anchor-position]` | XYZ anchor position |
| `[data-director-path-anchor-handle]` | handle XYZ field |
| `[data-director-insert-path-anchor]` | midpoint insertion |
| `[data-director-delete-path-anchor]` | selected-anchor deletion |
| `[data-director-toggle-path-closed]` | open/closed clone command |

## 6. Acceptance Criteria

- The existing preset selector set remains exactly line/ring/rectangle for
  Batch 37 compatibility; pencil/pen use a separate draw-tool selector.
- Starting either tool requires a selected track and switches to director view.
- Pencil drag with sufficient movement commits one path with at least two
  finite, decimated vertex anchors and exits drawing mode on pointer-up.
- Pen supports multiple anchors; click-drag creates nonzero symmetric handles;
  explicit complete or Enter commits, while Escape/cancel keeps the old path.
- Invalid drafts with fewer than two distinct anchors never replace a path.
- Selected path anchors and non-vertex handles are visible in R3F and mirrored
  into semantic DOM selectors for deterministic tests.
- Moving an anchor or handle changes persisted serializable data, the rendered
  curve and live playback sampling.
- Vertex clears handles; symmetric keeps exact inverse handles; asymmetric edits
  one handle without modifying the other.
- Insert/delete and open/closed commands preserve a valid path and finite sample.
- Path name edits are local and persistent for the current session.
- Object TransformControls are absent while a path control is selected.
- Capture hides path, draft, anchor and handle helpers.
- Desktop and `390x844` retain internal scrolling and zero document overflow.
- Batch 35-37 behavior remains green; no page, console, request or WebGL errors.

## 7. Out Of Scope

- exact LibTV pointer thresholds, plane orientation or completion gesture;
- path-level position/rotation/scale offset and reset;
- path history, persistence, copy/paste or reassignment;
- variable per-anchor interpolation beyond cubic Bezier;
- property curves, pose/group tracks, animation export and phone virtual camera;
- claiming clone anchor styling or Inspector geometry as measured source values.

## 8. Status

- [x] Current online artifact and hash reconfirmed
- [x] Source/upstream/clone boundaries documented
- [x] State, selectors and acceptance matrix documented
- [x] Pure path-anchor helpers and store schema
- [x] R3F drawing and control editing
- [x] Timeline/Inspector UI
- [x] Focused Playwright and screenshot ledger
- [ ] Cross-batch regression, stable docs and final quality gate
