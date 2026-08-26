# Director Desk Maturity After Batch 43

## Executive Assessment

The Director Desk now has a coherent relationship-aware camera loop:

```text
select camera
  -> author coordinate, rotation or object look-at
  -> optionally follow an animated scene object
  -> compose relation output after ordinary timeline/path sampling
  -> preserve camera-track FOV
  -> reject incompatible path and phone-camera authoring
  -> disable follow and recover existing tracks/paths
```

The foundational frontend authoring loop is mature and regression-covered.
Remaining work is source-backed product breadth and source visual fidelity, not
a replacement of the current R3F/store architecture.

## Capability Matrix

| Area | Clone maturity | Evidence confidence | Remaining risk |
|---|---|---|---|
| entry, full-screen shell, return | high | mixed source runtime + clone verification | exact source spacing and breakpoints |
| R3F scene and camera framing | high | source vocabulary + upstream + clone verification | source renderer/default details |
| typed timeline and keyframes | high | source vocabulary + clone verification | exact source track chrome/gestures |
| motion paths and curves | high | source labels + upstream + clone verification | exact source geometry/reset semantics |
| camera look-at/follow | high frontend loop | exact source names/conflicts + clone verification | source panel geometry and camera math |
| articulated character pose | medium-high | exact source names + upstream + clone verification | no authenticated source panel DOM/CSS |
| animation export | medium-high | source labels + real clone browser output | source codec/upload/progress |
| phone virtual camera | medium | source vocabulary + clone-local preview | no source transport evidence |
| preset camera motion | low | strong adjacent source vocabulary | replace/append timing and geometry unknown |
| groups/crowds | low | unbounded source vocabulary | interaction and timeline semantics unknown |
| model/environment library | low | source/upstream hints | discovery/import/asset compatibility |

## Stable Architecture

- Camera relationship state is plain serializable data beside target and FOV.
- Timeline evaluation has an explicit ordinary-sampling pass followed by a
  relationship-resolution pass over stable object IDs.
- Three.js cameras, vectors, quaternions and matrices remain outside Zustand.
- Follow resolution overrides sampled position/target but preserves sampled
  FOV and does not delete tracks or paths.
- UI disablement is backed by store guards, so direct actions cannot bypass
  source-proven conflicts.
- Batch 35-43 browser scripts cover the complete current Director foundation.

## Evidence Debt

Current LibTV locale contracts prove look-at/follow labels and three conflicts.
They do not expose source component code, authenticated follow-state DOM/CSS or
camera formulas. Primitive focus heights, target-local yaw rotation, default
offset, first-person forward distance and Inspector layout remain explicit
clone calibration.

The same boundary remains for pose and phone-camera features. Upstream
replication code and local browser behavior are useful implementation evidence,
but are not current LibTV runtime facts.

## Next Candidate

Batch 44 should investigate **source preset camera motion** before crowds:

- the same current locale section already proves `预设运镜`, `替换运镜`,
  `追加运镜`, `环绕`, `半弧`, `推近`, `拉远`, `升降`, `横移`,
  `螺旋上升` and the no-remaining-duration guard;
- the source explicitly blocks presets while camera follow is active;
- the clone already has camera tracks, paths, speed curves and timeline
  duration, so a bounded vertical slice can reuse proven architecture;
- replace/append semantics can be verified deterministically without inventing
  a crowd object model.

The batch must first bound source vocabulary and inspect the fixed upstream for
any analogous camera-preset implementation. Exact preset geometry, duration,
easing, panel layout and replace/append behavior remain unresolved until that
evidence is recorded.
