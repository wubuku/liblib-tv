# Batch 588 — 场景面板读数改为可编辑文本框 + 开关行自绘轨道（结清 586 记录项）

> 状态：`SCRIPT_RECORDED_PASS`（52 检查）。源站证据：**2026-10-01 实时 CDP
> 采样**（1920×1150，3D场景 面板）。

## 源站实测（SOURCE_FACT）

### 1. 滑杆读数是可编辑文本框，不是只读文本

五处读数全部是 `input[type=text]`，`readOnly=false`、`disabled=false`，
共用同一套样式 `focus:bg-white/13 h-7 min-w-px flex-1 rounded-lg border-0`：

| 行 | 读数框 | 文本 | range |
|---|---|---|---|
| 场景缩放 | 70×28 | `300%` | `0.1..10` step `0.1` |
| 全景球 水平旋转 | 70×28 | `0°` | `0..360` step `1` |
| 全景球 球形半径 | 70×28 | `60`（**无单位**） | `10..500` step `10` |
| 地面 透明度 | 62×28 | `0.40`（两位小数） | `0..1` step `0.05` |
| 地面 高度 | 62×28 | `0.0`（一位小数） | `-2..2` step `0.05` |

天空颜色 hex 框同族，但 `maxLength=6`，且其 `uppercase` 是 **CSS
`text-transform`**（实测 computed `textTransform: uppercase`，底层值仍按
输入原样保留）——不是把值转大写。

### 2. 三个开关行是自绘开关，不是原生 checkbox

`角色标签` / `网格吸附` / `高斯地面吸附` 均为整宽 `button` **280×56**，
`background: transparent`、`justify-content: space-between`、
`align-items: center`，内含标签 span + 轨道 + 旋钮：

- 轨道 **24×14**，`border-radius: 9999px`（全圆角）
  - 开 `rgb(255,255,255)`；关 `rgba(255,255,255,0.18)`
- 旋钮 **10×10**
  - 开 `rgb(31,31,31)` 居右（轨道 x+12）；关居左（轨道 x+2）

`地面` 用同一构造但为 **240×15**（嵌套行，非整宽）。

> 注：`显示地面` / `显示网格`（`showGround` / `showGrid`）是另外两行，
> 源站未采到其自绘形态，clone 保持原生 checkbox 不动。

### 3. 左侧搜索框

`placeholder="请输入搜索内容"`（216×32，无 `aria-label`）。此前 clone 写的是
「搜索场景内容」。「搜索场景对象」是另一个 1×1 `<span>` 的无障碍标签，
与 placeholder **不是同一串**。

## clone 合同（CLONE_DECISION）

- 新增 `NumericReadoutInput`：可编辑文本框，镜像 store 值
  （`useEffect` 随外部变更同步），失焦回滚到上一个合法值；
- 五处读数接入，格式逐字对齐；提交时按各自 range 的 min/max 钳制；
  场景缩放读数是百分比，提交时 `/100` 换回 store 的倍数；
- 新增 `SceneToggleRow`：`role="switch"` 的整宽 button + 24×14 轨道 +
  10×10 旋钮，保留既有 `data-director-scene-*` 属性名（batch 550 断言
  `data-director-scene-snap-to-grid`），另加统一的
  `data-director-scene-toggle-on` 状态标记；
- 搜索框 placeholder 改为「请输入搜索内容」，`aria-label` 保留（a11y 超集）；
- hex 框加 `maxLength={6}` 与 `uppercase` **类**（非值转换——按值转大写会与
  585 已固化的 store 小写约定互相打架，第一次实现就是这么撞的，已回退）。

### 未取证、刻意不臆造的部分

- **读数提交语义**：源站是否失焦提交、如何钳制，未实测（改源站数值会写入
  用户真实项目）。本批复用 585 已在**兄弟行**（天空颜色 hex）实测通过的
  提交模式，不另造规则。
- **球形半径默认值**：实测值 60，但该项目可能已被用户改过，源站默认值不可考，
  clone 保持自己的 30（batch 555 的 `defaults:radius` 合同不变）。

## 断言迁移（合同演进，沿既有先例）

读数从 `<span>` 变成 `<input>` 后，**`input.value` 不参与 `innerText`**，
三处基于 `inner_text()` 的读数断言同时失效：

| 文件 | 处置 |
|---|---|
| `verify-liblib-batch582.py` | `scale:percent-readout` / `opacity:readout` 改为读文本框值（24 → 26 检查） |
| `verify-liblib-batch555.py` | `radius:label-updates` 改读文本框值；另有一处**582 遗留失败**：555 设半径 55，但 582 已对齐源站为 `step 10`，range 值净化吸附到 60，原断言自 582 起即失效——改用步进对齐的 60（5 → 7 检查） |
| `verify-liblib-batch566.py` | `height:label` 改读文本框值 |
| `verify-liblib-batch550.py` | **无需迁移**（只点 `[data-director-scene-snap-to-grid]`，属性名已保留） |

## 内容

- `src/components/director/DirectorInspector.tsx`（`SceneToggleRow`、
  `NumericReadoutInput`、五处读数、三处开关、hex `maxLength`+`uppercase`）
- `src/components/director/DirectorObjectTree.tsx`（搜索框 placeholder）
- `scripts/verify-liblib-batch588.py`（52 检查，新）
- `scripts/verify-liblib-batch582.py` / `555.py` / `566.py`（断言迁移）

## 回归与门禁

- 回归：588（52）/ 585（24）/ 584（113）/ 583（24）/ 582（26）/ 566（6）/
  555（7）/ 550（5）/ 548（10）/ 89 全绿；
- `tsc --noEmit` 净；`eslint` 0 error；`verify-docs.py` ✓；`next build` ✓。

## 待后续批次

- 读数提交语义与钳制规则需在源站实测（要改用户真实项目的数值，需先授权）；
- 球形半径源站默认值（需新建场景才能测）；
- `显示地面` / `显示网格` 两行是否也是自绘开关（源站未采到）；
- `地面` 行 240×15 自绘开关的完整形态（含其下 透明度/高度 子行的归属）；
- 顶栏收起按钮位置：源站在 280px 宽左列 header 的右缘（x=240），clone 顶栏
  整窗宽，按钮落在标题旁；
- `directorPmx*` 触发条件。
