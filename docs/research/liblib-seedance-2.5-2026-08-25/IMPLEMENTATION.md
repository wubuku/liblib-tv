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
- `查看过程` 显示四阶段本地生成过程图。
- 片段重拍/智能续写支持时间片选择、最多五段、Prompt 投影和本地提交状态。
- 逐帧拉片由就绪视频工具条创建独立的 `shot-breakdown` 节点。

### 专用节点

- `shot-breakdown`：视频素材、拆解维度、异步本地结果和分镜/动态/音乐结果卡。
- `video-clip`：智能剪辑 Beta 四模式、参考入口、Prompt 和发送禁用态。

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
- 超长视频过程图。
- 片段重拍五段上限、Prompt 投影和提交状态。
- 逐帧拉片创建、选择画布视频、异步完成和结果标签页。

已保存的主要证据：

- `docs/design-references/liblib-clone-image-overlays-aligned-2026-08-25.png`
- `docs/design-references/liblib-clone-image-autolink-2026-08-25.png`
- `docs/design-references/liblib-clone-seedance-video-selected-2026-08-25.png`
- `docs/design-references/liblib-clone-seedance-long-video-process-2026-08-25.png`
- `docs/design-references/liblib-clone-seedance-segment-reshoot-2026-08-25.png`
- `docs/design-references/liblib-clone-seedance-shot-breakdown-complete-2026-08-25.png`

### 移动端边界

本轮此前已保存 `390px` 图片选中态截图，证明图片工具条/编辑面板会随节点锚定并自然被视口裁切，而不是强行居中到屏幕。续接本轮时应用内浏览器连接不可用，因此没有把新的 Seedance 移动截图写成“实测”；移动端新增组件只通过源码断点、固定尺寸和既有 390px 截图做静态回归审查。

## 4. 未完成与刻意不做

- 没有真实 Seedance、图片生成、片段重拍、逐帧拉片或智能剪辑后端。
- 没有实现上传后的真实媒体元数据解析。
- 结果卡、时间片和生成过程都是本地 mock。
- 没有把图片 AutoLink、视频 AutoLink 和画布历史持久化到服务端。
- 没有继续处理本轮之外的 Batch3 差异。

## 5. 文件索引

- Store 与页面：`src/store/canvasStore.ts`, `src/app/page.tsx`
- 图片：`src/components/nodes/ImageNode.tsx`, `src/components/ImageToolbar.tsx`, `src/components/ImageEditPanel.tsx`
- 视频：`src/components/nodes/VideoNode.tsx`, `src/components/VideoProcessingToolbar.tsx`, `src/components/VideoGenerationPanel.tsx`, `src/components/SegmentReshootPanel.tsx`
- 专用节点：`src/components/nodes/ShotBreakdownNode.tsx`, `src/components/ShotBreakdownResultsPanel.tsx`, `src/components/nodes/VideoClipNode.tsx`
- 对应组件规格：`docs/research/components/`
