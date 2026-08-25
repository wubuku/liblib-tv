# Add Node Menu Specification

## Target

- Component: `src/components/AddNodePanel.tsx`
- Renderer registration: `src/app/page.tsx`
- Store defaults: `src/store/canvasStore.ts`
- Trigger: bottom primary toolbar `添加节点`

## Source-shaped list

| Order | Label | Clone action | Badge |
|---:|---|---|---|
| 1 | 文本 | create `text` | — |
| 2 | 图片 | create `image` | — |
| 3 | 视频 | create `video` | — |
| 4 | 视频编辑 | create `video-clip` | Beta |
| 5 | 导演台 | create current local director prototype | NEW |
| 6 | 逐帧拉片 | create `shot-breakdown` | SD 2.5 |
| 7 | 音频 | create `audio` | — |
| 8 | 脚本 | create `script`; show source arrow as unverified deeper menu | — |
| 9 | 素材库 | open local submenu | — |

## AudioNode contract

- Type: `audio`
- Default world size: `350x140`
- Data:

```ts
interface AudioNodeData {
  filename?: string;
  duration?: string;
}
```

- Visual: dark node with handles, title `音频`, filename, non-interactive waveform placeholder and duration.
- Prototype boundary: no playback, waveform decoding, upload, or generation.

## Material submenu

- Parent row has a right arrow.
- Child choices:
  - `我的素材库`
  - `预设素材库`
- Selecting either closes AddNodePanel and opens the existing local `MaterialLibraryPanel`.

## Resource feedback

- `上传` and `从生成历史选择` remain local prototype commands.
- Clicking either shows a short status inside AddNodePanel and does not create a false node.

## Stable selectors

- `[data-liblib-overlay="add-node"]`
- `[data-add-node-entry="<type-or-label>"]`
- `[data-add-node-submenu="material"]`
- `[data-add-node-resource="upload"]`
- `[data-add-node-resource="history"]`
- `[data-add-node-status]`
- `[data-add-node-arrow]`
- `.react-flow__node-audio`
