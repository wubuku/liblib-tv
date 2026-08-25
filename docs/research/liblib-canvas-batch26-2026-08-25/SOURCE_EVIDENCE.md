# Batch 26 Source Evidence

> 采样日期：2026-08-25  
> 原站：`https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd`

## 1. 证据方法

本批先读取既有截图台账，没有重复识别整张截图。新的高置信信息来自当前画布 HTML 引用的公开线上 JavaScript bundle：

- `0_o2gxip5splz.js`：当前中文文案；
- `15epcn_e-6pl6.js`：视频节点、智能续写入口与选择器；
- `26cwwn3id9r7t.js`：续写 range、extension 和 graph helper。

源站 HTML 在采样时列出 108 个 current chunk URL。这里仅记录与续写直接相关的结构化结论，不保存整份压缩代码，也不把 minified 变量名当成稳定 API。

## 2. Source Fact：入口与阶段

- 点击 `智能续写` 会先检查 Seedance 2.5 的可用初始配置。
- 入口会请求把源节点聚焦到 `zoom:1`，动画时长为 `300ms`。
- 然后打开视频时间线 session，并提示 `请截取续写前置视频`。
- 选择器不是 `SegmentReshootPanel`，也不包含重拍 Prompt editor。
- `Escape` 或左侧关闭按钮取消选择阶段。
- `确认续写` 成功后关闭选择器。

当前文案还明确声明：

```text
智能续写仅支持 Seedance 2.5 的全能参考模式
```

## 3. Source Fact：range 合同

线上 helper 的常量和校验为：

| 项目 | 值 |
|---|---:|
| 最短前置视频 | `4s` |
| 最长前置视频 | `30s` |
| 源视频最低时长 | `4s` |
| 初始起点 | `0s` |
| 初始终点 | `min(sourceDuration, 30s)` |

合法范围还要求：

- `startSec >= 0`；
- `endSec > startSec`；
- `endSec <= sourceDuration`；
- 选中时长在 `4-30s`。

选择器支持三种直接操纵：

- 拖动左手柄调整起点；
- 拖动右手柄调整终点；
- 拖动选中区域整体平移，并保持时长不变。

拖动超限时显示：

- `所选视频最短不小于 4 秒`
- `所选视频最长不大于 30 秒`

## 4. Source Fact：选择器几何与层级

线上组件公开的布局合同：

```text
wrapper
  absolute
  left: 50%
  top: 100%
  translateX(-50%)
  marginTop: 8
  z-index: 20

surface
  width: 660px
  flex row
  gap: 8px
  padding: 4px
  rounded: 12px
  backdrop blur + shadow

children
  close: 32x32
  timeline: flex-1, 48px high
  start/end handles: 16px wide
  selected duration: centered tooltip-style chip
  confirm: 32px high, horizontal padding 12px
```

续写 timeline 使用 cyan 主色的左右手柄、上下 `2px` outline 和 `12px` 圆角；时长显示保留两位小数，例如 `30.00 秒`。

## 5. Source Fact：确认后的画布拓扑

确认合法 range 后，原站创建：

- 一个新的 `video` 节点；
- 一条从源视频到目标视频的 edge；
- 新节点名称 `续写 {nodeLabel}`；
- 新节点位置为源节点右侧最近可用位置；
- Seedance 2.5 初始模型；
- 全能参考初始模式；
- 数量 `1`；
- 空的用户 Prompt suffix；
- 包含 source node、edge 和 range 的 `video-continuation` extension。

extension 的 graph helper 还明确规定：“退出续写模式”只清除该 extension 和它声明的 source-to-target edge，不删除目标节点。

## 6. Source Fact 与实现推断的边界

### Source fact

- 选择器的 DOM 层级、Tailwind class、宽高、间距、手柄宽度和拖动算法来自当前线上 bundle。
- `4-30s`、初始 `0-min(duration,30)` 和 graph extension 语义来自当前线上 helper。
- 续写节点名、Prompt placeholder、visible prefix 和 clear label 来自当前线上文案。

### Inference

- bundle 中的 presentation container 与项目 clone 的 React Flow 浮层实现不同；clone 将沿用已验证的 node-relative inverse-scale 技术。
- 目标节点的空媒体视觉由 source `pending` 分支和现有 clone 节点体系共同推断。
- bundle 暴露 visible prefix 文案，但本批没有通过登录态 DOM 测量它在 Prompt editor 内的精确像素位置。

### Clone-only decision

- 时间线缩略帧使用仓库已有静态图片循环，不从视频提取。
- 确认后创建本地空视频生成节点，不裁剪/上传 range。
- Prompt submit 只显示本地状态。
- 退出续写模式作为单次本地 graph transaction 实现。

## 7. 当前 Clone 审计

| 项目 | 当前 clone | 当前原站证据 |
|---|---|---|
| 组件 | 与重拍共用 `SegmentReshootPanel` | 独立 continuation selector |
| 进入状态 | 立即出现完整 Prompt editor | 先截取前置视频 |
| 默认 range | `24-28s` | `0-min(duration,30)` |
| range 语义 | 单个预切 4 秒 tile | 连续 `4-30s` 可拖选区 |
| 几何 | `660x316`，node gap `16 * zoom` | `660x56`，node margin `8` |
| 确认行为 | 同一源节点本地 submit | 创建右侧视频节点和 edge |
| Prompt | 源节点内部 | 新续写节点的生成器 |
| clear | 不存在 | 保留目标节点，清 extension/edge |

结论：当前实现不是“近似续写”，而是复用了错误的交互模型，应该拆分。
