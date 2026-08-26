# LibTV Director Desk Source Evidence

> Observation date: 2026-08-26. This document records LibTV source facts
> separately from the upstream open-source implementation and clone decisions.

## Evidence Sources

| Evidence | Provenance | What it proves |
|---|---|---|
| Logged-in canvas audit | `docs/research/liblib-live-2026-08-25/` | The source canvas is a React Flow graph and exposes a director node entry |
| Saved live string audit | `docs/research/liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json` | The node is named `导演台` and described as building a 3D scene and capturing composition references |
| Current canvas HTML | Source URL captured on 2026-08-26 | The current product still loads the director-related locale and canvas chunks |
| Current locale chunk | `0_o2gxip5splz.js` from the LibTV static host | Director scene, timeline, path, camera and export contracts exist in the current source bundle |
| Hardware acceleration copy | Same locale chunk | Director desk, panorama preview and lighting are explicitly classified as 3D features |

The locale chunk is a product-contract signal, not proof that every named command
is enabled for every account or complete in production. It is stronger than a
marketing claim because the keys are loaded by the current canvas application,
but runtime interaction still needs browser verification.

## Confirmed Product Boundary

The source product is not only a 2D React Flow canvas. The canvas contains a
`DIRECTOR_CONSOLE_3D` node whose description is:

```text
搭建3D场景，截图作为构图参考
```

The current source bundle also identifies:

- scene editing and a dedicated animation timeline;
- transform, pose, prop, group and camera keyframes;
- a main camera track, default camera-motion track and automatic paths;
- character, prop and camera motion trajectories;
- path drawing, anchor editing, orient-to-path and speed curves;
- camera follow/look-at/FOV timeline properties;
- SAM bone-pose controls and character body-part groups;
- ground snapping, Gaussian-scene ground detection and collision surfaces;
- animation video recording, upload and creation of a returned canvas node;
- a phone virtual camera with pairing, gyroscope controls and camera-track import;
- a hardware-acceleration guard covering director desk, panorama preview and
  lighting.

This establishes a real 3D authoring and animation domain. It does not establish
whether the original renderer is Three.js, React Three Fiber or another WebGL
stack. The current saved chunks prove WebGL-dependent behavior, but no reliable
library signature has been extracted yet.

## Source Capability Layers

| Layer | Source-backed capabilities | Verification state |
|---|---|---|
| Canvas entry | director node, default director node naming, 3D composition description | confirmed by live bundle and add-node audit |
| Scene staging | characters, props, groups, camera, ground, panorama/3D environment | confirmed by current bundle contracts |
| Camera authoring | camera tracks, keyframes, follow/look-at, FOV, automatic camera paths | confirmed by current bundle contracts |
| Animation | timeline, playback, loop, zoom, auto-keyframe, property curves | confirmed by current bundle contracts |
| Motion paths | freehand/pen/preset paths, anchors, orientation and speed curves | confirmed by current bundle contracts |
| Character posing | pose keyframes and SAM bone controls | confirmed by current bundle contracts |
| Output loop | screenshot references and animation video returned to the canvas | confirmed by node description and export contracts |
| Mobile control | phone virtual camera, gyroscope and recorded track import | confirmed by current bundle contracts |
| Exact visual geometry | shell widths, toolbar placement, panel dimensions and responsive behavior | requires authenticated runtime inspection |
| Rendering library | Three.js/R3F versus another WebGL implementation | unresolved |

## Implication For The Upstream Project

The upstream project implements a meaningful subset of this source domain:

- real R3F scene staging;
- director/camera view switching;
- character, crowd, primitive, model and camera objects;
- transform controls, aspect framing and screenshots;
- panorama import;
- shot/capture records;
- a host bridge that accepts a canvas panorama and sends captures back.

It does not currently implement the source bundle's animation timeline, motion
paths, camera keyframes, phone virtual camera or animation-video return flow.
Therefore it should be treated as an existing LibTV director-desk
replication/implementation reference, not as a complete snapshot of the current
LibTV feature set.

## Next Runtime Questions

Authenticated browser exploration should answer these before visual calibration:

1. Does opening a director node replace the canvas route, open an embedded
   full-screen desk or mount an overlay?
2. What are the exact left tree, central viewport, right inspector and bottom
   timeline dimensions?
3. Which controls are present in scene-edit mode before animation mode is opened?
4. How are source image/panorama edges represented when the director node opens?
5. Does a screenshot create an image node immediately or only after confirmation?
6. Which timeline and phone-camera features are currently account-gated?
7. What runtime module or global identifies the original WebGL renderer?
