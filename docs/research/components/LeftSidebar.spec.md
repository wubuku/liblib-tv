# LeftSidebar Specification

## Overview

- **Target file:** `src/components/LeftSidebar.tsx`
- **Position:** Absolutely positioned at left center (`absolute left-0 top-1/2 -translate-y-1/2`).
- **Layout:** Vertical column of 7 icon-only buttons.
- **z-index:** 40.

## DOM Structure

```
<div className="absolute left-0 top-1/2 -translate-y-1/2 flex flex-col items-center gap-1 p-1 bg-[#171717] border-r border-[#363636]"
     style={{ zIndex: 40 }}>
  <SidebarButton icon={<AddNodeIcon />}     isActive={isAddNodePanelOpen} onClick={toggleAddNodePanel} title="添加节点" />
  <SidebarButton icon={<ToolboxIcon />}     isActive={activePanel === "toolbox"} onClick={...}       title="打开工具箱" />
  <SidebarButton icon={<MaterialIcon />}    isActive={activePanel === "material"} onClick={...}      title="素材库" />
  <SidebarButton icon={<CharacterIcon />}   isActive={activePanel === "character"} onClick={...}     title="角色库" />
  <SidebarButton icon={<HistoryIcon />}     isActive={activePanel === "history"} onClick={...}       title="历史记录" />
  <SidebarButton icon={<KeyboardIcon />}    onClick={toggleShortcutsPanel}                            title="快捷键" />
  <SidebarButton icon={<TutorialIcon />}    isActive={activePanel === "tutorial"} onClick={...}      title="教程" />
</div>

{/* Panels render conditionally */}
{isAddNodePanelOpen && <AddNodePanel />}
{activePanel === "toolbox" && <ToolboxPanel ... />}
{activePanel === "material" && <MaterialLibraryPanel />}
{activePanel === "character" && <CharacterLibraryPanel ... />}
{activePanel === "history" && <HistoryPanel ... />}
```

## Button Style

```
className="relative flex items-center justify-center rounded-lg transition-colors h-8 w-8 cursor-pointer"
         + hover:bg-[rgba(255,255,255,0.08)]
         + isActive ? "bg-[rgba(255,255,255,0.15)]" : ""
```

Optional badge slot (unused currently).

## Interactions

| Button | Click Effect |
|--------|-------------|
| 添加节点 | Toggles `useUIStore.isAddNodePanelOpen`. When true, opens `AddNodePanel` (a panel at `left-14 top-0`). |
| 工具箱 | Toggles local `activePanel === "toolbox"`. Opens `ToolboxPanel` on the left. Click X or sidebar button again to close. |
| 素材库 | Opens `MaterialLibraryPanel` on the right. |
| 角色库 | Opens `CharacterLibraryPanel` on the right. |
| 历史记录 | Opens `HistoryPanel` on the right. |
| 快捷键 | Opens `KeyboardShortcutsDialog` modal. |
| 教程 | Toggles `activePanel === "tutorial"` (no panel implemented). |

## Files Referenced

- `src/components/LeftSidebar.tsx`
- `src/components/AddNodePanel.tsx`
- `src/components/ToolboxPanel.tsx`
- `src/components/MaterialLibraryPanel.tsx`
- `src/components/CharacterLibraryPanel.tsx`
- `src/components/HistoryPanel.tsx`
- `src/components/KeyboardShortcutsDialog.tsx`
