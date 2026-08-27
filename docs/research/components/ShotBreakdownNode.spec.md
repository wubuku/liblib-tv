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
- Ready metadata: `00:30 · 1280×720` beside `视频素材`
- Completion action: one store transaction creates persistent `shot-breakdown-result` nodes
- Result state: three storyboard groups, one motion group and one music node, explicitly not a real upstream analysis task

## Media Rendition Boundary

The current source selector and result cards use fixed near-`16:9` frames with
`object-cover`. This is a compact scanning role, not an authority for ordinary
media-node, detail-view, editor or export geometry. Non-`16:9` source/result
media can be visibly cropped by the current prototype.

The `TYPE_FIXED` / `REFERENCE_THUMBNAIL` policy in
[`../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)
allows that crop only as an explicit surface rendition. Source intrinsic
dimensions and eventual result output metadata must remain separate; no
thumbnail or request ratio may overwrite them. `LIBTV-MRG-013` and the designed
`LIBTV-VR-023` retain square/portrait coverage as future work.

## States

| State | Behavior |
|---|---|
| `empty` | Upload/select video; start button disabled |
| `ready` | Poster and source metadata visible; dimensions editable; start enabled |
| `running` | Local component-only transition; start disabled; spinner and `拉片中` |
| `complete` | Button shows `拉片完成`; persistent result nodes remain on canvas independent of selection |

## Result Contract

- Result renderer: `src/components/nodes/ShotBreakdownResultNode.tsx`
- Structured local data: `src/lib/shotBreakdownResults.ts`
- Storyboard: `S01-S08` across three groups
- Motion: `M01-M03`
- Music: BGM waveform, time and play command
- No result tabs, checkmarks, aggregate selection footer or selected-state panel
- One undo/redo removes/restores the source completion state, result nodes and edges together
- Dimension toggles filter which categories are created

## Verification

Batch 24 verifies the ready input, five default persistent results, `S01-S08`, `M01-M03`, BGM, category filtering, deselection persistence, local item action feedback, one-step undo/redo and desktop/mobile canvas bounds.

See `docs/research/liblib-canvas-batch24-2026-08-25/` and `scripts/verify-liblib-batch24.py`. No claim is made that the clone calls a real analysis API.
