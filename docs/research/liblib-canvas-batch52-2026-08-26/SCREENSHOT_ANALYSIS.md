# Batch 52 截图识别台账

> 识别日期：2026-08-26
> 来源：本地 LibTV clone 运行态
> 目的：记录本批唯一一次视觉检查结果，避免后续为同一截图重复识图。

## 1. 识图范围

本批截图来自 `scripts/verify-liblib-batch52.py`，不是原站截图。源站事实
来自已归档的 DOM/bundle/live audit；本台账只解释 clone 是否把这些合同呈现
出来。所有截图均为 device scale factor `1`。

| 文件 | viewport | 状态 | 识图方式 |
|---|---:|---|---|
| [`liblib-clone-batch52-current-image-toolbar-929-2026-08-26.png`](../../design-references/liblib-clone-batch52-current-image-toolbar-929-2026-08-26.png) | `929x874` | 选中图片，标准双浮层 | 一次视觉检查 + DOM audit |
| [`liblib-clone-batch52-image-preview-929-2026-08-26.png`](../../design-references/liblib-clone-batch52-image-preview-929-2026-08-26.png) | `929x874` | page-level Preview 打开 | 一次视觉检查 + DOM audit |
| [`liblib-clone-batch52-image-preview-mobile-390-2026-08-26.png`](../../design-references/liblib-clone-batch52-image-preview-mobile-390-2026-08-26.png) | `390x844` | mobile Preview 打开 | 一次视觉检查 + DOM audit |

## 2. 桌面标准双浮层

直接可见：

- 深色画布上保留原有节点、边、左右上角导航和底部工具栏；
- 选中图片上方是一条横向深灰工具条，左侧在当前视口外自然裁切，
  中央到右侧可见 `打光 / 九宫格 / 高清 / 元素编辑 / 图层分离 / 宫格切分`
  和四个图标动作；
- 图片下方是节点内编辑面板，面板与工具条都以图片节点中心为水平基准；
- 没有额外的第三个节点浮层，Preview 尚未打开时页面结构保持标准双浮层。

DOM 事实：

```text
node      x=48, y=176.717, w=198.671, h=99.336
toolbar   x=-398.914, y=110.906, w=1092.500, h=49
panel     x=-182.664, y=280.594, w=660, h=191
zoom      0.283816
```

工具条 13 个按钮的 DOM 测量和 disabled 状态见
[`runtime-audit.json`](runtime-audit.json)。本图的 `x < 0` 不是 bug，而是
固定宽 source-shaped host 以节点中心为 anchor 后允许自然裁切的结果。

## 3. 桌面 Preview

直接可见：

- 整个 viewport 被近黑色遮罩覆盖，底层画布仍隐约可见；
- 2:1 咖啡馆图片位于 viewport 中央，保持原始宽高比，没有拉伸；
- `AI生成` 水印位于媒体左上方，不跟随 content viewport 的空白区域移动；
- 关闭按钮位于内容 viewport 右上外侧，按钮有清晰边界和焦点高亮；
- Preview 没有在节点旁增加 toolbar/panel，也没有改变底层 graph。

DOM 事实：

```text
overlay  0,0,929,874
content  69.672,87.406,789.641,699.188
media    69.672,239.594,789.641,394.813
watermark 79.672,249.594,48,23
close    839.313,75.406,32,32
```

## 4. 移动 Preview

直接可见：

- viewport 仍被遮罩覆盖，内容区按 `85vw x 80vh` 缩小；
- 2:1 图片保持 contain 并垂直居中；
- 关闭按钮仍位于 content 右上外侧；
- 底层固定宽图片工具条在遮罩下仍可见并自然裁切，但没有导致页面横向
  滚动条；
- 底部工具栏、整理确认卡和导航没有被 Preview 的媒体层重新布局。

DOM 事实：

```text
overlay  0,0,390,844
content  29.25,84.406,331.5,675.188
media    29.25,339.125,331.5,165.75
watermark 39.25,349.125,48,23
close    340.75,72.406,32,32
```

移动端“预览”按钮位于固定宽工具条的视口外侧，这是源站形态的自然裁切。
专项验证器没有把它误判为可物理点击的可见控件，而是先断言其屏幕位置，
再通过 DOM handler 验证 Preview 生命周期。

## 5. 证据边界

| 类型 | 本台账结论 |
|---|---|
| Clone screenshot fact | 三张图的层级、裁切、遮罩、媒体比例、按钮可见性和无明显重叠 |
| DOM-backed clone fact | 所有 rect、按钮宽度/顺序/disabled、focus、graph/selection 不变 |
| Source-backed contract | `1092.5x49`、13 项顺序、`10 + 24 * zoom`、Preview page-level、`85vw x 80vh` |
| Clone decision | 未完成高风险动作保持 disabled，不伪造 graph/task side effect |
| 未确认 | 源站完整 CSS、下载副作用、标注保存、元素编辑有效记录、真实任务服务 |

后续 agent 应优先读取本台账和 `runtime-audit.json`。若问题只是“本批截图
里有什么”，无需再次打开 PNG；只有要验证新的状态、不同 viewport 或发生
代码改动时，才截取最小的新区域并追加新记录。
