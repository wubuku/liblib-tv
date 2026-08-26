# Batch 43 Plan: Director Camera Look-At And Follow

## 1. Gap And Value Ranking

| Candidate | Current clone | Evidence | Value | Decision |
|---|---|---|---:|---|
| manual coordinate look-at | raw `注视点` XYZ only | exact source labels | 5 | reshape |
| manual rotation look-at | absent | exact source label | 5 | implement |
| object look-at | absent | source concept + upstream implementation | 5 | implement |
| follow target | absent | exact source labels | 5 | implement |
| first/third-person follow | absent | exact source labels | 5 | implement |
| live animated-target follow | absent | workflow implication | 5 | implement |
| path conflict | absent | exact source rejection text | 5 | implement |
| phone-camera conflict | absent | exact source rejection text | 5 | implement |
| preset camera motion | absent | exact labels, no runtime state | 4 | later batch |
| collision/smoothing | absent | no evidence | 2 | defer |

## 2. Implementation Steps

1. Add strict look-at/follow types and pure focus/follow math.
2. Extend serializable camera data with look-at mode/object and follow
   target/offset/view mode.
3. Preserve relation fields through cloning, camera-track sampling and phone
   camera workflows.
4. Apply object look-at and follow relationships after all per-object timeline
   tracks are sampled.
5. Add source-named camera Inspector controls with stable selectors.
6. Render manual rotation through the actual R3F camera rather than `lookAt`.
7. Guard preset/free path creation and phone-camera connection/recording while
   the active camera follows a target.
8. Add focused desktop/mobile Playwright for direct editing, animated-target
   follow, first/third-person differences and conflict behavior.
9. Capture focused clone states once and write `SCREENSHOT_ANALYSIS.md`.
10. Run Batch 35-43 regression and project quality gates, update stable docs,
    commit/push and reassess Director maturity.

## 3. Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-camera-look-at-mode]` | coordinate/rotation/object chooser |
| `[data-director-camera-look-at-object]` | selected object-target metadata |
| `[data-director-camera-target-coordinates]` | manual/object derived XYZ |
| `[data-director-camera-follow-target]` | none/object follow chooser |
| `[data-director-camera-follow-offset]` | follow offset XYZ region |
| `[data-director-camera-follow-view]` | first/third-person segmented control |
| `[data-director-camera-follow-state]` | serialized active relation metadata |
| `[data-director-camera-follow-conflict]` | exact path conflict message |

## 4. Acceptance Criteria

- Camera Inspector displays the exact source labels in the implemented states.
- Coordinate mode uses `lookAt(target)` and edits three finite coordinates.
- Rotation mode uses the camera transform rotation and does not immediately
  overwrite it with `lookAt`.
- Object look-at stores a stable object ID and updates target coordinates when
  that object moves or is sampled by the timeline.
- Follow target stores a stable object ID, offset and first/third-person mode.
- A moving character transform track deterministically moves the followed
  camera at scrub and playback time.
- First- and third-person modes produce distinct finite camera position/target
  values and visible WebGL pixels.
- Camera keyframe FOV remains composable while relation-derived position/target
  are active.
- A followed camera cannot bind preset/free motion paths and exposes the exact
  source path conflict copy.
- A followed active camera cannot enter phone virtual-camera local connection
  or recording and exposes the exact source copy.
- Disabling follow immediately restores ordinary camera transform/target
  authoring without deleting existing tracks.
- Desktop and `390x844` Inspector controls stay within the viewport with no
  document overflow.
- Batch 35-42, focused Batch 43, `docs:check`, `npm run check` and
  `git diff --check` pass.

## 5. Clone Calibration

- focus heights by primitive kind;
- offset defaults and target-local yaw rotation;
- first-person forward distance;
- Inspector widget geometry and responsive wrapping;
- follow application after per-kind timeline composition;
- relationship configuration is persistent camera state, not a new keyframe
  track type.

## 6. Out Of Scope

- exact source DOM/CSS or follow mathematics;
- source `预设运镜` replace/append workflow;
- damping, collision avoidance and obstacle-aware camera rigs;
- head-bone/socket following for imported humanoids;
- keyframed follow target, offset or view-mode changes;
- object deletion and relationship repair;
- real phone/LAN transport.

## 7. Status

- [x] Fresh current HTML and 108-chunk corpus extracted
- [x] Exact look-at/follow/conflict vocabulary recorded
- [x] Fixed upstream object-look-at implementation audited
- [x] Source/upstream/clone boundaries recorded
- [ ] Serializable relation state and pure math
- [ ] Inspector and R3F runtime
- [ ] Path and phone-camera conflict guards
- [ ] Focused Playwright and screenshot ledger
- [ ] Cross-batch regression and stable docs
