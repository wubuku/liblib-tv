# LibTV 图片工具条动作状态矩阵

> 定位：补全 [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](LIBTV_OVERLAY_GEOMETRY_MATRIX.md) 中 `UIX-01C` 的动作语义证据。本文只描述当前 LibTV 源站“有什么、怎么呈现、何时可能产生副作用”；不代表已授权修改 clone 代码。

## 1. 研究边界

本轮使用两种只读证据：

1. 从当前登录态页面的 182 个 `<script>` 中筛出 128 个 LibTV Next.js chunks，搜索 6 个当前图片工具条 test id；
2. 只现场打开静态处理路径能够证明不会提交任务的 `预览`、空绘制 `标注` 和空态 `元素编辑`，读取 DOM 后立即关闭；另对 `旋转` 做了一次入口观察，并立即撤销其产生的派生节点。

唯一命中全部 test id 的当前 chunk 为：

```text
https://liblibai-web-static.liblib.cloud/liblibtv_online/static/_next/static/chunks/15epcn_e-6pl6.js
length = 1,563,088 bytes
```

未点击 `图层分离 / 下载`，未绘制标注，未点击保存，未上传或生成。`元素编辑` 只进入空态后用 Escape 退出；`旋转` 的一次 live 点击产生了一个名为“旋转与镜像”的派生节点，随后用一次撤销恢复。bundle 中的 minified 标识符只用于还原状态链，本文不保存大段上游代码。

## 2. 总体状态模型

当前图片工具条不是一组彼此独立的“创建派生节点”按钮。至少存在三类状态转换：

```text
selected image + standard toolbar + bottom generation panel
  ├── preview
  │     -> page-level MediaPreviewOverlay
  │     -> close returns to unchanged selected state
  ├── local editing tool
  │     -> replace standard toolbar with tool-specific toolbar
  │     -> hide bottom generation panel
  │     -> overlay editor/canvas on the image node
  │     -> escape / discard / save
  └── generation-backed editing tool
        -> local authoring state
        -> explicit or tool-triggered task submission
        -> patch current node or create/reuse output node
```

这条状态机直接否定当前 clone 的通用假设：`onAction -> addDerivedNode` 不是图片工具条的共同语义。

## 3. 六动作矩阵

| 动作 | 入口处理 | 打开后的主 UI | 潜在写入/任务 | 本轮 live | 风险 |
|---|---|---|---|---|---|
| 元素编辑 | 上报 `图片编辑`，设置 `ElementTool.EditElements` | `InteractiveImageEditMode`，点选/框选/画笔工具 | 点击生成后创建或复用输出节点，并通过 task gateway 提交 | 已验证空态 | 中：空态进入可退出；提交为高 |
| 图层分离 | 上报 `图层分离`，设置 `ElementTool.LayerSeparation` | `layer-composition-editor`，图层移动/缩放/旋转/翻转/重绘 | bundle 含 `submitGenerationTask`、任务轮询和 composition patch；进入后的初始化是否立即提交需保守处理 | 未点击 | 高 |
| 标注 | toggle `ElementTool.Annotate` | 节点 canvas + 专用 8 按钮工具条 + 保存 | 空态无写入；保存语义未执行 | 已验证空态 | 低到中 |
| 旋转 | 有图片时上报并设置 `ElementTool.RotateOrMirror`，外层可能先执行进入回调 | bundle 描述本地旋转/镜像编辑；退出脏状态出现保存/丢弃 modal | 当前 fixture 的 live 点击实际产生了“旋转与镜像”派生节点；保存还可能上传旋转结果并更新当前节点 | 已点击后撤销 | 高：入口已证明可改变 graph，禁止在共享画布继续试探 |
| 下载 | 调用专用 download callback | 水印偏好检查、下载提示 | 可能请求带/不带水印 URL，触发浏览器下载并上报 output success | 未点击 | 中 |
| 预览 | 将 preview state 设为 true | page-level `MediaPreviewOverlay` | 只读查看；关闭设回 false | 已验证 | 低 |

### 3.1 元素编辑

bundle 事实：

- 点击入口后设置 `ElementTool.EditElements`，并通知外层当前 tool 变化；
- `InteractiveImageEditMode` mount 时打开 session，unmount 时关闭 session；
- 顶部专用工具条固定 `h-11 w-fit`，含关闭入口、point、box、brush 和画笔尺寸；
- session 支持 undo/redo；只有存在有效 edit records 时生成按钮才可用；
- 提交时创建或复用名为 `源图名称--元素编辑` 的输出节点，`showGenerator=false`、`selectNewNode=false`，随后通过 task gateway 执行。

