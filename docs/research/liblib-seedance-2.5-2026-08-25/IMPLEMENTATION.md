# Seedance 2.5 实施结果

> 实施日期：2026-08-25
> 范围：只复刻 LibTV 已有能力的前端呈现，不实现真实模型、上传、计费或持久化后端。

## 1. 完成内容

### 图片节点

- 按源站观察实现空白、仅提示词、带参考图/工具结果三种编辑面板高度：`191px`、`211px`、`274px`。
- 面板内容改为节点数据驱动，使用各节点自己的提示词、参考图和生成设置。
- `智能引用 AutoLink` 改为“建议 → 用户确认 → 写入 token 与参考图”的闭环，不直接覆盖用户输入。
- 人像质感调节有选中状态和局部视觉增强。
- 全景、多角度、打光、九宫格、高清、宫格切分会创建连接到源图片的派生图片节点。

### Seedance 2.5 视频

- 就绪视频节点使用真实本地海报、播放态、时长和清晰度。
- 顶部工具条包含源站高价值视频处理命令。
- 下方生成面板复刻模型菜单、模式菜单、普通/超长参数、音频、数量、高级设置和 AutoLink 视觉。
- 超长视频范围为 `30-300s`，`300s` 显示 `14700` 本地预计积分。
- Batch 33 将原先面板内四阶段只读预览替换为画布级 pending 过程图。
- 长视频提交以一次 transaction 创建素材、镜头、两批候选、汇聚和最终成片
  共 12 个节点、22 条边，并保留 source selection 与 atomic undo/redo。
- 片段重拍支持最多五个预切 range、Prompt 投影和本地提交状态。
- 智能续写使用独立 `4-30s` 连续 selector；确认后创建连接的 empty video target，由目标节点承载续写 Prompt 和退出模式事务。
- 逐帧拉片由就绪视频工具条创建独立的 `shot-breakdown` 节点。

### 专用节点

- `shot-breakdown`：视频素材、拆解维度和本地完成命令；Batch 24 将结果改为持久画布节点。
- `shot-breakdown-result`：三个分镜组、一个动态组和一个音乐节点，作为单事务派生产物。
- `video-clip`：Batch 25 对齐为未连接视频空态、单列四模式和独立节点下方 Prompt panel。

## 2. 关键工程修复

React Flow 的 `onNodesChange` 原先使用 render 闭包里的旧 `nodes` 快照。派生节点按钮点击后，React Flow 紧接着发出的 selection/change 事件会用旧数组覆盖刚追加的节点，表现为“按钮无效”。现在统一从 `useCanvasStore.getState().getActiveCanvas()?.nodes` 读取当前快照；节点拖拽同步也使用同一策略。

视频时间范围改用 `onInput` 驱动状态，避免拖动/键盘修改滑块时 UI 和成本显示滞后。

## 3. 验证记录

### 已完成的浏览器实测

- 桌面 `1440x900`：图片上下浮层几何、图片三态、AutoLink 确认、派生图片节点与连线。
- 桌面：视频生成面板双浮层几何。
- Seedance 2.5 模型菜单和模式菜单。
- 普通参数和超长参数。
- `300s / 14700`。
- 超长视频画布过程图、请求 metadata、重复批次避让和 atomic history。
- 片段重拍五段上限、Prompt 投影和提交状态。
- 逐帧拉片创建、选择画布视频、维度过滤、持久结果组和单次 undo/redo。

已保存的主要证据：

- `docs/design-references/liblib-clone-image-overlays-aligned-2026-08-25.png`
- `docs/design-references/liblib-clone-image-autolink-2026-08-25.png`
- `docs/design-references/liblib-clone-seedance-video-selected-2026-08-25.png`
- `docs/design-references/liblib-clone-seedance-long-video-process-2026-08-25.png`
- `docs/design-references/liblib-clone-batch33-long-video-contact-sheet-2026-08-26.png`
- `docs/design-references/liblib-clone-seedance-segment-reshoot-2026-08-25.png`
- `docs/design-references/liblib-clone-seedance-shot-breakdown-complete-2026-08-25.png`
- `docs/design-references/liblib-clone-batch24-shot-breakdown-contact-sheet-2026-08-25.png`
- `docs/design-references/liblib-clone-batch25-video-clip-contact-sheet-2026-08-25.png`
- `docs/design-references/liblib-clone-batch26-continuation-contact-sheet-2026-08-25.png`

### 移动端边界

图片、片段重拍、智能剪辑和智能续写均已有 `390px` Playwright 实测。固定屏幕宽度的节点浮层保持节点锚定并自然被视口裁切，document 不产生横向 overflow；它们不会强行重排为移动端卡片。

### Batch 9 浮层锚定加固

后续 Batch 9 复核了原站失败视频与生成面板的精确矩形，并补齐自动化：

- image/video panel 中心与节点中心误差 `0px`；
- `660x274` 屏幕尺寸在约 `28%` / `38%` zoom 下保持；
- panel gap 校准为 `16 * zoom`；
- parented video 的 child drag、parent move/reselect、pan、zoom 和多选生命周期通过；
- 详细记录见 `docs/research/liblib-canvas-batch9-2026-08-25/`。

## 4. 未完成与刻意不做

- 没有真实 Seedance、图片生成、片段重拍、逐帧拉片或智能剪辑后端。
- 没有实现上传后的真实媒体元数据解析。
- 结果卡、时间片和生成过程都是本地 mock。
- 没有把图片 AutoLink、视频 AutoLink 和画布历史持久化到服务端。
- 没有继续处理本轮之外的 Batch3 差异。

## 5. 文件索引

- Store 与页面：`src/store/canvasStore.ts`, `src/app/page.tsx`
- 图片：`src/components/nodes/ImageNode.tsx`, `src/components/ImageToolbar.tsx`, `src/components/ImageEditPanel.tsx`
- 视频：`src/components/nodes/VideoNode.tsx`, `src/components/VideoProcessingToolbar.tsx`, `src/components/VideoGenerationPanel.tsx`, `src/components/SegmentReshootPanel.tsx`, `src/components/VideoContinuationSelector.tsx`
- 专用节点：`src/components/nodes/ShotBreakdownNode.tsx`, `src/components/nodes/ShotBreakdownResultNode.tsx`, `src/components/nodes/VideoClipNode.tsx`, `src/components/VideoClipEditPanel.tsx`
- 对应组件规格：`docs/research/components/`
