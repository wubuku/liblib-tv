# FrameOS Component Inventory

Catalog of FrameOS route components (`src/components/frameos/`). For page-level topology, see [`PAGE_TOPOLOGY.md`](./PAGE_TOPOLOGY.md). For interactions, see [`BEHAVIORS.md`](./BEHAVIORS.md). For the design tokens (palette, etc.), see [`DESIGN_TOKENS.md`](./DESIGN_TOKENS.md).

> FrameOS is a separate route from the liblib-tv clone — different layout, different palette (blue primary `#2563EB`, deeper bg `#0D0D0D`). They share React Flow primitives and the `DeletableEdge` custom edge.

---

## Shell & Docks

| Component | File | Purpose |
|-----------|------|---------|
| `FrameosAppHeader` | `src/components/frameos/FrameosAppHeader.tsx` | Floating top header — "帧界 FrameOS" logo + 金币/积分 counters + 下载桌面端 |
| `FrameosBreadcrumb` | `src/components/frameos/FrameosBreadcrumb.tsx` | "默认作品 / 咖啡馆对峙 / 画布 1" breadcrumb (static, no dropdown) |
| `FrameosToolRail` | `src/components/frameos/FrameosToolRail.tsx` | Left vertical rail — 添加节点 pill + 从素材库选择 + 本地上传 + 帮助 |
| `FrameosHistoryDock` | `src/components/frameos/FrameosHistoryDock.tsx` | Top-right 撤销/重做 buttons |
| `FrameosMapDock` | `src/components/frameos/FrameosMapDock.tsx` | Bottom-left minimap + zoom/fit/arrange dock |
| `FrameosPromptBar` | `src/components/frameos/FrameosPromptBar.tsx` | Bottom-center AI prompt input + 模型 selector + 积分 display |
| `FrameosHelpPanel` | `src/components/frameos/FrameosHelpPanel.tsx` | Help side panel |
| `FrameosNodeEditPanel` | `src/components/frameos/FrameosNodeEditPanel.tsx` | Per-node editing side panel |
| `FrameosNodeToolbar` | `src/components/frameos/FrameosNodeToolbar.tsx` | Floating toolbar that follows the selected node |
| `FrameosIcon` (registry) | `src/components/frameos/icons.tsx` | SVG icon registry used by FrameOS components |

## Nodes

All FrameOS nodes extend `FrameosNodeShell` (shared card chrome with `node-floating-title` header and resize-handle).

| Type ID | File | Notes |
|---------|------|-------|
| `text` | `src/components/frameos/nodes/FrameosTextNode.tsx` | 300×200 paragraph-style text block, double-click to edit |
| `image` | `src/components/frameos/nodes/FrameosImageNode.tsx` | 300×169 or 225×300 portrait, 替换 button in top-right |
| `video` | `src/components/frameos/nodes/FrameosVideoNode.tsx` | 300×169 video cover + play button + review-failed badge |

## Edge

| Type ID | File | Notes |
|---------|------|-------|
| `default` | `DeletableEdge` (from liblib-tv `src/components/nodes/DeletableEdge.tsx`) | Same flowing-pulse + scissors-delete pattern. FrameOS reuses it as-is. |

## Routes

| Path | File |
|------|------|
| `/frameos` | `src/app/frameos/page.tsx` (landing redirect) |
| `/frameos/canvas/[id]` | `src/app/frameos/canvas/[id]/page.tsx` (canvas demo) |
| Layout | `src/app/frameos/layout.tsx` |

## State

| Store | File | Responsibility |
|-------|------|----------------|
| `useFrameosStore` | `src/store/frameosStore.ts` | FrameOS nodes, edges, breadcrumb, prompt-bar state, selection |

## Assets

| File | Purpose |
|------|---------|
| `docs/research/frameos/assets.json` | Images/colors extracted from the live FrameOS site |
| `docs/research/frameos/buttons.json` | Computed styles for every button type |
| `docs/research/frameos/node-cards.json` | Per-node-card DOM extraction |
| `docs/research/frameos/node-styles.json` | Computed node card styles |
| `docs/research/frameos/nodes.json` | Node inventory snapshot |
| `docs/research/frameos/panel-styles.json` | Panel computed styles |
| `docs/research/frameos/prompt-bar.json` | Prompt bar DOM |
| `docs/research/frameos/region-styles.json` | Region (rail/dock/header) styles |
| `docs/research/frameos/svgs.json` | SVG icon registry extracted from FrameOS |
| `docs/research/frameos/global-styles.json` | Global CSS variables / tokens |
| `docs/research/frameos/header-and-prompt.json` | Header + prompt bar combined extraction |
| `docs/research/frameos/components/` | Per-component raw extraction (mirrors `docs/research/components/`) |
| `docs/research/frameos/*.png` | Original site screenshots |

## Removed / Planned

- **Backend integration**: prompt bar is contenteditable but does nothing on submit.
- **History (undo/redo)**: buttons log to console only.
- **Auto-arrange ("一键整理")**: no-op.
- **素材库 / 本地上载 / 帮助**: placeholders.