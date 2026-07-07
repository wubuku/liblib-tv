# BottomToolbar Specification

## Overview

- **Target file:** `src/components/BottomToolbar.tsx`
- **Position:** Fixed at `bottom-4` centered horizontally (`left-1/2 -translate-x-1/2`).
- **Background:** `rgba(20,20,20,0.7)` + `backdrop-blur-md` + border `border-[#363636]` + `rounded-xl`.
- **Padding:** `p-1.5`.
- **z-index:** 40.

## DOM Structure (left → right)

```
<div className="fixed bottom-4 left-1/2 -translate-x-1/2 flex flex-row items-center gap-1 p-1.5 bg-[rgba(20,20,20,0.7)] backdrop-blur-md border border-[#363636] rounded-xl z-40"
     style={{ boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>

  <ToolbarButton className="h-7 w-auto gap-1.5 px-3 text-sm font-normal" onClick={toggleAssetPanel}>
    <AssetIcon />
    <span>资产管理</span>
  </ToolbarButton>

  <ToolbarButton className="h-7 w-7" tooltip="整理画布，Option+Shift+F"><ArrangeIcon /></ToolbarButton>
  <ToolbarButton className="h-7 w-7" tooltip="角色"><CharacterIcon /></ToolbarButton>

  <button className="h-10 w-10 rounded-full bg-[#09caf5] text-[#171717] hover:bg-[#5ddcff] transition-colors mx-1"
          aria-label="添加节点">
    <AddIcon />
  </button>

  <ToolbarButton className="h-7 w-7" tooltip="整理节点"><ArrangeNodesIcon /></ToolbarButton>
  <ToolbarButton className="h-7 w-7" tooltip="收藏"><StarIcon /></ToolbarButton>
  <ToolbarButton className="h-7 w-7" tooltip="历史记录"><HistoryIcon /></ToolbarButton>
  <ToolbarButton className="h-7 w-7" tooltip="分镜"><ImageIcon /></ToolbarButton>
  <ToolbarButton className="h-7 w-7" tooltip="帮助" onClick={toggleShortcutsPanel}><HelpIcon /></ToolbarButton>

  <ToolbarButton className="h-7 w-auto px-3"><span className="text-xs">{zoomLevel}%</span></ToolbarButton>
</div>
```

## Components Used

- **`ToolbarButton`** (private inner component) — icon button wrapper that uses `@base-ui/react/tooltip` for the hover tooltip with 300ms delay.

## Interactions

| Element | Click Effect |
|---------|-------------|
| 资产管理 | `toggleAssetPanel` in `useUIStore` (panel not implemented; currently no-op). |
| 整理画布 icon | No-op (reserved for auto-arrange). |
| 人物 icon | No-op. |
| **`+` (large cyan)** | Opens `AddNodePanel` (`toggleAddNodePanel`). The button is `h-10 w-10`, larger than the rest (`h-7`), drawn in primary cyan. |
| 整理节点 icon | No-op. |
| ⭐ icon | No-op (favorite feature). |
| ⏰ icon | No-op (history). |
| 📷 icon | No-op (image-related action). |
| ? icon | Opens `KeyboardShortcutsDialog` (`toggleShortcutsPanel`). |
| 54% zoom | No-op (could open a percentage menu). |

## Files Referenced

- `src/components/BottomToolbar.tsx`
- `@base-ui/react/tooltip`
