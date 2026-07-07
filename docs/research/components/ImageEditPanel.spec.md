# ImageEditPanel Specification

## Overview

- **Target file:** `src/components/ImageEditPanel.tsx`
- **Trigger:** ImageNode is selected (`selected === true`).
- **Position:** Absolutely positioned below the image node (`absolute left-0 right-0 top-full mt-2`).
- **z-index:** 50.

## DOM Structure

```
<div className="absolute left-0 right-0 top-full mt-2 z-50 bg-[#1f1f1f] border border-[#363636] rounded-xl shadow-xl overflow-hidden">

  <!-- Tabs -->
  <div className="flex items-center gap-2 px-4 py-2 border-b border-[#363636]">
    <button onClick={() => setActiveTab("style")}>风格</button>
    <button onClick={() => setActiveTab("mark")}>标记</button>
  </div>

  <!-- Prompt -->
  <div className="px-4 py-3">
    <p>可直接文字生图，或上传图片输入文字指令...</p>
    <textarea placeholder="输入提示词..." />
  </div>

  <!-- Bottom controls -->
  <div className="px-4 py-3 border-t border-[#363636]">
    <div className="flex items-center justify-between">
      <!-- Left: model selectors -->
      <div>
        <button>Lib Image ▾</button>
        <button>自适应 · 标准画质 · 2K ▾</button>
        <button>预设 ▾</button>
        <button onClick={() => setIsCameraConfigOpen(true)}>
          <CameraIcon /> 摄像机
        </button>
        <button onClick={() => setIsCameraMovementOpen(true)}>
          <CameraMoveIcon /> 运镜
        </button>
      </div>

      <!-- Right: quantity + generate -->
      <div>
        <div>− 1张 +</div>
        <div>ⓘ 18</div>
        <button className="bg-[#09caf5]">→</button>
      </div>
    </div>
  </div>
</div>

<CameraConfigDialog isOpen={isCameraConfigOpen} ... />
<CameraMovementDialog isOpen={isCameraMovementOpen} ... />
```

## Computed Styles

| Element | Styles |
|---------|--------|
| Wrapper | `bg-[#1f1f1f] border border-[#363636] rounded-xl shadow-xl overflow-hidden` |
| Active tab | `bg-[#363636] text-[#f7f7f7]` |
| Inactive tab | `text-[#919191] hover:text-[#f7f7f7] hover:bg-[#353639]` |
| Prompt | `w-full bg-[#363636] text-[#f7f7f7] text-sm p-2.5 rounded-lg border border-[#525252] focus:border-[#09caf5] outline-none resize-none h-16` |
| Selector button | `flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#363636] hover:bg-[#525252]` |
| Generate button | `w-8 h-8 rounded-lg bg-[#09caf5] text-white hover:bg-[#5ddcff]` |

## Interactions

| Action | Effect |
|--------|--------|
| Click 风格 / 标记 tab | Switch active tab. |
| Type in prompt textarea | Updates `prompt` local state. |
| Click 摄像机 button | Opens `CameraConfigDialog`. On apply, currently `console.log` only. |
| Click 运镜 button | Opens `CameraMovementDialog`. On apply, currently `console.log` only. |
| Click + / − | Adjust quantity (1 by default). |
| Click → generate button | No-op (would call generation API). |

## Notes

- This panel is a UI scaffold; no actual generation happens.
- The prompt, camera config, and camera movement are held in component state only.
- On apply events fire `console.log` rather than persisting to the store.

## Files Referenced

- `src/components/ImageEditPanel.tsx`
- `src/components/CameraConfigDialog.tsx`
- `src/components/CameraMovementDialog.tsx`
