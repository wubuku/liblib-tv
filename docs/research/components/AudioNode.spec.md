# AudioNode

## Purpose

`src/components/nodes/AudioNode.tsx` renders standalone audio resources on the LibTV canvas.

## Current Size

- world width：`350`
- world height：`140`
- left target Handle
- right source Handle

## Base State

- floating filename above the node
- `音频` heading
- local play control
- deterministic waveform placeholder
- duration at the right
- local prototype copy

The node does not decode or play a remote audio resource.

## Batch 28 Audio-Split Contract

An audio-split result adds:

```typescript
audioSplit?: AudioSplitMetadata;
```

- filename by mode：
  - `av -> {source}_音轨`
  - `vocals -> {source}_人声`
  - `background -> {source}_背景音`
- duration inherited from source video
- metadata records source node, mode, `outputKind: "audio"` and edge
- stable selectors expose the contract for Playwright

The graph transaction is owned by `canvasStore.createAudioSplit`, not by this renderer.

## Prototype Boundary

- waveform is generated CSS, not decoded PCM;
- play is a visual control only;
- there is no output URL, upload, task polling or persistence;
- source labels and topology follow the current bundle, while exact node gap is clone calibration.

## Evidence

- `docs/research/liblib-canvas-batch15-2026-08-25/`
- `docs/research/liblib-canvas-batch28-2026-08-25/SOURCE_EVIDENCE.md`
- `docs/research/liblib-canvas-batch28-2026-08-25/AUDIO_SPLIT_WORKFLOW.spec.md`
