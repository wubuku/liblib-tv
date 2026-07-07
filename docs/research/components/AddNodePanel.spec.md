# AddNodePanel Specification

## Overview

- **Target file:** `src/components/AddNodePanel.tsx`
- **Trigger:** LeftSidebar "+" button (添加节点)
- **Position:** `absolute left-14 top-0` — appears right next to the sidebar.

## DOM Structure

```
<div ref={panelRef} className="absolute left-14 top-0 w-64 bg-[#1f1f1f] border border-[#363636] rounded-lg shadow-xl z-50 overflow-hidden">
  <div className="p-3 border-b border-[#363636]">
    <h4>添加节点</h4>
    <div className="grid grid-cols-2 gap-2">
      {nodeTypes.map(nodeType => (
        <button key={nodeType.type} onClick={...} className="relative ... hover:bg-[#353639]">
          <div>{nodeType.icon}</div>
          <span>{nodeType.label}</span>
          {nodeType.badge && <span className="absolute top-1 right-1 badge">{nodeType.badge}</span>}
        </button>
      ))}
    </div>
  </div>

  <div className="p-3">
    <h4>添加资源</h4>
    <div className="space-y-2">
      <button>↑ 上传</button>
      <button>⏱ 从生成历史选择</button>
    </div>
  </div>
</div>
```

## Node Type Grid (8 types)

| Type | Label | Icon | Badge |
|------|-------|------|-------|
| `text` | 文本 | text lines | — |
| `image` | 图片 | image | — |
| `video` | 视频 | camera | — |
| `composition` | 视频合成 | stack | "Beta" |
| `director` | 导演台 | eye | "NEW" |
| `audio` | 音频 | music note | — |
| `script` | 脚本 | document | — |
| `library` | 素材库 | stack of cards | "NEW" |

## Interactions

| Action | Effect |
|--------|--------|
| Click node type button | `useCanvasStore.addNode(type)`, then `toggleAddNodePanel` to close. |
| Click outside panel | Closes panel. |
| Click 上传 / 从生成历史选择 | No-op (placeholder buttons). |

## Files Referenced

- `src/components/AddNodePanel.tsx`
- `src/store/canvasStore.ts` (`addNode`)
