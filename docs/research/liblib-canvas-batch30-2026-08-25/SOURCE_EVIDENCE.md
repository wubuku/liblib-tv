# Batch 30 Source Evidence

> 采样日期：2026-08-25  
> 页面：`https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd`

## 1. Evidence Boundary

本批优先复用 Batch 29 已下载的当前页面 108 个 chunk，避免重复截图识别。
核心文件：

| File | SHA-256 | Role |
|---|---|---|
| `2jbcm5mok_bay.js` | `4380cf7e54d07a899f801718fa369331f3c43d5418c386ff37947ed54f3274d8` | toolbar/menu renderer |
| `15epcn_e-6pl6.js` | `3c976a417d35ead78e44a985f3d6d47cf1f9c5c6ae3c31221d82c5ebe70cef00` | video orchestration, editors, requests |
| `0_o2gxip5splz.js` | `19ae080ffa0c23788cc3a6543cf835d34d50da331ab739fdafd558f994bb441e` | Chinese i18n strings |
| `2ga3c1quu6wbd.js` | `db3e79339f495a2edecfcb1dd7da8c480c20b2b7074146e11fefaa75de0d0996` | supporting runtime |

登录态 source screenshot 若本批没有新增，不得用 clone screenshot 补写为原站
视觉事实。专项 screenshot 只验证 clone 实施结果。

## 2. Toolbar And Menu

`VideoNodeToolbar` 的工具组顺序：

```text
音视频分离 -> 主体编辑组 -> 帧截取组 -> download divider
```

主体编辑组数据：

```javascript
[
  "subjectRemove",
  "subjectModify",
  "subjectReplace",
  "matting",
]
```

对应中文：

```text
主体消除
主体修改
主体替换
智能抠像
```

通用 dropdown trigger 直接显示第一项 label，因此该组 trigger 是
`主体消除`，不是当前 clone 的 `画面编辑`。

通用 menu interaction 和 geometry：

- `trigger: hover`；
- `openDelay: 100`；
- `closeDelay: 120`；
- `position: bottom`；
- `offset: 8`；
- dropdown `minWidth: 160px`；
- dropdown radius `12px`、padding `6px`；
- item radius `8px`、font size `13px`、padding `8px 10px`。

## 3. Subject Editing Background

三项 action 通过同一个全局 `usePictureEditStore` 打开编辑器：

```text
onPictureEditClick(action)
  -> validate source
  -> pictureEditStore.open(action, sourceNodeId)
```

store 已确认：

- mode：`subjectRemove | subjectModify | subjectReplace`；
- mark limit：remove `4`、modify `4`、replace `2`；
- active tools：`point | box | brush | eraser`；
- mark 持有 frame time、识别候选、描述和 replace image；
- modify 要求每个有效 mark 填写描述；
- replace 要求每个有效 mark 上传替换图；
- replace image 入口为 `本地上传 / 历史图库`。

已确认中文：

```text
点选 / 框选 / 画笔 / 橡皮
重置 / 确定 / 提交 / 分析中
描述想要如何更改画面
最多标记 {count} 处
```

prompt 语义：

```text
remove:  移除{subject}，移除后背景自然融合
modify:  将{subject}修改为：{desc}
replace: 将{subject}替换为{target}
```

这些是下一批标注编辑器的 source-backed 背景，不是 Batch 30 已实现范围。

## 4. Source Validation

`validatePictureEditSourceVideo`：

- 格式仅支持 MP4 / MOV；
- duration `<2.5s` 不支持，提示展示约 `3~15s`；
- duration `>15s` 使用 `视频大于15秒，暂不支持该功能`；
- 单边分辨率范围 `700..4553px`；
- 像素面积不超过 `8294400`，即 4K；
- 最大宽高比 `2.5`。

当前 clone 的 Add Node ready-video 固定为 `30s`，且旧批次依赖 `00:30`。
因此本批不修改 fixture，而是让三项 subject action 命中源站真实的 `>15s`
限制。这样既不破坏旧测试，也不以无行为菜单冒充已完成编辑器。

## 5. Smart Matting Panel

`SmartMattingGenerator` 是 node 下方独立 panel：

- presentation：`NodeToolbar`；
- anchor：节点下方 `16px`；
- width：`min(560, max(360, round(nodeWidth)))`；
- 当前 clone `512px` video 对应 `512px` panel；
- shell：rounded `12px`、padding `8px`、水平 `justify-between`；
- 左侧：`32px` close、`智能抠像` label；
- 右侧：power cost display、`32px` generate icon button；
- power calculation 中 generate disabled；
- submitting 时 generate icon 替换 spinner。

该 panel 没有本批早期推测的 resolution selector。质量 setting helper 属于主体
编辑生成请求，不应错误加入智能抠像 panel。

## 6. Smart Matting Request And Graph

`buildMattingRequest`：

```text
provider: volcano
taskType: video
model: volcano-portrait-matting
format: WEBM
params.prompt: ""
params.videoList: [sourceUrl]
params.extendInfo.videoListV2:
  [{ url, width?, height?, duration? }]
metadata.node_id: pre-generated outputNodeId
```

点击 generate 后：

1. 以 source 右侧最近位置创建 VIDEO output；
2. name 为 `${sourceName}-智能抠像`；
3. `action = VIDEO_GENERATE`；
4. `generatorType = PICTURE_EDIT`；
5. `isSmartMattingOutput = true`；
6. 创建 direct edge `source video -> output video`；
7. 提交 generation task；
8. success 时把 task ID 写回 output。

本项目没有 backend，因此只复刻 panel、request-shaped metadata、pending output、
direct edge 和 atomic history，不伪造真实 task ID 或透明视频结果。

## 7. Source Fact / Inference / Clone Decision

### Source fact

- trigger 是 `主体消除`，menu 为四项且顺序固定。
- generic dropdown 为 hover 触发，时序 `100ms / 120ms`。
- 三项主体编辑共享 store/editor，并先进行 source validation。
- 30 秒 source 会提示 `视频大于15秒，暂不支持该功能`。
- 智能抠像使用 node-bottom compact panel，不直接从 menu 创建 output。
- generate 创建 `PICTURE_EDIT` pending VIDEO 和 direct source edge。
- output name、request provider/model/task type/format 已由 bundle 确认。

### Inference

- clone 继续使用 `512x288` VideoNode 作为 matting output。
- clone 使用 source right `+100` world units 和现有 slot resolver 表达
  `findClosestRightFlowPosition`；原站碰撞算法未完整移植。
- source selection 在创建 output 后保留；源码没有 output-selection 调用，
  panel 关闭并保留 source context。

### Clone-only decision

- power display 固定为未计算态 `--`，避免编造积分价格。
- generate 使用短本地 timer 暴露 submitting spinner，随后创建 pending graph。
- pending output 不显示伪造透明媒体，只显示等待媒体资源状态。
- prototype 仅保存 request-shaped metadata 到 Zustand 内存。

