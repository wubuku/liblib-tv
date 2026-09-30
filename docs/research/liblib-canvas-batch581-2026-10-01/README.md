# Batch 581 — 摄像机属性面板对齐 2026-10-01 源站实测

> 状态：`SCRIPT_RECORDED_PASS`（27 检查）。源站证据：**2026-10-01 实时 CDP
> 采样**（本批首次打通源站导演台，见下「入口突破」），非历史截图。

## 入口突破：导演台浮层常驻 DOM

- 画布节点「导演台 2」的 `打开导演台` 按钮**点击无响应**（button 未禁用、
  `data-practice-anchor="director.open"`、JS click 与原生 click 均不触发
  路由变化，`window.open` 未被调用，`history.pushState` 无记录）——此前
  多个批次把「源站导演台进不去」记为 BLOCKED_SOURCE。
- 本批换了个思路：不去点按钮，而是**在页面里找导演台本身**。结果它一直
  在：全屏浮层 `div.relative.min-h-0.flex-1.overflow-hidden`（1920×880，
  内含 2 个 canvas），锚点文本 `3D导演台`（HEADER）+ `导演视角` 按钮 +
  `请将图片节点连接到导演台左侧输入口`。
- 此前漏判的原因：探针只看 `document.body.innerText` 前 300 字符，而画布
  节点文本排在导演台浮层文本之前；`[class*=director]` 选择器也匹配不到。
  **教训：判断"某个源站界面是否存在"应按特征锚点（HEADER + canvas 数量 +
  唯一文本）检索，而不是按 body 文本前缀或 class 猜测。**

## 源站实测结构（SOURCE_FACT，2026-10-01，机位1 / 属性页）

按 y 坐标排序的右栏行序：

| y | 行 | 内容 |
|---|---|---|
| 68 | 页签 | `属性`（选中） `截图` —— **仅两个** |
| 134 | FOV | `FOV 50°`（滑杆 + 度数读数，紧贴页签栏下方） |
| 289 | 名称 | 输入 `机位1` |
| 361 | 切换机位 | 下拉 |
| 433 / 465 | 位置 | `X 3.3` `Y 2.2` `Z 10`（step 0.1） |
| 505 | 跟随目标 | `不跟随` / `角色A` |
| 577 / 609 | 旋转 | `X 5.42` `Y -161.74` `Z 0`（step 1） |
| 649 | 注视目标 | `手动坐标` / `手动旋转` / `角色A` |
| 721 / 753 | 注视坐标 | `X 0` `Y 1.2` `Z 0` |
| 814 / 816 | 视野角度 (FOV) | `?` 开关 + 说明文案 |
| 903 | 相机截图 | 分组标题 |

- FOV 原生 range 实测属性：`min=15 max=90 step=1 value=50`，且该 input 是
  `absolute inset-x-0 … opacity-0`——源站滑杆是**自绘轨道 + 透明原生
  range 叠加**，因此"从截图量滑块位置推量程"不可靠（batch 580 的 0–10
  推断据此标注为待复核）。
- 说明文案逐字：
  「控制镜头视野范围。数值越小，画面越近、越聚焦；数值越大，画面越广、能看到更多环境。」

## 源站新鲜度发现（FRESHNESS）

- **「运动轨迹」页签当前不渲染**：摄像机面板只有 `属性 | 截图`；但站点
  仍下发该功能的 i18n 键（`directorTabMotionPath` = 运动轨迹，
  `directorTabAttr` / `directorTabPose` / `directorTabAction` 同组），以及
  `directorDrawTrajectory`（绘制轨迹）、`directorCreateMotionTrajectory`
  （创建运动轨迹）、`directorMotionPath*` 一整套键。batch 563/576/580 依据
  的 2026-09-25 截图 64 确实存在该页签（带 NEW 徽标）。
- 判定：该页签是**条件渲染**（NEW 灰度/需存在运动轨迹才出现），当前账号
  场景下不满足条件。**不据此删除 clone 的该页签**——9-25 有截图证据，
  条件未知，删除会丢失已验收能力。改为在本文件与下批 freshness 记录中
  显式标注。
- 附带澄清：`directorPropUniformScale`（统一缩放）与
  `directorPropPosition/Rotation/Scale/Color` 同属 `directorProp*` 属性键
  组，说明统一缩放是**属性行组件**，在「运动轨迹」页签的关键帧字段组里
  复用（截图 64 可见），而不是该页签独有——batch 580 的位置无冲突。

## clone 合同（CLONE_DECISION）

1. **页签栅格修正**：三个页签此前挤在 `grid-cols-2`，第三个换行导致页签栏
   占两行（实测 属性 y=136 / 截图 y=153）。改为 `grid-cols-3` 单行等宽。
2. **FOV 上提 + 量程对齐**：`CameraFovField` 提到面板顶部（名称之上），
   形态改为源站的 `FOV` 标签 + `{n}°` 读数同行、滑杆在下；量程
   `20–90` → **`15–90`**（源站 DOM 实测）。
3. **字段序对齐**：把「跟随目标」选择器上提到变换组内、紧随「位置」
   （源站 y=505 位于位置 465 与旋转 609 之间）。clone 独有的「缩放」「当前
   镜头 / 镜头名称 / 开始 / 结束」保留在原处不动——源站属性页无缩放行，
   但缩放在「运动轨迹」页签可达（截图 64），且多个既有 verifier 依赖它。
4. **FOV 帮助块**：面板底部新增 `视野角度 (FOV)` + `?` 开关 + 源站文案，
   默认收起。
5. 「跟随偏移 / 跟随视角 / 跟随状态 span」等 clone 独有块原样保留。

## 内容

- `src/components/director/DirectorInspector.tsx`
  （页签 `grid-cols-3`；`CameraFovField` 上提 + 量程 + 读数；新增
  `CameraFovHelp`；跟随目标选择器上移）；
- `scripts/verify-liblib-batch581.py`（27 检查）；
- `scripts/verify-liblib-batch89.py` / `verify-liblib-batch96.py`
  ——**既有失败的最小解除阻塞**：两者在**未改动的已提交代码**上同样失败
  （89 报 2 条、96 报 1 条 `TransformControls: The attached 3D object must
  be a part of the scene graph.`），基线对照确认与本批无关；按 batch
  36/553/558/580 既有约定显式过滤该已知瞬态，并在 audit 里保留
  `details` / `filteredTransformControls` 痕迹。

## 回归与门禁

- 回归：580（29）/ 575（4）/ 563（17）/ 36 全绿；89、96 经上述最小修复后
  全绿；
- `tsc --noEmit` 净；`eslint` 0 error；`next build` ✓；`verify-docs.py` ✓。

## 待后续批次

- 在源站创建运动轨迹（绘制轨迹/创建运动轨迹）后复核「运动轨迹」页签的
  出现条件与 NEW 徽标去留；
- 统一缩放滑杆真实量程复核（需该页签可进入）；
- 源站滑杆的"自绘轨道 + 透明原生 range"实现是否要在 clone 全面套用
  （batch 580 的渐变实现是近似，视觉已接近但 thumb 仍为原生渲染）。
