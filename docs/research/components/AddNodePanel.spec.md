# AddNodePanel Specification

## Overview

- **Target file:** `src/components/AddNodePanel.tsx`
- **Trigger:** LeftSidebar "+" button (添加节点)
- **Position:** Bottom-primary-toolbar anchored floating panel; on desktop approximately `196x481`, matching the current source screenshot's single-column menu.

## DOM Structure

```
<div ref={panelRef} className="fixed ... w-[196px] ...">
  <h4>添加节点</h4>
  <div>
    {nodeEntries.map(nodeType => <button data-add-node-entry={nodeType.type}>...</button>)}
  </div>
  <h4>添加资源</h4>
  <button data-add-node-resource="upload">上传</button>
  <button data-add-node-resource="history">从生成历史选择</button>
</div>
```

## Node Type List (9 entries)

| Type | Label | Icon | Badge |
|------|-------|------|-------|
| `text` | 文本 | text lines | — |
| `image` | 图片 | image | — |
| `video` | 视频 | camera | — |
| `video-clip` | 视频编辑 | scissors | "Beta" |
| `script-execution` | 导演台 | clapperboard | "NEW" |
| `shot-breakdown` | 逐帧拉片 | scan | "SD 2.5" |
| `audio` | 音频 | music note | — |
| `script` | 脚本 | document | — |
| `material` | 素材库 | library | arrow |

## Interactions

| Action | Effect |
|--------|--------|
| Click create entry | `useCanvasStore.addNode(type)`, then `toggleAddNodePanel` to close. |
| Click 素材库 | Opens a local two-item submenu; selecting either item closes AddNodePanel and opens the existing MaterialLibraryPanel. |
| Click outside panel | Closes panel. |
| Click 上传 / 从生成历史选择 | Shows local prototype status; does not create a fake node. |

## Files Referenced

- `src/components/AddNodePanel.tsx`
- `src/store/canvasStore.ts` (`addNode`)
- `src/components/nodes/AudioNode.tsx`
