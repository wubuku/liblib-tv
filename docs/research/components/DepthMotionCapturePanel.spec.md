# DepthMotionCapturePanel

## Purpose

`src/components/DepthMotionCapturePanel.tsx` is the ready-video node-local
configuration surface for the clone's `深度动作捕捉` workflow.

## Evidence Boundary

Source evidence confirms the title, intro, resolution label, duration-limit
placeholders, confirm copy and output naming template. It does not confirm the
original panel's exact DOM geometry, trigger location, resolution enum or result
media. Those remain explicitly clone calibration or clone-only decisions.

## Structure

```text
DepthMotionCapturePanel
├── close
├── title + source-backed intro
├── source filename / duration / resolution summary
├── 720P / 1080P resolution segmented control
├── pending / submit reason
└── confirm extraction / spinner
```

## State Rules

- `30s` default fixture: guard feedback, no graph mutation;
- development-only `?duration=10`: panel is reachable;
- changing resolution updates local request-shaped state;
- submit creates one pending reference video and one direct source edge;
- cancel and `Escape` close without graph mutation;
- source remains selected after graph handoff.

## Geometry

The panel follows the existing video lower-editor contract: node-centered,
screen-sized, inverse-scaled and naturally clipped by the viewport. Exact width,
height, offsets and animation are clone calibration because no original
depth-capture screenshot is currently persisted.

## Stable Selectors

- `[data-depth-motion-panel]`
- `[data-depth-motion-close]`
- `[data-depth-motion-title]`
- `[data-depth-motion-intro]`
- `[data-depth-motion-resolution]`
- `button[data-depth-motion-resolution-option]`
- `[data-depth-motion-source-summary]`
- `[data-depth-motion-submit]`
- `[data-depth-motion-spinner]`
- `[data-depth-motion-submit-reason]`
- `[data-depth-motion-output]`
- `[data-depth-motion-duration]`
