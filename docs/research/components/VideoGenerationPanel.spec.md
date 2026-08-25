# VideoGenerationPanel

## Purpose

`src/components/VideoGenerationPanel.tsx` is the selected-video lower editor for Seedance 2.5. It is node-anchored, inverse-zoomed, and kept at a stable `660px` screen width.

## Source Contract

- Five input commands: `参考`, `标记`, `特效`, `角色库`, `运镜`
- Reference strip with three local mock assets and Auto Link summary
- Model menu: Seedance 2.5, Seedance 2.0 VIP, Minimax H3, Kling O3
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

## State

`model`, `mode`, `ratio`, `resolution`, `duration`, `audio`, `count`, advanced switches, prompt, process view, and local submission state are component-local prototype state. The range uses `onInput` so drag, keyboard, and automation update the same React state path.

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

## Verification

Verified on desktop local clone:

- model and mode menus
- disabled/enabled mode states
- normal and long-video parameter menus
- `300s / 14700`
- read-only four-stage `查看过程` view
- prompt submission state
- child drag, parent move/reselect, pan and zoom anchor geometry
- multi-selection overlay lifecycle

Evidence includes:

- `docs/design-references/liblib-clone-seedance-video-selected-2026-08-25.png`
- `docs/design-references/liblib-clone-seedance-long-video-process-2026-08-25.png`
- `docs/design-references/liblib-clone-batch9-video-anchor-929-2026-08-25.png`
- `scripts/verify-liblib-batch9.py`
