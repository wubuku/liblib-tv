# Director Desk Maturity Assessment After Batch 40

## Decision

The clone's **core director workflow is mature as a frontend prototype**:

```text
open from canvas
  -> stage/select/transform a real R3F scene
  -> edit camera and composition
  -> author typed keyframes
  -> author/edit/transform motion paths and speed curves
  -> preview deterministic animation
  -> capture still composition
  -> record a real playable animation video
  -> return image/video results to the React Flow graph
  -> undo/redo each graph return atomically
```

This means later batches no longer need to prioritize missing glue in the main
authoring loop. They may either deepen source-backed director extensions or
return to high-value canvas fidelity gaps.

## Mature Layers

| Layer | Current evidence |
|---|---|
| workspace | lazy full-screen director over a still-mounted source graph |
| rendering | real R3F/Three.js scene, camera/director views and framing |
| authoring | tree/Inspector selection, object/camera transforms and gizmos |
| timeline | typed transform/camera tracks, keyframes, scrub/playback/loop/zoom |
| curves | source-labeled presets plus editable cubic-Bezier timing |
| paths | preset, pencil and pen creation; anchors/handles; whole-path transforms |
| output | helper-free PNG and browser-recorded playable WebM |
| graph return | direct source edge, target selection and one-step history |
| responsive | desktop three-column workspace and mobile drawers/settings |
| verification | Batch 35-40 Playwright plus production build |

## Remaining Source-Backed Director Extensions

| Candidate | Source evidence | Clone state | Priority after core maturity |
|---|---|---|---:|
| phone virtual camera pairing/gyro/track import | direct locale contracts | absent | 4 |
| character pose/SAM bone controls and pose tracks | direct locale contracts; upstream pose implementation | absent | 4 |
| groups/crowds and group keyframes | direct locale contracts; upstream group implementation | absent | 3 |
| camera follow/look-at authoring | direct locale contracts | target/FOV exist, binding UI absent | 3 |
| model library/import and panorama environments | direct locale contracts; upstream implementation | fixed clone scene only | 3 |
| source MP4 upload and durable media | direct failure taxonomy | browser-local WebM only | 2, blocked by backend scope |
| exact source director geometry | authenticated runtime still incomplete | clone calibrated | 3 |

## Highest-Value Next Decision

The next batch should first inspect the phone virtual-camera locale/runtime
contract because it is the most distinctive remaining director interaction and
has a bounded UI surface. If runtime evidence remains too weak for faithful
implementation, return to the current source-confirmed canvas overlay gaps
(`1092.5px` action set and multi-zoom toolbar positioning) rather than inventing
a phone workflow.

## Boundary

“Core workflow mature” does not mean source parity. The clone still lacks major
director breadth and backend output parity. It means the end-to-end authoring
and return path is functional, observable, documented and regression-protected.
