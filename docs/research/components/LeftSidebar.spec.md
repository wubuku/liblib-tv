# LeftSidebar Specification

## Overview

- **Target file:** `src/components/LeftSidebar.tsx`
- **Historical name:** `LeftSidebar`; the live component is the centered primary bottom toolbar.
- **Desktop position:** fixed at bottom `16px`, horizontally centered.
- **Layout:** eight icon-only commands in a `338x49` rounded toolbar.
- **z-index:** above the React Flow surface and below opened entry panels.

## Commands

| Button | Effect |
|---|---|
| 添加节点 | Toggles `useUIStore.isAddNodePanelOpen`. |
| 移动 | Toggles canvas move/hand mode. |
| 工具箱 | Opens the source-derived 25-preset `ToolboxPanel`. |
| 素材库 | Opens the two-command `MaterialLibraryPanel`. |
| 角色库 | Opens the character detail/carousel modal. |
| 历史记录 | Opens the asset history modal. |
| 快捷键 | Toggles the anchored shortcuts panel. |
| 教程与帮助 | Toggles the compact tutorial menu. |

## Interaction Contract

- A content panel, add-node panel, and shortcuts panel cannot remain open together.
- Clicking an already active entry closes it.
- Toolbar buttons expose accessible labels and active pressed state.
- At mobile widths the primary toolbar remains the first of two stacked bottom rows; anchored panels move upward to avoid covering it.

Panel-specific geometry, assets and responsive rules are documented in [`MainEntryPanels.spec.md`](MainEntryPanels.spec.md).

## Files Referenced

- `src/components/LeftSidebar.tsx`
- `src/components/AddNodePanel.tsx`
- `src/components/ToolboxPanel.tsx`
- `src/components/MaterialLibraryPanel.tsx`
- `src/components/CharacterLibraryPanel.tsx`
- `src/components/HistoryPanel.tsx`
- `src/components/KeyboardShortcutsDialog.tsx`
