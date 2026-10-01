# Batch 585 — 颜色类行改为源站可编辑 hex 文本框（结清 584 遗留取证）

> 状态：`SCRIPT_RECORDED_PASS`（24 检查）。源站证据：**2026-10-01 实时 CDP
> 采样**。

## 源站实测结构（SOURCE_FACT）

源站每一处颜色行都是 `#` 前缀 + **可编辑 hex 文本框** + 取色器，三者同排：

| 行 | y | 控件 |
|---|---|---|
| 角色 颜色 | 481 / 513 / 518 | `color #4f8ef7` + `text 4F8EF7`（大写、无 `#`）+ `#` |
| 场景 天空颜色 | 452 / 457 | `color #060608` + `text 060608`（小写）+ `#` |

即 hex 文本框是**可输入并提交**的控件，不是静态读数。

## 584 遗留取证的结论（本批结清）

1. **源站姿势页没有踝部/足部组**：姿势面板 `scrollHeight=1766 /
   clientHeight=832`，滚到底（`scrollTop=934`）后最后一行是
   `膝部 → 右 → 弯曲`（相对 y=844），此后无内容。**584 的七组 / 25 关节
   即完整**，无需补踝/足组。
2. **机位属性页的位置/旋转行同样带轴片**：实测 y=390（位置 X/Y/Z）与
   y=534（旋转 X/Y/Z）均有 `<button aria="左右拖动调整 X 轴">`，
   与角色页一致。clone 的 `AxisFields` 是共享组件，583 已覆盖，
   本批补上断言固化。

## clone 合同（CLONE_DECISION）

- 新增共用组件 `HexColorRow`，渲染 `#` + hex 文本框 + 取色器；
- 接入两处：对象属性 颜色（583 原为只读读数 + 隐藏 color input）与
  场景 天空颜色（582 原为只读读数 + 可见 color input）；
- hex 输入规则：允许省略 `#`、大小写不敏感、提交时归一为小写；
  **非法值不提交**并在失焦时回滚到上一个合法值（避免把脏值写进 store）；
- 文本框镜像 store 值（`useEffect` 随外部变更同步），取色器提交路径不变。

## 内容

- `src/components/director/DirectorInspector.tsx`（`HexColorRow`；
  两处颜色行替换；移除 583 的 `data-director-object-color` 隐藏 input，
  统一为 `data-director-color-picker` / `data-director-hex-input`）；
- `scripts/verify-liblib-batch585.py`（24 检查）。

## 回归与门禁

- 回归：583（hex 读数断言随之迁移）/ 582 / 584（113）/ 42 / 89 / 563；
- `tsc --noEmit` 净；`eslint` 0 error；`verify-docs.py` ✓；`next build` ✓。

## 待后续批次

- `directorPmx*`（骨骼控制 / 骨骼选择提示）对应的 UI 未在源站出现，疑为
  「自定义骨骼模型」路径，需确认触发条件后才能取证；
- 全景图「已连接全景图」态：需按 `docs/CANVAS_TEST_MEDIA.md` 的授权测试
  媒体把图片节点连到导演台左侧输入口才能采样（会写入用户真实项目，
  需先确认再做）；
- 其余颜色行（场景 背景颜色 / 地面颜色）源站是否同为 hex 文本框形态
  本批未单独取证（clone 仍是纯取色器）。
