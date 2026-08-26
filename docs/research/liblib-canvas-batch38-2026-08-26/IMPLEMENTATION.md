# Batch 38 Implementation Log

> Status: main product implementation complete; focused verification and
> screenshot finalization pending.

## Protection Points

1. Current source hashes, exact vocabulary and evidence boundary.
2. Serializable anchor/handle contract and pure curve rebuild.
3. Store drawing/edit lifecycle.
4. R3F drawing/TransformControls and Inspector/timeline UI.
5. Playwright, screenshot ledger, regressions and stable docs.

## Current Decisions

- Preserve Batch 37's `path.points` sampling boundary and derive it from richer
  anchors.
- Keep drawing draft serializable; keep pointer state and Three.js refs local to
  R3F components.
- Use separate selectors for free-draw tools so Batch 37's exact three-preset
  contract remains stable.
- Do not implement path transforms or animation export in this batch.

## Main Implementation

### Pure geometry and state

- Added serializable `DirectorMotionPathAnchor` records with relative incoming
  and outgoing handles.
- Added deterministic cubic-Bezier expansion, default tangent generation,
  anchor-type conversion and path validity helpers.
- Migrated line/ring/rectangle presets to the same anchor-backed model without
  changing Batch 37's sampled `points` playback boundary.
- Added pencil/pen draft lifecycle, one-path-per-track replacement, explicit
  complete/cancel, anchor selection, position/handle editing, type conversion,
  insertion, deletion, closed toggle and path rename.

### R3F authoring

- Added a transparent horizontal drawing plane at the bound object's Y value.
- Pencil drag appends decimated vertex anchors and commits on pointer-up.
- Pen pointer-down adds an anchor; pointer drag creates exact inverse symmetric
  handles; Enter or the completion command commits.
- Persisted paths render selectable anchors, handle guides and one active
  `TransformControls` attachment.
- Object transform controls are suppressed while a path control or drawing
  draft owns the interaction.

### Timeline and Inspector

- Added source-labeled `自由绘制`, `铅笔路径` and `钢笔路径` commands while
  preserving the exact three Batch 37 preset selectors.
- Added the `正在绘制曲线` overlay with pen completion and cancel commands.
- Added path name, enabled state, open/closed state, anchor list, exact
  `顶点` / `对称` / `非对称` controls, numeric position/handle editing and
  clone-only insert/delete commands.

## Browser-Discovered Regression

The first real pen smoke exposed an event-layer problem that static store tests
would not catch:

1. the drawing plane handled pointer down/move/up;
2. the later synthesized click still reached a scene object;
3. that object became selected, so the bound object's path Inspector vanished.

The fix blocks object and blank-scene selection while a draft is active,
restores the bound object explicitly on commit, and disables `OrbitControls`
during drawing so camera orbit cannot consume the same drag gesture.

Mobile verification exposed a second timing form of the same bug: R3F could
invoke an object click handler whose React closure predated the commit. The
final guard therefore also lives in the store. Viewport-originated selection
requests are atomically ignored while a draft or selected anchor owns the
interaction; explicit object-tree selection remains able to exit anchor editing.

## Main Smoke Evidence

Run against `http://localhost:3000/?batch38-fixed=1` at `1440x900`:

- pencil drag committed 17 anchors and selected the first anchor;
- converting the first pencil anchor to symmetric produced exact inverse,
  nonzero handles and expanded 17 points to 28;
- pen created three anchors and 25 sampled points;
- cancellation preserved the previous path;
- asymmetric output-handle editing left the input handle unchanged and rebuilt
  sampled geometry;
- insertion, deletion and closed toggle preserved a valid path;
- capture contained zero detected cyan/orange helper pixels;
- no console or page errors occurred.

Quality gates after the interaction fix:

```bash
npm run typecheck
npm run lint -- --quiet
```

Both passed.

## Focused Verification

Added `scripts/verify-liblib-batch38.py`. It covers:

- exact free-draw and preset menu contracts;
- real pencil and pen pointer gestures;
- drawing/anchor selection ownership across desktop and mobile;
- symmetric and asymmetric handle semantics;
- name, position, insert, delete and closed-path edits;
- Escape cancellation preserving the old path;
- deterministic playback movement;
- helper-free capture pixels;
- `1440x900` and `390x844` layout/overflow;
- console, page and request failures.

The focused script passes and generates six Batch 38-only image artifacts.
Their one-time interpretation is recorded in `SCREENSHOT_ANALYSIS.md`.

## Commit Protection

- Plan protection: `dc35be3`.
- Implementation protection: pending.
- Verification/finalization: pending.

## Interruption Handoff

If interrupted after the implementation commit, add
`scripts/verify-liblib-batch38.py`, generate only Batch 38 screenshots, inspect
them once into `SCREENSHOT_ANALYSIS.md`, then run Batch 35-38 regressions and
the repository quality gates. Do not stage verifier-regenerated historical
screenshots.
