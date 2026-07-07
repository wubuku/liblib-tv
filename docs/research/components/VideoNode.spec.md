# VideoNode Specification

## Overview

- **Target file:** `src/components/nodes/VideoNode.tsx`
- **Type ID:** `video`
- **Interaction model:** Draggable node with two handles (left target / right source). Selected state shows no embed panel — instead, the **运镜 (camera movement)** button at the bottom invokes `CameraMovementDialog`.

## DOM Structure

```
<div className="w-[320px] overflow-visible rounded-xl bg-[#212121] border ...">
  <Handle type="target" position={Left} id="target" />   ← render at node left edge
  <Handle type="source" position={Right} id="source" />  ← render at node right edge

  <header>
    <VideoIcon />
    {filename}
    <span>{duration}s</span>
  </header>

  <div className="aspect-video bg-[#171717]">  <!-- 16:9 video preview -->
    <div className="text-[#525252]">
      <VideoIcon className="w-12 h-12" />  <!-- large placeholder icon -->
      <span>视频预览</span>
    </div>
    <!-- Hover overlay: play button -->
    <button className="opacity-0 hover:opacity-100">
      <PlayIcon />
    </button>
  </div>

  <div className="border-t border-[#363636] p-3">
    <button onClick={() => setIsCameraOpen(true)}>
      <CameraIcon />
      <span>运镜</span>
      {cameraMovement && (
        <span>· {getMovementLabel(cameraMovement.movementType)}</span>
      )}
      <ChevronDown />
    </button>
  </div>

  <CameraMovementDialog isOpen={isCameraOpen} ... />
</div>
```

## Data Shape

```ts
interface VideoNodeData {
  filename?: string;       // default: "分镜视频"
  duration?: number;       // seconds; default: 5
  cameraMovement?: {
    movementType: string;
    speed: string;
    duration: number;
    amplitude: number;
  };
}
```

## Computed Styles

| Element | Styles |
|---------|--------|
| Wrapper | `w-[320px] rounded-xl bg-[#212121] border overflow-visible` |
| Header | `flex items-center gap-2 border-b border-[#363636] px-4 py-3` |
| Video area | `relative aspect-video bg-[#171717] flex items-center justify-center` |
| 运镜 button | `w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-[#363636] hover:bg-[#525252]` |

## States & Behaviors

| State | Effect |
|-------|--------|
| Default | Shows filename header + video area placeholder + 运镜 button. |
| Hover | Subtle shadow `hover:shadow-[0_4px_12px_rgba(0,0,0,0.3)]`. |
| Selected | Cyan border + cyan glow ring (`shadow-[0_0_0_2px_rgba(9,202,245,0.3)]`). |
| Click 运镜 button | Opens `CameraMovementDialog`. On apply, writes to local state. The button label updates to show the selected type. |
| Connects to other nodes | via the two handles (target + source) styled by `.react-flow__handle`. |

## Files Referenced

- `src/components/nodes/VideoNode.tsx`
- `src/components/CameraMovementDialog.tsx`
