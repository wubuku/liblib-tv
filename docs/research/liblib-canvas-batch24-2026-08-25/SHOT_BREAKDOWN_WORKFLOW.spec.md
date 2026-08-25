# Shot Breakdown Workflow Specification

## Scope

- `src/components/nodes/ShotBreakdownNode.tsx`
- `src/components/nodes/ShotBreakdownResultNode.tsx`
- `src/store/canvasStore.ts`
- React Flow node types `shot-breakdown` and `shot-breakdown-result`

## Input node

- default world size: `320x389`;
- default state: `empty`;
- ready state section metadata: `00:30 · 1280×720`;
- dimensions: `storyboard`, `motion`, `music`;
- default dimensions: all active;
- source paths: local upload or local canvas-video selection;
- running state is a local prototype transition;
- completion does not mount a selected-state result panel.

Stable selectors:

- `[data-shot-breakdown-node]`
- `[data-shot-breakdown-media]`
- `[data-shot-breakdown-source-meta]`
- `[data-shot-breakdown-dimension]`
- `[data-shot-breakdown-start]`

## Result topology

Default completion creates five top-level result nodes:

| Order | Category | Contents |
|---:|---|---|
| 1 | storyboard | group 01, `S01-S03` |
| 2 | storyboard | group 02, `S04-S06` |
| 3 | storyboard | group 03, `S07-S08` |
| 4 | motion | `M01-M03` |
| 5 | music | one BGM card |

Each result is connected from the source analysis node and remains visible when selection changes. Disabling a dimension omits all nodes for that category.

Stable selectors:

- `[data-shot-breakdown-result]`
- `[data-shot-breakdown-category]`
- `[data-shot-breakdown-item]`
- `[data-shot-breakdown-item-action]`
- `[data-shot-breakdown-waveform]`

## Transaction contract

Completion is one store transaction:

1. source node `status` becomes `complete`;
2. result nodes and edges are appended;
3. `resultNodeIds` are stored on the source;
4. one history snapshot is pushed;
5. a second completion call is idempotent while those result nodes exist.

One undo restores the ready source and removes every generated result node/edge. One redo restores them.

## Visual contract

- result surfaces are dark, low-contrast rounded rectangles;
- storyboard and motion use two columns;
- item label is above the media;
- no tabs, result checkmarks, aggregate selection footer or “加入参考” button;
- action icon remains on the media top-right;
- music is narrower than storyboard/motion groups;
- dimensions and offsets are source-shaped clone calibration, not claimed source DOM values.

## Prototype boundary

- all result assets are local static media;
- dynamic cards are still-image previews with a play affordance;
- result action commands provide local UI feedback only;
- no upload service, frame extraction, video analysis, generation task, billing, account asset or persistence claim.
