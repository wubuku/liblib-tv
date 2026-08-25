# Batch 10 Screenshot Analysis

> 识图日期：2026-08-25
> 用途：固化五种 clone 图片编辑器状态的视觉结果。后续先读本文和结构化测试，不重复打开这些整图。

## 1. 证据集合

来源：本地 clone，viewport `929x874`，整理后约 `28%`。

```text
docs/design-references/liblib-clone-batch10-male-929-2026-08-25.png
docs/design-references/liblib-clone-batch10-female-929-2026-08-25.png
docs/design-references/liblib-clone-batch10-coffee-929-2026-08-25.png
docs/design-references/liblib-clone-batch10-cafe-929-2026-08-25.png
docs/design-references/liblib-clone-batch10-storyboard-929-2026-08-25.png
docs/design-references/liblib-clone-batch10-image-editor-state-matrix-2026-08-25.png
```

联系表由专项脚本从五张完整页面截图按 DOM panel 矩形裁切并组合为 `1320x912`。当 panel 超出 viewport 时，联系表中的黑色留白代表不可见区域，不是 panel 自身的空白或黑色填充。

## 2. 联系表识图

### 男性 / 女性

- 两个 panel 都是紧凑 `191px` 状态；
- Prompt 区显示原站 placeholder；
- footer 为模型、参数、设置、翻译、撤销和禁用提交；
- 没有 AutoLink 图标，因为 Prompt 为空；
- panel 左侧随节点锚点自然超出 viewport，顶部入口和 footer 左端在截图中被裁切。

### 咖啡

- panel 为 `211px`；
- 602 字 Prompt 多行铺满主体区域，并在固定高度中滚动/裁切；
- footer 右侧能看到 AutoLink、翻译、撤销和可用提交按钮；
- 没有“参考”顶部入口，也没有 references；
- 联系表左侧黑色区域来自 viewport 裁切。

### 咖啡馆

- panel 为 `191px`，证明有 Prompt 不必自动扩展到 `211px`；
- 7 字 Prompt 位于 panel 左侧，但节点锚定导致该区域超出当前 viewport，所以截图中主体看起来近似空白；
- 完整页面截图直接显示 panel 固定在左侧节点下方，未被夹回 viewport；
- footer 有 AutoLink 图标和可用提交按钮。

### 分镜 #2

- panel 为 `274px`；
- 顶部可见“参考 / 标记 / 风格”三个 `54x26` 入口；
- 两张参考图为 `47x47`，带编号；
- 204 字 Prompt 完整进入多行主体；
- footer 可见链形 model 图标、矩形 settings 图标和 `32px` 操作控件；
- 不再出现 `⌘` / `▭` 字符。

## 3. DOM 支持

专项脚本自动测量并确认：

```text
panel width = 660
panel heights = 191 / 191 / 211 / 191 / 274
top controls = 54x26
references = 47x47
model/settings/footer icon controls = 32px high
```

Prompt、placeholder、references、顶部入口和 generation settings 均直接与原站 JSON 对比，不依赖截图文字识别。

## 4. 证据边界

- **截图直接事实**：五种相对高度、Prompt 密度、参考图结构、footer 图标化、自然裁切和整体层级。
- **DOM/测试事实**：精确尺寸、完整 Prompt、placeholder、入口集合和 AutoLink 接受后的状态变化。
- **clone 决策**：AutoLink footer 入口与候选弹层；Lucide 图标替代原站未提取 SVG。
- **未确认**：原站 footer 每个 SVG 的逐路径形状、tooltip 文案、AutoLink 弹层精确位置与动画。

## 5. 复用规则

后续涉及以下问题时先读本文，不重复识图：

- 五个图片节点的 panel 高度和内容密度；
- `咖啡馆` 为什么有 Prompt 仍为 `191px`；
- 左侧 panel 为什么在截图中缺少左半内容；
- footer 是否仍出现脑补字符；
- 分镜 references 的尺寸和排列。

只有取得原站 footer SVG、AutoLink 弹层新状态或原站 UI 更新时，才需要新的最小区域截图。

