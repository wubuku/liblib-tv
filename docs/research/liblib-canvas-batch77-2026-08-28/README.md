# Batch 77: Director Transform Controls Binding Regression

> 状态：`IN_PROGRESS`。
>
> 建档日期：2026-08-28；代码基线：`d5734d3`。

## 1. 问题

用户在 Director 选中物体后无法通过三轴控件移动它。当前运行态已确认这不是
隐藏操作：

1. 选中非锁定物体；
2. 保持底部工具条“移动”模式；
3. 拖动物体上的红、绿、蓝轴；
4. 或在右侧 Inspector 修改位置 XYZ。

实际 clone 中，选中“冷掉的咖啡”后 gizmo 出现在场景原点，而不是杯子位置；
拖拽不会修改 `authoredObjects`，并会遗留 active Director gesture。

## 2. 当前判断

这是 clone 实现 bug。Drei `TransformControls` 在 children 模式下绑定自己创建的
wrapper group，而提交逻辑读取内部 `groupRef`。gizmo attachment、视觉 preview
和 commit readback 因此不属于同一个 Three.js object。

同一写法还存在于：

- ordinary scene object；
- character group rig；
- motion-path anchor / Bezier handle。

本批会统一修正三类绑定，并以实际 browser pointer drag 建立回归门禁。

## 3. 入口

- [`PLAN.md`](PLAN.md)：范围、修复决策和验收条件；
- [`STATIC_AUDIT_2026-08-28.md`](STATIC_AUDIT_2026-08-28.md)：代码与运行态复现；
- `IMPLEMENTATION.md`：修复、验证和 checkpoint 结果，完成后补齐；
- [`../liblib-canvas-batch35-2026-08-26/DIRECTOR_WORKSPACE.spec.md`](../liblib-canvas-batch35-2026-08-26/DIRECTOR_WORKSPACE.spec.md)：
  原始 Director workspace 交互合同；
- [`../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)：
  gesture/history 总合同。

## 4. 证据边界

本批修复当前 clone 的 R3F/Drei ownership 回归，不新增 LibTV source-exact
Director 视觉或交互主张，也不重新识别历史截图。
