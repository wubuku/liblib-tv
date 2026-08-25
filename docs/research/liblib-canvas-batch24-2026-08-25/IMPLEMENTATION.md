# Batch 24 Implementation Log

> 状态：实现、专项验证、跨批回归和完整工程门禁均已完成。

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

## 3. 跨批回归与最终门禁

### Playwright

按顺序运行 `scripts/verify-liblib-batch9.py` 到 `scripts/verify-liblib-batch24.py`，16 个批次全部通过：

- Batch 9-12：节点浮层锚定、图片五态、overlay 生命周期、资产 tabs；
- Batch 13-17：分镜模式、Agent/share、添加节点、画布 CRUD、资产层级；
- Batch 18-20：缩放菜单、minimap、720° 全景派生节点；
- Batch 21-24：Seedance 参数、模型菜单、片段重拍、逐帧拉片。

### Engineering

- `npm run check`：通过。
  - ESLint：0 errors，9 条既有 FrameOS warnings；
  - TypeScript strict check：通过；
  - Next.js 16.2.1 production build：通过；
  - 路由：`/`、`/_not-found`、`/frameos`、`/frameos/canvas/[id]`。
- `npm run docs:check`：通过，186 个 Markdown，443 个本地目标。
- `git diff --check`：通过。

构建仍提示仓库上层存在另一个 `package-lock.json`，Next 自动推断 workspace root；该警告在本批前已存在，不影响构建产物。

## 4. 截图

- `docs/design-references/liblib-clone-batch24-shot-breakdown-ready-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch24-shot-breakdown-results-overview-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch24-shot-breakdown-results-detail-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch24-shot-breakdown-mobile-390-2026-08-25.png`
- `docs/design-references/liblib-clone-batch24-shot-breakdown-contact-sheet-2026-08-25.png`

## 5. Git 保护点

- `5a0648f`：Batch 24 原站证据、计划、识图台账和工作流规格。
- `3a15fd2`：持久结果节点实现、专项 Playwright、截图和实现台账。
- 最终回归结果随本文档提交并推送。

## 6. 剩余边界

- 没有真实媒体上传、逐帧分析、动态视频、BGM 提取、会员或积分服务。
- source output screenshot 没有 React Flow DOM，因此结果组 type、精确尺寸、edge 数量仍是 source-shaped inference。
- 本地结果图片来自仓库现有素材，不冒充文章中的原始媒体。
- 结果 action 的真实产品行为尚未采样。
