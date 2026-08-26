# Director Desk Maturity Assessment After Batch 41

## Decision

The phone virtual-camera **frontend authoring loop is mature as a truthful
prototype**:

```text
open source-shaped virtual-camera surface
  -> enter explicit local preview
  -> drive the real R3F active camera
  -> tune stability/level/hold/elevation
  -> record from the current playhead
  -> import a distinct named camera and typed camera track
```

It is not transport-complete. Same-Wi-Fi signaling, certificate trust, real QR
pairing, phone-hosted controls, WebRTC/ICE and diagnostics remain absent and
are visibly not claimed by the UI.

## Director Workflow Maturity

| Layer | Current evidence |
|---|---|
| scene staging | real R3F objects, camera/director views and transforms |
| composition | ratio frame, thirds, still capture and canvas return |
| animation | typed transform/camera tracks, keyframes, scrub/playback/loop |
| motion design | presets, pencil/pen Bezier paths, transforms and speed curves |
| output | helper-free stills and browser-recorded playable WebM |
| remote-camera concept | real local pose preview, timed take and camera-track import |
| graph return | atomic image/video nodes, source edges and undo/redo |
| responsive | desktop workspace plus mobile drawers/settings/phone panel |

The end-to-end director prototype remains mature after Batch 41. Future batches
should add source-backed breadth, not rebuild the core authoring loop.

## Remaining Director Breadth

| Candidate | Evidence | Clone state | Priority |
|---|---|---|---:|
| character pose/SAM bone controls and pose tracks | current locale contracts plus upstream pose implementation | absent | 5 |
| groups/crowds and group keyframes | current locale contracts plus upstream group implementation | absent | 4 |
| camera follow/look-at authoring | direct current locale contracts | target/FOV only | 4 |
| model library/import and panorama environments | direct locale contracts plus upstream implementation | fixed scene | 3 |
| exact source director geometry | authenticated runtime incomplete | clone-calibrated | 3 |
| real phone LAN/WebRTC transport | direct state/diagnostic vocabulary only | explicit local preview | 2 |
| source MP4 upload and durable media | direct failure taxonomy | browser-local WebM | 2 |

## Highest-Value Next Batch

Batch 42 should investigate **character pose/SAM controls and pose tracks**.
This is the strongest remaining director candidate because:

- source vocabulary establishes a dedicated pose-authoring workflow;
- the fixed upstream replication contains mannequin pose primitives and preset
  implementation that can be code-archaeology evidence;
- the clone already has a character object, Inspector, typed tracks and R3F
  transform/render boundaries;
- a bounded first batch can implement a real articulated character and pose
  preset/keyframe loop without requiring backend services.

The next batch must first extract current LibTV pose/SAM vocabulary and inspect
the upstream pose schema/components. It must not label upstream UI geometry or
bone behavior as current LibTV source fact.
