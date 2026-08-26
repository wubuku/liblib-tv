# Batch 56 截图识别台账

> 状态：已完成（2026-08-26）。
> 规则：本文件是 Batch 56 的唯一截图识别入口。后续回答本批截图内容前先
> 阅读本文；除非截图、viewport、代码状态或研究问题变化，否则不重复视觉识别。

## 1. 预期截图

| 文件 | 来源 | viewport | 状态 |
|---|---|---:|---|
| `liblib-clone-batch56-image-rotate-derived-desktop-929-2026-08-26.png` | clone | `929x874` | 旋转点击后派生节点被选中 |
| `liblib-clone-batch56-image-rotate-derived-mobile-390-2026-08-26.png` | clone | `390x844` | 旋转点击后派生节点与边的窄屏状态 |

截图由 Batch 56 verifier 在派生节点创建后、undo 前采集；这是“新节点被选中”
状态，而不是 redo 后 selection 被现有 history 合同清空的状态。

## 2. 首次识别结果

识别日期：2026-08-27。来源：本地 LibTV clone；截图由当前 Batch 56
verifier 生成；desktop/mobile 均为 `deviceScaleFactor=1`，画布已先执行
`Alt+Shift+f` 整理，随后选中 `图片4` 点击 `旋转`。

### Desktop `929x874`

- 画布保持深色 React Flow 工作区，顶部仍是画布导航，底部保留整理确认卡和
  工具栏；没有 page-level 旋转弹窗。
- source `图片4` 与右侧新建的 `旋转与镜像` 图片节点同时可见，中间有一条
  source -> derived 连线。
- `旋转与镜像` 节点带青色 selected border；其节点上方出现标准图片 toolbar，
  下方出现 generation panel，说明 selection 已移动到派生节点。
- 派生节点中的 media 仍是本地 prototype 图片；截图没有角度值、镜像按钮或
  “真实处理完成”结果状态。
- 由于画布是 `28%` 左右的组织视图，节点和浮层在整页中相对紧凑；这是当前
  clone 的 viewport 状态，不应把截图尺寸误读为 world geometry。

### Mobile `390x844`

- 画布 graph 在窄屏中保持自然缩小，source、derived node 和连线仍可见；
  页面没有横向滚动。
- 顶部导航和底部工具栏按既有 mobile shell 布局收缩；派生节点继续位于
  source 右侧，而不是被搬到页面中心。
- selected 派生节点的 source-shaped toolbar 可能自然裁切于窄视口边缘，符合
  当前节点中心 anchor / fixed content width 合同；没有新增 mobile clamp。
- 截图只证明本地 prototype 的可见层级和选中态，不证明源站最终旋转 bitmap。

## 3. 待记录的识图问题

后续只有在截图、viewport、代码状态或研究问题变化时，才追加最小识别：

- 是否需要单独记录“旋转点击后”与“redo 后 selection 清空”两种状态；
- 派生节点的真实 source image result 是否能在获准 fixture 中确认；
- source toolbar 与 derived toolbar 的 exact source CSS 是否发生漂移。

## 3. 证据分层模板

| 类型 | 记录规则 |
|---|---|
| Clone screenshot fact | 只记录截图直接可见的节点、边、浮层、文字、裁切和层级 |
| DOM-backed clone fact | 引用 verifier/runtime audit 的 rect、属性和状态 |
| Source-backed contract | 仅引用 `SOURCE_EVIDENCE.md` 及其上游文档 |
| Clone-only decision | 明确标记复用 source URL、固定命名和本地 prototype 反馈 |
| 未确认 | 不从截图推断 angle/flip、真实 bitmap、保存或 provider 行为 |

## 4. 当前可复用截图证据

不要重新识别 Batch 52、53 或 54 的 PNG；相关结论分别见：

- [`../liblib-canvas-batch52-2026-08-26/IMPLEMENTATION.md`](../liblib-canvas-batch52-2026-08-26/IMPLEMENTATION.md)
- [`../liblib-canvas-batch53-2026-08-26/SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch53-2026-08-26/SCREENSHOT_ANALYSIS.md)
- [`../liblib-canvas-batch54-2026-08-26/SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch54-2026-08-26/SCREENSHOT_ANALYSIS.md)
