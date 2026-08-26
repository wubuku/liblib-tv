# Batch 44 Plan: Director Preset Camera Motion

## 1. Value Choice

| Candidate | Current evidence | Existing foundation | Decision |
|---|---|---|---|
| preset camera motion | exact entry/modes/7 presets/2 guards | camera tracks, playback, R3F | implement |
| crowds/groups | broad upstream implementation, source contract unbounded | character rig only | defer |
| model/environment library | source/upstream breadth | no asset persistence | defer |

Preset motion is the highest-confidence next vertical slice. It closes a
source-proven camera workflow and exercises existing Director architecture
without adding an invented crowd domain.

## 2. Implementation Steps

1. Add pure finite camera-preset geometry generation for seven IDs.
2. Add serializable last-application/error metadata to timeline state.
3. Add a store action for replace/append camera-keyframe generation.
4. Preserve camera target, FOV, transform scale/rotation and relation fields.
5. Disable any bound generic path without deleting it when preset keyframes
   become active.
6. Add a selected-camera-track `预设运镜` trigger and clone-calibrated popover.
7. Enforce follow and no-room guards in both UI and store.
8. Add focused desktop/mobile Playwright, WebGL pixel checks and state checks.
9. Capture each visual state once and immediately write screenshot analysis.
10. Run Batch 35-44 regression and complete stable docs/commit/push.

## 3. Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-camera-preset-trigger]` | selected camera-track entry |
| `[data-director-camera-preset-panel]` | open preset surface |
| `[data-director-camera-preset-mode]` | replace/append segmented control |
| `[data-director-camera-preset-option]` | one of seven preset IDs |
| `[data-director-camera-preset-status]` | last successful application metadata |
| `[data-director-camera-preset-error]` | exact no-room/follow copy |

## 4. Acceptance Criteria

- All exact source labels are visible in the relevant states.
- Only a selected camera track enables the trigger.
- Replace creates finite sorted camera keyframes spanning `0..duration`.
- Append preserves existing keyframes and starts at the latest keyframe.
- Append at timeline end rejects atomically with exact no-room copy.
- Follow rejects atomically with exact source conflict copy.
- Each preset creates a distinct finite camera trajectory and changes WebGL
  pixels during scrub/playback.
- Generated values preserve FOV and finite target data.
- A bound generic motion path is disabled, not deleted, after successful
  preset application.
- Desktop/mobile panels stay within workspace/document bounds.
- Batch 35-44, `docs:check`, `npm run check` and `git diff --check` pass.

## 5. Clone Calibration

- trigger placement and popover geometry;
- replace span `0..timeline.duration`;
- append span `latest keyframe..timeline.duration`;
- preset sample counts and all spatial offsets;
- constant generated FOV/target values;
- ordinary linear interpolation through generated points;
- path-disable behavior and persistent last-application summary.

## 6. Out Of Scope

- source-exact preset DOM/CSS/math/easing/duration;
- keyframed preset parameters or editable preset intensity;
- blending generic paths with preset motion;
- camera collision, smoothing or obstacle avoidance;
- undo/redo for Director store mutations;
- backend persistence/export parity.

## 7. Status

- [x] Fresh current HTML/locale extraction
- [x] Exact preset/mode/error vocabulary
- [x] Fixed upstream absence audit
- [x] Bounded clone contract
- [x] Pure preset math and store action
- [x] Timeline popover and guards
- [x] Focused Playwright and screenshot ledger
- [x] Cross-batch regression and stable docs

Closeout: 2026-08-26. The preset workflow is a mature clone vertical slice,
but source-exact preset geometry, timing, easing and backend persistence remain
unresolved evidence debt.
