# VideoGenerationPanel

## Purpose

`src/components/VideoGenerationPanel.tsx` is the selected-video lower editor for Seedance 2.5. It is node-anchored, inverse-zoomed, and kept at a stable `660px` screen width.

## Source Contract

- Five input commands: `参考`, `标记`, `特效`, `角色库`, `运镜`
- Reference strip with three local mock assets and Auto Link summary
- Source-visible model menu:
  - Seedance 2.5 — `2min`
  - Seedance 2.0 VIP — `2min`
  - Minimax H3 — `2min`
  - Seedance 2.0 Fast VIP — `2min`
  - Seedance 2.0 Mini — `2min`
  - Wan 3.0 Prime — `1min`
  - Wan 3.0 — `3min`
- Mode menu keeps source-disabled modes disabled:
  - `文生视频`
  - `全能参考`
  - `图生视频`
  - `首尾帧`
  - `图片参考`
  - `视频编辑`
  - `超长视频 Beta`
- Normal duration range: `4-30s`
- Long-video duration range: `30-300s`
- Normal estimated points: `duration * 46 * count`
- Long-video estimated points: `duration * 49`, therefore `300s = 14700`
- Advanced switches: network search, material check, AutoLink

### Parameter dialogs

The normal and long-video parameter states use source-measured fixed screen geometry:

| State | Size | Relative to generation panel |
|---|---:|---:|
| normal | `341x445` | `left +82`, `top -211.7` |
| long video | `341x397` | `left +90`, `top -163.7` |

Normal includes:

- seven ratio glyph cards in a 5+2 grid;
- `480P / 720P / 1080P` segmented resolution;
- `4-30s` duration with current-value box and slider;
- full-width audio and count segmented controls.

Long video keeps ratio/resolution/audio, switches duration to `30-300s`, adds helper copy and removes count.

Stable selectors:

- `[data-video-params-trigger]`
- `[data-video-params-menu]`
- `[data-video-ratio-option]`
- `[data-video-resolution-option]`
- `[data-video-duration]`
- `[data-video-audio-option]`
- `[data-video-count-option]`
- `[data-video-long-hint]`
- `[data-video-credits]`

Ratio glyphs are clone CSS outlines because the exact source SVG paths were not extracted. The long helper is a conservative paraphrase rather than a verbatim DOM claim.

### Model menu

The model popover uses the source screenshot-backed geometry:

```text
size = 380x410
relative to generation panel = left 0, top -176.7
selected row = 58px
compact row = 48px
```

The first five source-visible items show a premium icon; the two Wan items do not. Only the selected row expands its confirmed description. Known descriptions are limited to:

- Seedance 2.5: `最强视频模型，全能参考，30s音画同步`
- Seedance 2.0 Fast VIP: `最强视频模型快速版，会员专属通道，15s音画同步`

Other model descriptions remain absent until directly extracted. The seven rows are not documented as a complete model library, and the clone icons do not claim the source SVG paths.

Stable selectors:

- `[data-video-model-trigger]`
- `[data-video-model-menu]`
- `[data-video-model-option]`
- `[data-video-model-premium]`
- `[data-video-model-description]`

## State

`model`, `mode`, `ratio`, `resolution`, `duration`, `audio`, `count`, advanced switches, prompt, process view, and local submission state are component-local prototype state. The range uses `onInput` so drag, keyboard, and automation update the same React state path.

Model/menu visibility, authoring controls, clone state, request projection and real runner support are separate evidence layers. Their current three-layer audit and Open Canvas anti-drift lessons are recorded in [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md). The seven visible rows are not a complete executable registry, and the local credits formulas are not billing/API contracts.

## Positioning

The panel is positioned relative to the selected video child with centered translate and `scale(1 / zoom)`. It is not viewport-fixed and does not clamp itself to the browser.

The source semantic gap is `16 * zoom`. Because the clone's absolute containing block is a node shell with a `1px` border, the implementation uses `bottom: -17px`; `-16px` measured as only `15 * zoom`.

At `929x874`, after source-like organize:

```text
video child center = 643.446
panel center = 643.446
panel gap = 4.541px = 16 * 0.283816
panel size = 660x274
```

The video is a child of `g-EFbbHpwq5w`. Child drag, pan, and zoom keep the panel attached. Dragging the parent selects the parent and unmounts the child panel; selecting the child again reconstructs it from the child's new absolute screen rect.

Stable test selector: `data-video-generation-panel`.

## Continuation Target State

When `VideoNodeData.continuation` exists, the same `660x274` panel becomes the second stage of smart continuation:

- source tile and capability text are visible;
- visible prefix is `对 {sourceLabel} 的 {range} 片段进行续写：`;
- Prompt placeholder is `请输入需要续写的内容`;
- model and mode are disabled at `2.5 / 全能参考`;
- `退出续写模式` calls one store transaction that removes metadata and the declared source edge while preserving the target node.

Stable selectors:

- `[data-video-continuation-source]`
- `[data-video-continuation-context]`
- `[data-video-continuation-range]`
- `[data-video-continuation-exit]`
- `[data-video-continuation-locked]`

The source tile uses metadata copied at target creation because this prototype has no service-backed media reference object. Prompt submission remains local feedback.

## Long Video Graph Handoff

Long-video mode no longer presents a four-card process diagram inside the
`660x274` editor. `查看过程` now explains that the process is created on the
canvas after submit.

Submitting long-video mode:

- briefly disables the submit button and exposes `submitting`;
- sends prompt, model, ratio, resolution, duration, audio, credits and reference
  count to the selected source video;
- calls one `canvasStore.createLongVideoProcess` transaction;
- creates a 12-node, 22-edge material/shot/candidate/assembly/final graph;
- keeps the source video selected;
- exposes `created` and the canvas-process confirmation.

The node count, geometry and local busy timer are clone calibration. Candidate
and final cards remain pending and do not claim real generated media.

Stable selectors:

- `[data-video-long-process-info]`
- `[data-video-generate-submit]`
- `[data-video-long-submit-state]`
- `[data-video-long-submit-spinner]`

Detailed node and topology contract:
[`LongVideoProcessNode.spec.md`](LongVideoProcessNode.spec.md).

## Verification

Verified on desktop local clone:

- model and mode menus
- disabled/enabled mode states
- normal and long-video parameter menus
- `300s / 14700`
- canvas-level long-video process graph handoff
- submit busy/created states, request metadata and pending result copy
- repeated process avoidance and atomic graph undo/redo
- prompt submission state
- child drag, parent move/reselect, pan and zoom anchor geometry
- multi-selection overlay lifecycle
- normal/long parameter dialog geometry and control hierarchy
- mode disabled matrix and `300s / 14700`
- source-visible seven-model menu, premium/estimate hierarchy and selected-only descriptions
- continuation source/range prefix, dedicated placeholder and fixed model/mode
- continuation clear transaction, target preservation and undo/redo

Evidence includes:

- `docs/design-references/liblib-clone-seedance-video-selected-2026-08-25.png`
- `docs/design-references/liblib-clone-seedance-long-video-process-2026-08-25.png`
- `docs/design-references/liblib-clone-batch33-long-video-contact-sheet-2026-08-26.png`
- `docs/design-references/liblib-clone-batch9-video-anchor-929-2026-08-25.png`
- `scripts/verify-liblib-batch9.py`
- `scripts/verify-liblib-batch21.py`
- `scripts/verify-liblib-batch22.py`
- `scripts/verify-liblib-batch26.py`
- `scripts/verify-liblib-batch33.py`
