# LibTV 图片节点双浮层几何矩阵

> 定位：`LIBTV-UIX-01` 的当前源站证据与 clone 差异基线。Open Canvas 只提供研究方法；本文件中的像素、动作和裁剪结论均以 LibTV 登录态源站为准。

## 1. 结论先行

当前 clone 的主要剩余问题已经不应描述为“上下浮层都没有正确锚定”：现有结构与源站的核心几何合同一致，但顶部工具条仍冻结在 2026-08-25 的旧动作集合。

- 五个现有图片节点的顶部工具条都与节点水平居中，底部编辑面板也都与节点水平居中；最大中心误差小于 `0.01px`。
- 顶部工具条与节点之间约 `16.68px`，属于屏幕空间间距；底部面板与节点之间为 `16 * zoom = 4.450px`，属于节点内 flow-space 偏移经 viewport 缩放后的结果。
- 底部面板固定为 `660px` 屏幕宽度，高度由内容态决定为 `191 / 211 / 273.797px`。
- 源站不做 viewport clamp。左边缘出现负 x、顶部出现负 y、底部超出 viewport 都是当前可见行为。
- 2026-08-25 的源站工具条是 `900.5x49`，包含 7 个文字动作和 4 个图标动作；2026-08-26 同一画布、同一批节点统一变为 `1092.5x49`，包含 9 个文字动作和 4 个图标动作。
- 这次宽度增加不是节点内容态差异，而是源站动作集合更新：新增 `元素编辑` 和 `图层分离`，两个按钮各 `88px`，加上两个 `8px` 间距，合计正好增加 `192px`。
- 当前 clone 仍硬编码 `900.5px`，缺少这两个文字动作，并用 `撤销 / 重做` 两个图标按钮替代了源站的 `标注 / 旋转 / 下载 / 预览` 四个工具。六动作的静态状态链和安全 live 复测已继续落入 [`LIBTV_IMAGE_ACTION_MATRIX.md`](LIBTV_IMAGE_ACTION_MATRIX.md)；实现前不应继续凭感觉调整上下 offset。

原始结构化记录见 [`libtv-image-overlay-audit-2026-08-26.json`](../liblib-seedance-2.5-2026-08-25/libtv-image-overlay-audit-2026-08-26.json)。历史 `900.5px` 数据见 [`image-node-state-audit.json`](../liblib-live-2026-08-25/image-node-state-audit.json)。

## 2. 取证范围

| 项目 | 值 |
|---|---|
| 源站 | `https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd` |
| 操作 | 只读 DOM、空白点击、依次单选五个现有图片节点 |
| 未执行 | 上传、生成、参数修改、新建节点、删除、远端写入 |
| viewport | `929x874` CSS px |
| device pixel ratio | `2` |
| React Flow transform | `matrix(0.278112, 0, 0, 0.278112, 17.9639, 131.434)` |
| 观察日期 | 2026-08-26 |

本轮先点击画布空白清除旧选择，再点击目标节点。这样可以避免前一个节点的宽工具条覆盖后一个节点，导致点击实际命中工具条而不是节点。

## 3. 五节点矩阵

所有坐标均为浏览器 CSS px。`T gap` 是工具条底部到节点顶部，`P gap` 是节点底部到编辑面板顶部。

| 节点 | Node rect `(x,y,w,h)` | Toolbar rect `(x,y,w,h)` | Panel rect `(x,y,w,h)` | T gap | P gap | 内容态 |
|---|---|---|---|---:|---:|---|
| `image_2026-06-15T11-22-00` | `54.675,207.358,171.873,97.339` | `-405.641,141.680,1092.5,49` | `-189.389,309.148,660,191` | `16.678` | `4.450` | 空 Prompt，`16:9 / 标准 / 2K` |
| `咖啡` | `131.990,501.880,194.679,97.339` | `-316.922,436.203,1092.5,49` | `-100.671,603.669,660,211` | `16.677` | `4.450` | 长 Prompt，`2:1 / 低 / 1K` |
| `image_2026-06-15T11-22-15` | `131.990,390.635,171.874,97.339` | `-328.328,324.953,1092.5,49` | `-112.073,492.424,660,191` | `16.682` | `4.450` | 空 Prompt，`16:9 / 标准 / 2K` |
| `图片4` | `131.990,613.124,194.679,97.339` | `-316.922,547.445,1092.5,49` | `-100.671,714.914,660,191` | `16.679` | `4.450` | 短 Prompt，`2:1 / 低 / 1K` |
| `分镜 #2` | `457.382,48.000,172.986,97.339` | `-2.383,-17.680,1092.5,49` | `213.874,149.789,660,273.797` | `16.680` | `4.450` | 两个引用、长 Prompt，`16:9 / 低 / 1K` |