这说明“元素编辑”首先是节点内 authoring mode，生成结果才进入 graph mutation；clone 不能把入口点击直接实现为一张已完成派生图。

本轮空态 live 几何（zoom `0.407229`，节点 `i-1FQ9tErTcC`）：

| 元素 | Rect / 值 |
|---|---|
| 专用工具条 | `x=-142.852, y=89.734, w=272, h=44` |
| 工具条中心 | `-6.852`，与节点中心约 `-6.853` 对齐 |
| mode root | `x=-132.273, y=185.734, w=250.852, h=203.711` |
| edit stage | `x=-131.961, y=185.734, w=250.211, h=141.711` |
| initial mask / guide | stage 全覆盖；guide 文案为 `标记你想要修改的对象` |
| record panel | `x=-206.844, y=339.445, w=400, h=50`，文案为 `编辑内容待添加` |
| 标准 bottom generation panel | 不存在 |

工具条按钮为关闭、点选、框选、画笔和撤销；空态下撤销 disabled。Escape 后专用 mode、toolbar 和 stage 均卸载，标准 `1092.5x49` toolbar 与 `660x191` generation panel 恢复。该次操作没有绘制、生成、上传或保存。

### 3.2 图层分离

bundle 事实：

- 点击入口设置 `ElementTool.LayerSeparation`；
- 专用 `layer-composition-editor` 可选择非背景图层，移动、缩放、旋转、翻转、隐藏和下载单层；
- 快捷键作用域包含 `mod+d` 复制图层、Delete/Backspace 删除图层；
- composition 有 `splitting / failed / ready / redrawing / merging` 等状态；
- 分离和重绘链路包含 task submit、task id、停止任务、失败回写和节点数据 patch。

由于 active tool 的 effect 中存在根据初始化状态继续执行 split 的路径，本轮没有点击。后续 live 取证必须使用可丢弃副本或明确获准的测试节点，不能在当前研究画布上试探。

### 3.3 标注 live 状态

在 `图片4` 节点上进入空标注态：

| 元素 | Rect / 值 |
|---|---|
| selected node | `131.990,613.124,194.679,97.339` |
| 专用工具条 | `-38.680,554.398,536,49` |
| 工具条中心误差 | `-0.009px` |
| 工具条到节点 gap | `9.726px` |
| 可见按钮 | 8 个，文字为 `标注 / 保存`，undo/redo 初始 disabled |
| 绘制 canvas CSS rect | `132.266,613.398,194.117,97` |
| canvas backing size | `388x194`，对应 device pixel ratio `2` |
| 标准底部生成面板 | 不存在 |

进入标注态时，标准 `1092.5x49` 工具条被 `536x49` 专用工具条替换，底部 `660px` 生成面板卸载。按 Escape 后 canvas 和专用工具条消失，标准工具条与底部面板恢复；没有绘制或保存。

这说明双浮层合同必须包含 `editingImageTool` 状态分支：标准选中态和工具编辑态不是把第三个浮层叠上去，而是替换 toolbar、隐藏 generation panel、把编辑 surface 投影到节点本体。

### 3.4 旋转与镜像

bundle 事实：

- 入口只在已有图片或等价 source 时生效；
- 编辑态维护角度、水平翻转、垂直翻转和 natural size；
- 无修改退出可直接关闭；有修改退出会显示 modal，提供 `丢弃更改` 和 `保存`；
- 保存路径 `applyRotateLocal` 可能上传转换结果，再更新当前节点 data 或创建输出节点。

因此 clone 不应把“旋转”做成无确认的即时 CSS transform，也不应把它误作撤销/重做按钮。

本轮对当前登录态共享画布只做了一次入口观察：点击 `image-toolbar-rotate` 后，画布新增并选中了一个 `i-EnxA3zCn8U` 节点，标签为 `旋转与镜像`；随后发送一次 `Meta+Z`，该节点从 DOM 和可见 graph 中消失。由于这条路径已经证明入口具备 graph mutation 能力，本轮没有继续寻找旋转面板、改变角度/镜像或触发 dirty modal。该 live 结果优先于“入口必然只进入 local editor”的安全假设，后续必须在可丢弃副本或获准测试节点上重新确认。

### 3.5 下载

bundle 的下载 callback 会：

