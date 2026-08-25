# Batch 25 Screenshot Analysis

> 识图日期：2026-08-25  
> 用途：固化智能剪辑空态与下方 Prompt editor 的层级；后续不重复打开原图。

## 1. Source screenshot

### 文件

- 路径：`docs/design-references/liblib-original-seedance-video-edit-node-2026-08-25.png`
- 来源：LibTV 登录态画布
- viewport：`929x874`
- zoom 文案：`28%`
- 交互状态：`video-clip` 节点单选，Prompt editor 可见
- 整图识图次数：1
- 临时最小 crop：原图 panel 区域，未入库，识图次数：1
- 临时最小 crop：原图 node 区域放大，未入库，识图次数：1

### Source screenshot fact：节点

- 节点位于画布中部，screen box 约 `99x99`。
- 外部标题为 `智能剪辑 1`。
- 节点内部顶部/中部有剪刀图标。
- 主空态文案为 `空空如也，请连接视频节点后操作`。
- 下方有 `尝试：` 和四个模式命令。
- 四个模式是单列列表，不是 2x2 segmented grid；每行左侧有小图标。
- 节点内部没有大 textarea、参考 row 或 footer。

### Source screenshot fact：下方 panel

- panel 是独立深灰圆角 surface，位于节点正下方。
- 左上是 `+参考` pill。
- 右上是 expand command。
- 主体 placeholder：`描述想剪成什么效果`。
- footer 左侧：
  - 剪刀图标；
  - `默认模式` 和 chevron；
  - output glyph；
  - `16:9 · 720P · 30s` 和 chevron。
- footer 右侧为浅灰圆形发送按钮；live DOM 记录其 disabled。
- panel 没有标题栏、tabs 或额外 top command row。

### Geometry

live JSON：

- node：`x=463.803, y=436.152, w=98.979, h=98.979`
- inferred zoom：`98.979 / 350 = 0.282798`
- node center：`x≈513.293`

截图反推：

- panel：约 `x≈183, y≈540, w≈660, h≈191`
- panel center：`x≈513`
- node-to-panel gap：约 `4.5px`
- `16 * 0.282798 = 4.525px`

panel 数值是像素估计；节点 rect 是 live DOM fact。

## 2. Current clone code gap

- `VideoClipNode` 内部有 clone-only `智能剪辑 Beta` header。
- 四模式使用 2x2 active grid。
- 参考 row、textarea 和 footer 都在节点内部。
- 没有 `空空如也，请连接视频节点后操作`。
- 没有独立、反缩放、节点锚定的下方 panel。
- 节点选中和 multi-selection 不控制独立 editor 生命周期。

## 3. Re-inspection rule

除非需要确认 connected-video 状态、mode command 的真实副作用、精确 SVG 或 panel computed style，不再打开原始整图。实现几何优先使用本文、`live-audit.json` 和 Batch 9 已验证的 floating-anchor 合同。

本批 clone 截图完成后在本文追加一次性 contact sheet 结论。