中心误差矩阵：

| 节点 | Toolbar center - node center | Panel center - node center |
|---|---:|---:|
| `image_2026-06-15T11-22-00` | `-0.002px` | `0px` |
| `咖啡` | `-0.001px` | `0px` |
| `image_2026-06-15T11-22-15` | `-0.005px` | `0px` |
| `图片4` | `-0.001px` | `0px` |
| `分镜 #2` | `-0.008px` | `-0.001px` |

这组数据把定位合同收敛为两条不同的转换链：

```text
top toolbar:
  node screen center/top
  -> React Flow NodeToolbar
  -> screen-space offset about 16px
  -> content-sized, unscaled toolbar

bottom editor:
  node-local left 50% / bottom -16 flow units
  -> translate(-50%, 100%)
  -> inverse scale(1 / viewport zoom)
  -> 660px unscaled panel, gap 16 * zoom
```

两个层共享 node center，但不共享 containing block，也不共享纵向 gap 的坐标空间。

## 4. 工具条时间版本差异

### 4.1 2026-08-25 基线

历史 DOM 审计覆盖同一批五个图片节点。工具条统一为 `900.5x49`，文字动作顺序为：

```text
人像质感调节 / 全景 / 多角度 / 打光 / 九宫格 / 高清 / 宫格切分
```

后面还有 4 个无文字图标按钮。历史记录没有保存它们的 test id，因此不能仅凭旧 JSON 反推语义。

### 4.2 2026-08-26 当前基线

当前五节点工具条统一为 `1092.5x49`，DOM 外层类包含 `w-fit`。13 个按钮按顺序为：

| 顺序 | test id | 文案/语义 | 宽度 |
|---:|---|---|---:|
| 1 | `image-toolbar-portrait-texture` | 人像质感调节 / NEW | `178px` |
| 2 | `image-toolbar-panorama-slash` | 全景 | `62px` |
| 3 | `image-toolbar-angle` | 多角度 | `75px` |
| 4 | `image-toolbar-light` | 打光 | `62px` |
| 5 | `image-toolbar-nine-grid` | 九宫格 | `91px` |
| 6 | `image-editor-primary-tool-trigger` | 高清 | `78px` |
| 7 | `image-toolbar-interactive-edit` | 元素编辑 | `88px` |
| 8 | `image-toolbar-layer-separation` | 图层分离 | `88px` |
| 9 | `image-toolbar-grid-split` | 宫格切分 | `104px` |
| 10 | `image-toolbar-annotate` | 标注图标 | `32px` |
| 11 | `image-toolbar-rotate` | 旋转图标 | `32px` |
| 12 | `image-toolbar-download` | 下载图标 | `32px` |
| 13 | `image-toolbar-preview` | 预览图标 | `32px` |

`1092.5 - 900.5 = 192`，正好等于 `88 + 8 + 88 + 8`。因此本轮可以将“宽度差异”从未归因状态提升为高置信推断：源站在两次审计之间增加了两个文字动作，并继续按内容自适应宽度；没有证据表明图片内容态本身切换了工具条宽度。

## 5. 当前 clone 差异

