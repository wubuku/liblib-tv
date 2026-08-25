# Batch 22 Screenshot Analysis

## 1. 原站模型菜单聚焦审计

### 文件

- 原图：`docs/design-references/liblib-original-seedance-model-menu-2026-08-25.png`
- 聚焦 crop：原图 `x=440..870, y=90..550`，临时文件不入库
- 来源：LibTV 登录态画布
- 采样日期：2026-08-25
- viewport：`929x874`
- 聚焦识图次数：1

Batch 21 已通过四图 contact sheet 识别过菜单上下文；本次只为确认 model popover 自身边界、行层级和选中文案而查看最小 crop。

### Source fact

- 可见顺序：
  1. Seedance 2.5 — `2min`
  2. Seedance 2.0 VIP — `2min`
  3. Minimax H3 — `2min`
  4. Seedance 2.0 Fast VIP — `2min`
  5. Seedance 2.0 Mini — `2min`
  6. Wan 3.0 Prime — `1min`
  7. Wan 3.0 — `3min`
- 前五项 title 后有 gold diamond。
- Wan 两项没有 diamond。
- `Seedance 2.0 Fast VIP` 是 selected row：
  - surface 和 border 比其他行更亮；
  - row 高度更高；
  - 第二行显示 `最强视频模型快速版，会员专属通道，15s音画同步`。
- 非选中项只显示 model icon、title、premium 和 estimate，不显示 description。
- 每项左侧有深灰圆角 model icon tile，estimate 是右侧 pill。

### Pixel-backed inference

- 外框约：`x≈458, y≈126, w≈380, h≈410`。
- source generation panel rect 为 `x=459.304, y=302.671, w=660, h=273.797`。
- 因此 model menu 约为：
  - relative left `≈0`
  - relative top `≈-176.7`
- menu bottom 约贴合 footer trigger top。

这些是 JPEG 边缘和 crop 的像素反推，不是 source DOM rect。

### Unknown

- 截图下边界不能证明七项就是完整模型库。
- 只确认了 2.5 与 Fast 的 description；其他模型的说明不补写。
- model logo 与 premium 的原始 SVG path 未提取。
- hover/scroll/keyboard navigation 未采样。

## 2. 当前 clone DOM 审计

- generation panel：`x=453.939, y=304.897, w=660, h=274`
- model menu：`x=462.939, y=313.772, w=330, h=216.625`
- relative：`left +9`, `top +8.875`
- 四个 row 均约 `50.656px`，全部显示 description。
- 当前列表：Seedance 2.5、Seedance 2.0 VIP、Minimax H3、Kling O3。

## 3. Gap conclusion

- menu 没有向上展开，反而大部分落在 generation panel 内。
- 高度约少 `193px`，宽度约少 `50px`。
- 三个 source-visible 模型分支缺失，并存在一个无本批证据的 Kling 项。
- 所有行同时展开说明，破坏 source 的扫描层级。

## 4. Re-inspection rule

实施前不再打开该截图。后续优先使用本文；只有完整模型库、其他 description、精确 SVG 或键盘/滚动行为进入范围时才重新采样。

## 5. Clone 验证截图

### 文件

- `docs/design-references/liblib-clone-batch22-model-menu-default-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch22-model-menu-fast-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch22-model-menu-mobile-390-2026-08-25.png`
- `docs/design-references/liblib-clone-batch22-model-menu-contact-sheet-2026-08-25.png`
- 来源：本地 clone
- 采样日期：2026-08-25
- viewport：desktop `929x874`；mobile `390x844`
- contact sheet 识图次数：1

### Clone screenshot fact

- 固定高度菜单内完整显示七个 source-visible row，没有底部裁切。
- 每行右侧 estimate pill 形成稳定列；前五行 premium icon 与 title 对齐，Wan 两行没有 premium icon。
- 默认截图只展开 `Seedance 2.5` 的说明；Fast 截图只展开 `Seedance 2.0 Fast VIP` 的说明。
- 两种 selected state 都有可辨识的加亮 surface 和 border，其他行保持紧凑。
- mobile 截图中菜单与 generation panel 左边缘对齐，`380px` 菜单完整落在 `390px` viewport 内。
- 未见 title、estimate、premium icon 或 description 互相覆盖，也未见菜单与 viewport 产生水平溢出。

### DOM-backed geometry

专项脚本测得：

- menu：`380x410`
- desktop menu relative to generation panel：`left 0px`、`top -176.7px`
- selected row：`58px`
- compact row：`48px`
- premium count：`5`

### Remaining fidelity boundary

- model tile 和 premium 仍使用 clone icon 近似，不代表原站 SVG path 已复刻。
- 本组截图只验证 source-visible 七项及两个已确认 description，不扩大为完整模型库证据。
