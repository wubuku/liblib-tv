# LongVideoProcessNode

## Purpose

`src/components/nodes/LongVideoProcessNode.tsx` renders the compact stage cards
created by a long-video submission. It replaces the old assumption that the whole
process belongs inside `VideoGenerationPanel`.

## Evidence Boundary

The article screenshot directly supports a canvas-level material -> shot ->
candidate -> assembly -> final hierarchy with dense many-to-many connections.
It does not provide legible labels, exact node counts, dimensions or a backend
task contract.

The current `3 material / 3 shot / 4 candidate / 1 assembly / 1 final` graph,
copy, local images, dimensions and positions are clone calibration. See:

- [`../liblib-canvas-batch33-2026-08-26/SOURCE_EVIDENCE.md`](../liblib-canvas-batch33-2026-08-26/SOURCE_EVIDENCE.md)
- [`../liblib-canvas-batch33-2026-08-26/SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch33-2026-08-26/SCREENSHOT_ANALYSIS.md)

## Stage Variants

| Stage | Visual |
|---|---|
| `material` | local reference thumbnail, title and source-shaped subtitle |
| `shot` | `Sxx` plan card with a waiting-state subtitle |
| `candidate` | dimmed thumbnail, batch badge and explicit `等待生成` overlay |
| `assembly` | compact merge icon and `等待镜头选择与拼接` |
| `final` | dimmed horizontal thumbnail, `等待拼接` and local Beta boundary |

Every card uses the existing dark node language and standard React Flow Handles.
Candidate and final media must remain visibly pending; local bitmaps cannot imply
that generation completed.

## Metadata

Each node exposes one `LongVideoProcessMetadata` value containing:

- source ID and label;
- shared process ID;
- prompt, model, ratio, resolution, duration, audio, credits and reference count;
- stage, stage index, optional batch index and `pending` status.

This is request-shaped prototype metadata, not a recovered LibTV API.

## Graph Lifecycle

`canvasStore.createLongVideoProcess` creates all 12 nodes and 22 edges in one
history transaction. Source video connects to every shot; materials connect to
multiple shots; shots feed both candidate batches; candidates merge into assembly;
assembly feeds final.

Repeated graphs keep their internal geometry and move downward until the whole
calibrated bounds no longer overlap existing nodes. Source selection is preserved.

## Stable Selectors

- `[data-long-video-process-node]`
- `[data-long-video-process-id]`
- `[data-long-video-process-stage]`
- `[data-long-video-process-stage-index]`
- `[data-long-video-process-batch-index]`
- `[data-long-video-process-source-id]`
- `[data-long-video-process-status]`
- `[data-long-video-process-model]`
- `[data-long-video-process-duration]`
- `[data-long-video-process-credits]`

## Verification

`scripts/verify-liblib-batch33.py` covers stage counts, 22-edge topology, shared
metadata, pending copy, repeated bounds, source selection, atomic undo/redo,
multi-selection and `390x844` clipping.
