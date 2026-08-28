# Batch 77 计划：Director Transform Controls Binding Regression

> **Purpose**：恢复 Director object/group/path TransformControls 的正确绑定、
> 拖拽提交和 gesture cleanup。
> **Status**：`SCRIPT_RECORDED_PASS`。
> **Date**：2026-08-28。

## 1. 前置合同

- Batch 35：选中非锁定对象后显示 TransformControls，支持
  translate/rotate/scale；
- Batch 69：`authoredObjects` 是 authoring baseline，`objects` 是 runtime
  projection；
- Batch 70：一次 TransformControls drag 应形成一个 Director history entry；
- Batch 71：pointer cancel、Escape 和其他结束路径不得遗留 active gesture。

## 2. 已复现缺陷

fresh-page、`1440x900`、Director 默认场景：

- 对象树选择 `director-prop-mug` 成功；
- store 为 `transformMode = translate`；
- mug authored/runtime position 均为 `[0.25, 1.08, 0.05]`；
- gizmo 渲染在场景原点附近，而不是 mug 上；
- 命中 gizmo 后 `GESTURE_BEGIN` 成功；
- pointer drag 后 authored position 不变；
- pointerup 后 history 仍为 0，active gesture 未清理。

## 3. 根因与修复决策

Drei children 模式等价于：

```tsx
<TransformControls>
  <group ref={actualTarget}>...</group>
</TransformControls>
```

TransformControls 实际 attach 到它自己创建的外层 group；当前 commit 却读取
`actualTarget`。修复采用 Drei 的 explicit object attachment：

```tsx
<>
  <TransformControls object={actualTargetRef} />
  <group ref={actualTargetRef}>...</group>
</>
```

这样 gizmo、drag preview 和 commit readback 共享同一个 `Object3D`。

## 4. 实施切片

### Slice A：绑定修复

- object TransformControls 显式绑定 `groupRef`；
- group TransformControls 显式绑定 group anchor ref；
- path anchor/Bezier TransformControls 显式绑定 control ref；
- 不改变对象 transform 数据结构、坐标系、timeline sampling 或视觉样式。

### Slice B：gesture cleanup

- 只有 `GESTURE_BEGIN` 成功时才认为 drag transaction active；
- mouseup commit 后必须清空 active gesture；
- pointercancel/unmount/owner invalidation 不得遗留 transaction；
- no-change drag 为零 history，而不是悬挂 active gesture。

### Slice C：真实 pointer verifier

- fresh-page 打开 Director；
- 通过对象树选择稳定、未分组、未锁定的 mug；
- 从 store/camera/object transform 计算 gizmo screen anchor；
- 使用 Playwright mouse pointer 命中并拖动实际 gizmo；
- 断言 authored/runtime position 改变、one history、gesture cleared；
- 断言 undo/redo exact、ordinary graph/history 不变；
- 断言 group/path explicit attachment 的静态合同；
- console/page/request errors 为 0，零截图写入。

## 5. 验收条件

| 场景 | 期望 |
|---|---|
| 选中 mug | gizmo 与 mug world position 对齐 |
| translate drag | authored/runtime position 改变 |
| drag commit | exactly one Director history，active gesture cleared |
| undo/redo | exact before/after round trip |
| zero-distance/no-change | zero history，active gesture cleared |
| ordinary graph | nodes/edges/history 不变 |
| existing Director gates | Batch 35、59、67-76 不回归 |
| project checks | docs check、diff check、`npm run check` 通过 |

## 6. 不在本批范围

- 改变 LibTV source-exact gizmo 外观、轴颜色或尺寸；
- 真实 mesh/panorama/asset loading；
- whole-project duplicate 或 durable resource cleanup；
- ordinary React Flow graph transform；
- 通过历史 clone 截图推导新的源站行为。

## 7. 任务状态

- [x] 读取合同与 Drei implementation；
- [x] fresh-page 复现 object gizmo 错位、零提交和 gesture 泄漏；
- [x] 修复 object/group/path explicit attachment；
- [x] 新增并运行实际 pointer drag verifier；
- [x] 运行 Director 跨批回归与全量检查；
- [x] 补齐实施和治理台账；
- [x] commit/push，确认工作区干净。

## 8. 结果摘要

- `scripts/verify-liblib-batch77.py` 已通过真实 Playwright pointer/wheel 输入；
- 普通画布已与 2026-08-28 登录态源站对齐：普通 wheel 平移、默认中键
  平移、`Space`/`H` 左键平移、`Command`/`Control` wheel 缩放，以及 `V`
  空白左键拖动 no-op；
- Director mug gizmo 拖动会同步 `authoredObjects` 与 runtime `objects`，提交
  恰好一条 Director history，undo/redo 可往返，零距离拖动不产生 history；
- 详细实现、运行命令和边界见 [`IMPLEMENTATION.md`](IMPLEMENTATION.md)、
  [`runtime-audit.json`](runtime-audit.json) 与
  [`SOURCE_NAVIGATION_AUDIT_2026-08-28.md`](SOURCE_NAVIGATION_AUDIT_2026-08-28.md)；
- 本计划的最终提交、push 和工作区状态以仓库 git 历史为准。
