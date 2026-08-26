# Batch 42 Plan: Director Character Pose And SAM Tracks

## 1. Gap And Value Ranking

| Candidate | Current clone | Evidence | Value | Decision |
|---|---|---|---:|---|
| articulated character | rigid six-part primitive | upstream R3F implementation shape | 5 | implement |
| 20 pose presets | absent | exact current source names + upstream values | 5 | implement |
| pose Inspector tab | absent | exact current source labels + upstream structure | 5 | implement |
| SAM grouped controls | absent | exact source group/bone taxonomy | 5 | implement |
| independent pose track | absent | exact source pose-keyframe semantics | 5 | implement |
| transform + pose composition | impossible due one-track map | implied by distinct source track semantics | 5 | fix |
| viewport bone gizmos / IK | absent | no runtime evidence | 2 | defer |
| imported-rig discovery | absent | unsupported-state inference only | 2 | defer |
| crowd pose authoring | absent | source/upstream breadth | 3 | later batch |

## 2. Implementation Steps

1. Add strict pose preset, rig, control-group and clone/interpolation helpers.
2. Attach serializable rig state to character objects.
3. Replace the rigid character primitive with an articulated nested R3F
   mannequin supporting body, torso, head, arm, wrist, leg and foot controls.
4. Add `属性 / 姿势` Inspector tabs, 20 preset buttons and six SAM groups.
5. Add `kind: "pose"` tracks and serializable pose keyframes.
6. Change timeline application from one track per object to per-kind
   composition.
7. Auto-upsert a pose keyframe at the current playhead on preset/control edit.
8. Render pose tracks distinctly and prevent motion-path authoring on them.
9. Add focused Playwright for visual rig changes, keyframe creation,
   interpolation, transform coexistence and responsive overflow.
10. Record screenshots once, run Batch 35-42 and project quality gates, then
    update stable docs and reassess director maturity.

## 3. Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-character-tabs]` | character-only Inspector tabs |
| `[data-director-character-tab="properties"]` | transform/property surface |
| `[data-director-character-tab="pose"]` | pose surface entry |
| `[data-director-pose-panel]` | full pose authoring region |
| `[data-director-pose-preset="<id>"]` | one of 20 preset commands |
| `[data-director-pose-group="<id>"]` | one source-named SAM group |
| `[data-director-pose-control="<key>"]` | one calibrated continuous control |
| `[data-director-pose-state]` | active preset/control-count metadata |
| `[data-director-track-kind="pose"]` | independent pose timeline row |

## 4. Acceptance Criteria

- All 20 current source preset labels appear once in the pose panel.
- The panel contains `姿势预设`, `姿势调节`, `SAM 骨骼姿势`, all six source
  groups and all 14 source bone labels.
- Applying a preset changes actual nonblank R3F canvas pixels and updates the
  selected character's serializable rig.
- Editing a continuous control clears preset identity and changes rendered
  character pixels.
- First pose edit creates a `姿态` track without removing the existing
  `变换` track.
- Pose edits at distinct playhead times create distinct pose keyframes.
- Scrubbing between pose keyframes interpolates finite controls and updates
  the R3F character.
- Transform and pose sampling both apply to the same character at one time.
- Generic add/delete/select/seek keyframe actions work for pose tracks.
- Motion-path creation is unavailable when the selected track is pose.
- Desktop and `390x844` Inspector/timeline stay within the viewport and page
  width; the pose panel scrolls internally.
- Batch 35-41, focused Batch 42, `docs:check`, `npm run check` and
  `git diff --check` pass.

## 5. Out Of Scope

- source-exact pose panel CSS without authenticated visual evidence;
- IK, viewport bone selection and per-bone transform gizmos;
- imported GLTF/VRM/Mixamo skeleton detection or retargeting;
- body types, clothing, facial controls or hand/finger articulation;
- groups/crowds and group pose keyframes;
- backend persistence.

## 6. Status

- [x] Current locale pose/SAM/timeline contracts extracted
- [x] Fixed upstream pose implementation audited
- [x] Source/upstream/clone boundaries recorded
- [x] Articulated mannequin and rig state
- [x] Pose Inspector and presets
- [ ] Independent pose tracks and interpolation
- [ ] Focused Playwright and screenshot ledger
- [ ] Cross-batch regression and stable docs
