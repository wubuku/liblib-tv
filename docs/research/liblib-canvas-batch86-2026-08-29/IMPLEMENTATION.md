# Batch 86 实施与验证记录

> 状态：`RECORDED_PASS`。
>
> 实施日期：2026-08-29。
>
> 代码与验证脚本均在 `master` 主 worktree 完成。

## 1. 实施内容

### 1.1 变换目标上下文

[`DirectorViewport.tsx`](../../../src/components/director/DirectorViewport.tsx)
在底部变换工具栏加入 `data-director-transform-context` surface。它显示：

- 当前目标名称或“未选择对象”；
- 目标类型：object、group、path-anchor、path-drawing、busy 或 none；
- 当前状态：editable、locked、blocked 或 idle；
- 对应的可变换说明，例如“可拖动三轴控件”“对象已锁定”。

这个 surface 是 clone-owned discoverability，不宣称 LibTV 原站有同样的
文字、位置、颜色或 ARIA 结构。多选状态明确显示“多选暂不显示三轴控件”，
避免让用户误以为多个对象已经绑定到单一 gizmo。

### 1.2 TransformControls 取消清理

对象和分组控制器现在除既有 window-level `pointerup`/`pointercancel` 外，
还显式响应：

- `onPointerCancel={cancelTransform}`；
- `onLostPointerCapture={cancelTransform}`。

路径锚点已有 `onPointerCancel`，因此本批只补对象和分组控制器的缺口。取消
会恢复同一 Three.js transform target、清空 active gesture，并避免写入 history。

### 1.3 未改变的边界

- 没有改变 Batch 77 的 explicit `object={transformTarget}` attachment；
- 没有改变 `authoredObjects` 是 authoring baseline、`objects` 是 runtime
  projection 的权威关系；
- 没有改变锁定对象的删除/可见性策略；
- 没有改变普通 React Flow 画布导航、FrameOS 或源站 Director 结论。

## 2. 验证

### 2.1 Pure/source verifier

```bash
node --experimental-strip-types scripts/verify-liblib-batch86.mjs
```

结果：`PASS`。覆盖目标上下文 selector、对象/分组 pointer cancel、
lost pointer capture、authoring/runtime/history 边界和证据边界。

### 2.2 Fresh-page Playwright

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch86.py
```

结果：`SCRIPT_RECORDED_PASS`。覆盖：

- 无选择目标上下文；
- 选中对象后的目标名称、移动提示和 Inspector 位置字段；
- 真实 gizmo pointer drag；
- pointercancel 后 baseline 恢复、gesture 清理和 zero history；
- authoring/runtime 同步、一次 history、undo/redo；
- 锁定目标上下文、`DIRECTOR_TARGET_LOCKED` 和 zero mutation；
- 移动端工具栏边界与无横向溢出；
- console/page/request diagnostics 均为 `0 / 0 / 0`。

结构化结果见 [`runtime-audit.json`](runtime-audit.json)。

### 2.3 Current-gate 串行回归

使用固定 `http://localhost:4317`，按项目当前 Director 闸门顺序串行运行
Batch 59、67–86，全部通过。结构化记录见
[`current-gate-regression.json`](current-gate-regression.json)。

本次回归没有写截图，历史截图/审计文件没有被重写，所有 browser 阶段的
console/page/request diagnostics 均为零。

## 3. 运行时观察

验证过程中发现 undo/redo 会恢复被记录文档快照中的 selection authority。
因此 verifier 在 undo/redo 后重新选择目标，再测试该目标的锁定反馈；这不被
本批升级为产品 bug，也作为 Batch 87 的候选研究问题记录，避免把测试 fixture
误写成源站行为。

## 4. 证据边界

| 类型 | 结论 |
|---|---|
| `CLONE_FACT` | 当前 clone 的目标上下文、TransformControls 和 typed lock rejection 已通过 |
| `CLONE_DECISION` | 目标/原因应在变换入口附近可发现，取消清理应靠近控制器 |
| `SOURCE_UNKNOWN` | LibTV 原站 Director exact target label、gizmo placement、lock feedback 和 undo selection policy |

本批没有新增截图；按照项目截图识别台账规则，已有 `SCREENSHOT_ANALYSIS.md`
不能回答上述 clone-owned reliability 问题，因此没有重复视觉识别。

## 5. 结果

| Gate | Result |
|---|---|
| pure/source verifier | `PASS` |
| fresh-page Batch 86 | `SCRIPT_RECORDED_PASS` |
| current-gate Batch 59, 67–86 | `CURRENT_GATE_SERIAL_REGRESSION_RECORDED_PASS` |
| diagnostics | `0 / 0 / 0` |
| screenshot artifact delta | `0` |
| source-exact Director claim | `NONE` |
