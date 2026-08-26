# Director Entry Node Specification

## Overview

- **Target file:** `src/components/nodes/ScriptExecutionNode.tsx`
- **Type ID:** `script-execution`（保留历史 type id，产品语义已修正为导演台）
- **Interaction model:** 点击主命令进入全屏 3D 导演台；不是静态脚本步骤卡。
- **Detailed workspace spec:** [`../liblib-canvas-batch35-2026-08-26/DIRECTOR_WORKSPACE.spec.md`](../liblib-canvas-batch35-2026-08-26/DIRECTOR_WORKSPACE.spec.md)

## Visible Contract

节点固定宽 `260px`，显示：

- 场记板图标和标题 `3D导演台`；
- source-backed 说明 `搭建3D场景，截图作为构图参考`；
- 当前原型对象/机位摘要；
- 主命令 `进入导演台`；
- 左右原生 React Flow `<Handle>`。

节点不再显示旧 clone 脑补的 `确认镜头 / 准备资产 / 合成提示词` 三步状态。

## Entry Behavior

`进入导演台` 按钮必须：

- 暴露 `[data-open-director]`；
- 使用 `nodrag nopan nowheel`；
- 在 `pointerdown` 和 `click` 阶段阻止事件冒泡，避免 React Flow 抢占 CTA；
- 调用 `useUIStore.openDirectorDesk(id, activeCanvasId)`；
- 打开 lazy-loaded、`position: fixed; inset: 0` 的 `DirectorDesk`；
- 关闭后重新选中来源节点，且不重置主画布 viewport。

## State Boundary

- `uiStore.activeDirectorNodeId + activeDirectorCanvasId`：工作区打开/关闭和
  canvas-bound owner 生命周期；Batch 58 在 owner 节点删除或 active canvas
  切换时关闭 workspace。
- `directorStore.sourceNodeId`：当前导演台 session 来源。
- `canvasStore.createDirectorCapture`：把截图作为一个 image node 和一条来源 edge
  原子写回画布，并进入画布 undo/redo history。

## Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-node]` | 导演台 React Flow 节点 |
| `[data-open-director]` | 进入导演台命令 |
| `[data-director-workspace]` | 全屏导演台根 |
| `[data-director-capture-node]` | 回流到画布的截图节点 |

## Evidence And Verification

- Source/runtime boundary: [`../liblib-canvas-batch34-2026-08-26/LIBTV_DIRECTOR_EVIDENCE.md`](../liblib-canvas-batch34-2026-08-26/LIBTV_DIRECTOR_EVIDENCE.md)
- Implemented slice: [`../liblib-canvas-batch35-2026-08-26/README.md`](../liblib-canvas-batch35-2026-08-26/README.md)
- Browser verification: `scripts/verify-liblib-batch35.py`
