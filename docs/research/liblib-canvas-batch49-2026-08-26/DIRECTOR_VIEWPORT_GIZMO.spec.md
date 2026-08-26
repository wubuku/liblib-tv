# Director 视口原生坐标控件契约

## 1. 目标

为 3D 导演台提供紧凑、可见、可访问的空间方向反馈，并允许用户以离散
正/反轴向快速重置 Director 视角。

## 2. DOM 结构

```text
[data-director-viewport]
  [data-director-viewport-gizmo]
    [data-director-gizmo-webgl-canvas]
    [data-director-viewport-gizmo-hit-layer]
      [data-director-viewport-gizmo-button="x-positive"]
      [data-director-viewport-gizmo-button="x-negative"]
      [data-director-viewport-gizmo-button="y-positive"]
      [data-director-viewport-gizmo-button="y-negative"]
      [data-director-viewport-gizmo-button="z-positive"]
      [data-director-viewport-gizmo-button="z-negative"]
```

## 3. 状态契约

| 状态 | 视觉 | 命中按钮 | 主视口 |
|---|---|---|---|
| `director` | 显示 | 可用 | OrbitControls |
| `camera` | 显示 | 点击后切回 director | active camera view |
| `capturing` | 隐藏 | 不可用 | capture helper 隐藏 |
| `path-drawing` | 可显示但不抢事件 | 不可用 | path plane 独占 pointer |
| `phone-recording` | 可显示但不抢事件 | 不可用 | phone camera workflow 独占 |

## 4. 交互

- 点击按钮前后不修改对象树选中对象；
- 点击轴向只替换 Director mode 的视角 snapshot；
- `X/Y/Z positive/negative` 的 aria label 明确写出正/反方向；
- `Escape` 不单独关闭 gizmo；
- 透明命中层只覆盖 80×80 gizmo 区域，不覆盖整个 viewport；
- `onPointerMissed` 的空白场景清选逻辑保持原样。

## 5. 相机映射

给定 `snapshot.position`、`snapshot.target`：

```text
radius = max(distance(position, target), epsilon)
nextPosition = target + normalize(axis) * radius
nextTarget = target
nextFov = snapshot.fov
```

`axis` 是六个离散方向之一。该公式是 clone-local UX 决策，参考固定上游
实现，不能被解释为当前 LibTV 源码数学。

## 6. 几何

- desktop/mobile overlay 都位于 viewport 右上角；
- overlay 默认 `80×80px`，距 viewport top/right `20px`；
- narrow viewport 通过 `max-width` 保持在容器内；
- gizmo canvas 与 main canvas 独立，不改变主 canvas 尺寸；
- hit button 位置随当前快照投影更新，不能固定写死屏幕坐标。

## 7. 非目标

- 不实现拖动 gizmo；
- 不实现相机对象 transform 写回；
- 不实现 timeline keyframe；
- 不实现 source-exact gizmo DOM；
- 不让 gizmo 进入截图或动画导出像素。
