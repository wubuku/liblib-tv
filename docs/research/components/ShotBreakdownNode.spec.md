# ShotBreakdownNode

## Purpose

`src/components/nodes/ShotBreakdownNode.tsx` is the LibTV-specific `逐帧拉片 SD 2.5` React Flow node. It is intentionally separate from `VideoNode`: the original product creates a dedicated node for frame analysis rather than opening a generic video side panel.

## Source Evidence

- Live audit: `docs/research/liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md`
- Entry screenshot: `docs/research/liblib-seedance-2.5-2026-08-25/evidence/frame-analysis-entry.png`
- Result screenshot: `docs/research/liblib-seedance-2.5-2026-08-25/evidence/frame-analysis-output.png`

## Contract

- React Flow type: `shot-breakdown`
- Default world size: `320x389`
- Default state: `empty`
- Dimensions: `storyboard`, `motion`, `music`
- Input paths: local video upload or a local mock video selected from the canvas
- Result state: local example media cards, explicitly not a real upstream analysis task

## States

| State | Behavior |
|---|---|
| `empty` | Upload/select video; start button disabled |
| `ready` | Poster and source metadata visible; dimensions editable; start enabled |
| `running` | Local 900ms transition; start disabled; spinner and `拉片中` |
| `complete` | `ShotBreakdownResultsPanel` appears below the node |

## Verification

Desktop interaction was verified on the local clone at `929x874`: create node, select a canvas video, toggle dimensions, start analysis, wait for completion, switch result tabs, and select result cards. Result screenshot: `docs/design-references/liblib-clone-seedance-shot-breakdown-complete-2026-08-25.png`.

The original live tab was not mutated further after the initial source audit. No claim is made that the clone calls a real analysis API.