1. 检查图片 URL 和下载忙状态；
2. 读取用户水印偏好；
3. 根据会员和水印选择原图或请求水印 URL；
4. 触发带格式化文件名的浏览器下载；
5. 上报 canvas output success；
6. 在缺少水印设置或失败时显示独立反馈。

这不是一个纯 `<a download>` 合同。prototype 可以使用本地下载降级，但必须标为 clone-only，不能声称复制了源站水印/权限流程。

### 3.6 预览 live 状态

点击 `图片4` 的预览后：

| 元素 | Rect / 值 |
|---|---|
| overlay | `0,0,929,874`，`fixed inset-0`、`bg-black/80`、toast z-layer |
| content container | `69.67,87.40,789.65,699.20`，`max-h-[90vh] max-w-[85vw]` |
| 当前图片 | `69.67,239.59,789.65,394.82`，保持 `2:1` |
| 水印 | `79.67,249.59,48,23.31` |
| close button | `839.32,75.40,32,32` |

静态渲染使用当前 output/history 数组，存在多个输出时才提供上一张/下一张；`showWatermark=true`。现场当前节点只有一张可预览图片，所以没有翻页按钮。

源站 close button 当前没有 role=dialog、test id、aria-label 或 title。这是源站可访问性缺口，不应成为 clone 必须照抄的缺陷；clone 的可见几何可复刻，但关闭按钮应保留可访问名称。

## 4. 当前 clone 差异

当前 [`ImageToolbar.tsx`](../../../src/components/ImageToolbar.tsx#L16) 只有 7 个文字动作和 `撤销 / 重做`，[`ImageNode.tsx`](../../../src/components/nodes/ImageNode.tsx#L34) 将除 `人像质感调节 / 全景` 外的动作统一映射为 `addDerivedNode`。源码搜索没有找到图片 preview、annotation、interactive element edit 或 layer composition 状态。

| clone 缺口 | 源站影响 | 建议优先级 |
|---|---|---|
| 没有 `editingImageTool` 状态 | 无法表达 toolbar 替换、panel 隐藏、节点内 canvas | P0 状态合同 |
| 没有 page-level image preview | 当前源站最安全、最独立的完整动作缺失 | P0 小实现候选 |
| 末端按钮为撤销/重做 | 与源站标注/旋转/下载/预览语义冲突 | P0 内容修正 |
| 旧动作统一即时派生节点 | 把 authoring、submit、result 三阶段压成一次点击 | P0 行为纠偏 |
| 没有元素编辑草稿模型 | point/box/brush records 与 task submit 无法区分 | P1/P2 |
| 没有 layer composition 状态机 | 无法表达 splitting/ready/redrawing/merging | P2，成本高 |
| 下载只有其他媒体的简单本地降级 | 缺水印、会员、失败反馈合同 | P1，需明确 prototype 边界 |

## 5. 待授权实施顺序

1. 先更新标准工具条的当前动作集合和 content-sized width，但对未实现动作提供明确的本地 prototype 边界。
2. 增加 `preview`：它独立、只读、证据完整，且不需要 graph mutation。
3. 建立 `editingImageTool` UI 状态和通用退出合同，再实现空标注态；没有保存语义前不伪造新图片。
4. 旋转先完成本地草稿、dirty、保存/丢弃合同，再决定更新当前节点还是创建输出。
5. 元素编辑按 records -> validate -> submit -> output node 分阶段设计，不能复用旧 `addDerivedNode` 快捷路径。
6. 图层分离最后实施；它依赖任务、layer composition、重绘/合并和图层级操作，不适合作为纯视觉按钮补丁。

以上仍是待授权队列。当前用户只允许修改文档，因此本轮没有触碰 `src/`。

## 6. 后续取证

| 优先级 | 项目 | 安全前提 |
|---|---|---|
| P0 | 元素编辑实际 active toolbar/panel 几何 | 已在共享画布完成空态进入/退出；后续只补非空 record，不提交 |
| P0 | 旋转无修改进入/退出与 dirty modal | 入口已证明可能先创建派生节点；必须使用可丢弃副本或明确授权，不能继续在当前画布试探 |
| P1 | 多输出图片的 preview prev/next | 找到已有 history 的节点，不创建结果 |
| P1 | 标注绘制后 dirty/escape 是否确认 | 使用可丢弃副本，禁止保存 |
| P2 | 图层分离 live 状态 | 需要测试节点、任务和积分授权 |
| P2 | 下载水印分支 | 需要允许读取偏好并产生本地文件 |
