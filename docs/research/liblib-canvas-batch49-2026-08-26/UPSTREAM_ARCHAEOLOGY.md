# Batch 49 上游代码考古

## 固定版本

```text
path: research/upstream/storyai-3d-director-desk
commit: 8c8bd361790be4d37158a7430365e65546e358fe
```

## 1. 上游结构

上游 `DirectorCanvas.tsx` 将坐标控件拆成两个层：

```text
main R3F canvas
  -> scene + camera + controls

viewport-gizmo-overlay
  -> second transparent R3F canvas
     -> GizmoHelper(alignment=center-center, margin=[0, 0])
     -> GizmoViewport(disabled, scale=25, axisColors)
  -> DOM hit layer
     -> six transparent 15×15 buttons
     -> projected axis position + z-index
```

这是可迁移的关键：视觉 renderer 与可测试/可访问的命中语义分离，避免
在 GizmoViewport 内部猜 face/axis hit testing，也避免全视口拖拽层吞掉
主场景事件。

## 2. 相机同步

上游把当前 view snapshot 映射到一个相对 target 的 gizmo camera：

```text
relativePosition = snapshot.position - snapshot.target
gizmo camera looks at origin
GizmoHelper updates relative orientation
on axis click:
  target + normalized(axis) * current radius
```

上游还根据 gizmo camera 的投影方向计算 DOM 命中按钮的屏幕位置，并以
projected z 作为层级排序。这一逻辑适合移植为无 Three.js runtime state 的
纯 helper 或局部函数。

## 3. 上游视觉/几何参考

固定上游 CSS 记录：

| 项 | 值 | 迁移方式 |
|---|---:|---|
| overlay | `80×80px` | clone calibration |
| top/right | `20px` | clone calibration |
| hit button | `15×15px` | clone calibration |
| hit button radius | `999px` | clone calibration |
| gizmo axis colors | `#E56C5B/#6CDB7A/#7AA7FF` | borrow |
| overlay z-index | `20` | adapt to clone layers |

这些是 upstream facts，不是 LibTV authenticated measurements。

## 4. 与当前 clone 的适配

当前 clone 没有 upstream 的 `CameraShotSnapshot` local state，也没有
`viewportPanelsCollapsed`。本批只补最小 snapshot bridge：

- Director mode target 使用当前 clone OrbitControls 的 `[0, 1, 0]`；
- Camera mode target/FOV/position 从 active camera object 读取；
- 轴向命中调用 clone-local camera command，将主相机切到 Director mode；
- 不新增 sidebars collapsed，避免同时改变 layout contract；
- 仍保留当前 clone 的 aspect frame、toolbar、capture hiding 规则。

## 5. 不能直接复制

- 上游 `DirectorCanvas` 的完整 camera/capture/panorama 架构；
- 上游外部模型库、GLB、panorama 和 asset persistence；
- 上游 store、undo、project schema；
- 上游 CSS 全量迁移到 Tailwind；
- upstream 的任何未被本批需求使用的 toolbar action。

