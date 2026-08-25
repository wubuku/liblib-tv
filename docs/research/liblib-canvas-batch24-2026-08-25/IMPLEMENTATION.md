# Batch 24 Implementation Log

> 状态：实现与专项验证已完成；跨批回归和完整工程门禁待最终阶段补录。

## 1. 实施内容

### 输入节点

- `ShotBreakdownNode` 保持 `320x389` world size。
- ready 素材 metadata 改为 `00:30 · 1280×720` section 右侧布局。
- 预览图不再覆盖 clone-only 源名称 pill。
- running 使用本地 `700ms` 过渡；该时长只为原型演示，不作为原站事实。
- complete 状态不再挂载节点下方浮层，也不再显示无证据的“重新拉片”。

### 结果节点

- 新增 `src/components/nodes/ShotBreakdownResultNode.tsx`。
- 新增结构化结果数据 `src/lib/shotBreakdownResults.ts`。
- 默认创建：
  - `storyboard-01`：`1040x680`，`S01-S03`
  - `storyboard-02`：`1040x680`，`S04-S06`
  - `storyboard-03`：`1040x350`，`S07-S08`
  - `motion`：`1040x680`，`M01-M03`
  - `music`：`324x220`，BGM
- 结果沿 source 右侧纵向排列，world gap 为 `48px`。
- 每张媒体卡保留一个本地“用作参考”命令；点击只改变当前组件的 active 反馈，不创建账户资产。

### Store 事务

- `canvasStore.completeShotBreakdown` 一次完成：
  - source `status=complete`
  - append filtered result nodes
  - append source-to-result edges
  - 写入 `resultNodeIds`
  - push 一次 history
- 已有结果时动作 idempotent。
- undo/redo 会整体移除/恢复 source 状态、结果节点和边。

### 删除旧模型

- 删除 `src/components/ShotBreakdownResultsPanel.tsx`。
- 删除 tabs、result check、`已选择 N 项`、`加入参考` 和 selected-only 生命周期。

## 2. 专项验证

`python3 scripts/verify-liblib-batch24.py` 已通过：

- 空画布创建 `shot-breakdown` 和 ready source；
- `320x389`、metadata、三个 active 维度；
- 默认五个结果节点、五条边、12 个结果项；
- `S01-S08`、`M01-M03`、BGM 波形与播放命令；
- deselect 后持久存在；
- 关闭 music 只创建四个结果节点；
- 单次 undo/redo；
- `929x874` 和 `390x844` 无 document overflow；
- console/page error 为空。

工程预检：

- `npm run typecheck`：通过。
- `npm run lint`：0 errors；保留 9 条既有 FrameOS warnings。

## 3. 截图

- `docs/design-references/liblib-clone-batch24-shot-breakdown-ready-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch24-shot-breakdown-results-overview-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch24-shot-breakdown-results-detail-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch24-shot-breakdown-mobile-390-2026-08-25.png`
- `docs/design-references/liblib-clone-batch24-shot-breakdown-contact-sheet-2026-08-25.png`

## 4. 剩余边界

- 没有真实媒体上传、逐帧分析、动态视频、BGM 提取、会员或积分服务。
- source output screenshot 没有 React Flow DOM，因此结果组 type、精确尺寸、edge 数量仍是 source-shaped inference。
- 本地结果图片来自仓库现有素材，不冒充文章中的原始媒体。
- 结果 action 的真实产品行为尚未采样。
