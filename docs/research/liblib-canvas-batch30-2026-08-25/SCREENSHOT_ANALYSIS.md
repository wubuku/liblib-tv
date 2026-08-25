# Batch 30 Screenshot Analysis

> 状态：已完成一次性 contact-sheet 识别。
> 识别日期：2026-08-25。
> 后续优先读取本文件，不重复打开整张 contact sheet。

## Assets

| Screenshot | Viewport | State |
|---|---:|---|
| `liblib-clone-batch30-picture-edit-menu-929-2026-08-25.png` | 929x874 | hover menu |
| `liblib-clone-batch30-duration-feedback-929-2026-08-25.png` | 929x874 | 30s guard |
| `liblib-clone-batch30-matting-panel-929-2026-08-25.png` | 929x874 | bottom panel |
| `liblib-clone-batch30-matting-graph-929-2026-08-25.png` | 929x874 | source -> outputs |
| `liblib-clone-batch30-matting-mobile-390-2026-08-25.png` | 390x844 | natural clipping |
| `liblib-clone-batch30-smart-matting-contact-sheet-2026-08-25.png` | composite | one-time recognition source |

## One-Time Visual Findings

### Picture-edit menu

- ready video 位于画布中央，cyan selection border 连续且未被 menu 切断。
- top toolbar 保持单行；viewport 左侧自然裁掉最前方少量 toolbar，右侧 command
  仍可见，没有换行或二次 toolbar。
- `主体消除` trigger 处于 active 深色背景，chevron 位于 label 右侧。
- menu 居中落在 trigger 下方，宽度明显大于 trigger，左右溢出均衡。
- 四项按消除、修改、替换、抠像垂直排列；icon、label 左对齐，行高一致。
- menu 覆盖 node 顶部区域但没有遮住 source toolbar trigger，也没有与 cyan
  node border 发生视觉错位。

### Duration feedback

- `视频大于15秒，暂不支持该功能` 是 node 内顶部居中的黑色 compact feedback。
- feedback 位于画面主体上方、toolbar 下方，没有压住 central play button。
- menu 已关闭，graph 没有新增 output 或 edge。

### Smart-matting panel

- source node 上方 toolbar 与下方 panel 同时出现，均以 node 中线为 anchor。
- bottom panel 左右边界与 `512px` source node 对齐，间距稳定且没有贴住 border。
- panel 高度紧凑，左侧 close + label，右侧 `--` power + generate button。
- 普通 `660px` VideoGenerationPanel 已卸载，因此没有双层 bottom panel。
- panel、node 和 top toolbar 的 z-order 清楚，没有互相遮挡。

### Repeated output graph

- fit-to-view 后 source 位于左列，两个 pending output 位于同一右列。
- 第一 output 与 source 同 Y；第二 output 在其下方，间距清楚，没有 node overlap。
- 两条 edge 都从 source 右侧出发，分别进入两个 output 左侧。
- output body 使用同一 pending icon/copy，不显示 source poster，避免冒充完成媒体。
- source cyan selection 保留；普通 generation panel 返回并位于 source 下方。
- 既有 `660px` generation panel 向右接近第二 output 列，但没有遮挡 output
  中央 icon/copy。该跨批 lower-editor 宽度风险不属于 matting panel 锚点错误。

### Mobile

- `390x844` 下 toolbar、source node 和 `512px` bottom panel 按画布坐标自然裁切。
- panel 与 node 仍保持相同横向 anchor；可见的 label 尾部、power 和 generate
  control 没有发生上下错位。
- bottom toolbar 保持在 viewport 内，document 没有横向滚动条。
- natural clipping 是当前 canvas contract，不是响应式压缩或换行。

## Geometry Backing

Playwright 数值断言：

- top toolbar：`1009x49px`；
- picture-edit menu：`160px`，trigger/menu center delta `0px`；
- trigger-to-menu gap：`7px`；
- smart-matting panel：`512x48px`；
- source-to-panel gap：`16px`；
- first output：source right `+100` world units、同 Y；
- second output：同列，垂直 slot `288 + 48` world units；
- desktop/mobile document overflow：false。

## Classification

### Direct screenshot facts

- menu、feedback、panel、pending outputs 和 mobile clipping 的上述可见关系。
- top/bottom floating UI 均与 source node 中心对齐。
- repeated outputs 没有互相覆盖。

### DOM-backed facts

- exact menu/panel dimensions、gaps、metadata、edge IDs、selection 和 history。
- hover `100ms / 120ms` 时序。

### Clone-only state

- power `--`、短 submitting spinner、pending resource body。
- screenshot 中的 cafe poster 是本地 fixture，不是抠像结果。

## Source Boundary

这些图片是 clone verification，不是原站视觉证据。原站事实来自
[`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md) 记录的当前线上 bundle。