| 合同 | 当前源站 | 当前 clone 静态实现 | 判断 | 优先级 |
|---|---|---|---|---|
| 顶部 anchor | NodeToolbar、节点中心、上方约 16px | `NodeToolbar position=Top align=center offset=16` | 结构一致 | 保持 |
| 底部 anchor | 节点内、中心、inverse zoom、`16 * zoom` gap | 节点内 `left-1/2`、`-bottom-[17px]`、`scale(1/zoom)` | 结构一致，17px 是边框补偿 | 保持 |
| 边缘策略 | 不 clamp，允许负 x/y 和裁切 | 当前规格与实现允许裁切 | 一致 | 保持 |
| Panel width/height | `660px`；`191/211/273.797` 内容态 | `660px`；初始节点为 `191/211/274` | 可接受的像素取整 | P2 视觉复核 |
| Toolbar sizing | `w-fit`，当前 `1092.5px` | 固定 `w-[900.5px]` | 冻结在旧版本 | P0 |
| 文字动作 | 9 个 | 7 个 | 缺 `元素编辑 / 图层分离` | P0 |
| 末端工具 | 标注、旋转、下载、预览，共 4 个 | 撤销、重做，共 2 个 | 语义与数量均不一致 | P0 取证 / P1 实施 |
| 动作副作用 | 新动作尚未安全实测 | 多数旧动作创建本地派生节点 | clone-only 行为不能冒充源站 | P0 取证 |
| 单选生命周期 | 单选显示；空白点击卸载 | `selected && selectedNodeCount <= 1` | 静态结构一致 | P1 runtime 回归 |

代码证据：[`ImageToolbar.tsx`](../../../src/components/ImageToolbar.tsx#L16)、[`ImageNode.tsx`](../../../src/components/nodes/ImageNode.tsx#L34)、[`ImageEditPanel.tsx`](../../../src/components/ImageEditPanel.tsx#L101)。

## 6. 事实、推断与 clone 决策

### `SOURCE_FACT`

- 当前五个图片节点共享相同的 13 按钮工具条和 `1092.5x49` 外框。
- 工具条和编辑面板均以节点中心为水平 anchor。
- 顶部和底部使用不同纵向坐标合同。
- 面板宽度固定、内容高度显式变化，边缘不 clamp。
- 2026-08-25 的结构化源站记录确实是 7 个文字动作、4 个图标动作和 `900.5x49`。

### `INFERENCE`

- `900.5 -> 1092.5` 是源站部署后的动作集合扩展，而不是图片节点内容态差异。
- 当前 clone 的上下 anchor 结构已经接近源站，用户感知的“不准确”至少有一部分来自工具条内容和宽度版本落后，而不只是 offset。
- 源站使用 `w-fit` 表明宽度应由动作集合决定，不应把某次测量值永久视为全局常量。

### `CLONE_DECISION`（待授权）

- 保留 React Flow `NodeToolbar` 和节点内 inverse-scale editor 两条现有定位链。
- 以当前动作集合更新 toolbar contract，并让宽度由内容决定；回归仍检查当前快照应测得约 `1092.5px`。
- 在未确认源站副作用前，只能先复刻新动作入口和 disabled/prototype 边界，不能猜测生成节点或远端任务行为。
- 末端四个图标动作需要逐项取证后再替换 clone-only 的撤销/重做。
- 不新增 viewport clamp、自动避让、页面居中或碰撞修正。

## 7. 后续批次

| 批次 | 研究问题 | 交付物 | 停止条件 |
|---|---|---|---|
| `UIX-01A` | 28% 下多节点几何 | 本文件与 JSON | 已完成 |
| `UIX-01B` | 53% / 100% 下是否保持 `1092.5x49`、`660px` | 多 zoom rect 表 | 不拖动或改写远端节点 |
| `UIX-01C` | 新增两个文字动作和四个图标动作打开什么 UI | [`LIBTV_IMAGE_ACTION_MATRIX.md`](LIBTV_IMAGE_ACTION_MATRIX.md)；preview/空 annotate live，其余 bundle | 图层分离等任务动作保持未点击 |
| `UIX-01D` | 选择切换、空白点击、拖动/平移的卸载与跟随时序 | 连续 DOM rect/状态记录 | 不改变远端画布数据 |
| `UIX-01E` | clone runtime 当前值与源站同场景对照 | source/clone 双列矩阵 | 等用户授权代码前仍可只读运行 |

就绪视频顶部工具条仍是独立证据缺口。当前画布只有失败视频，不能把图片工具条的尺寸或动作集合外推到 ready-video 状态。
