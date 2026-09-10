# Batch 334 — 故事板视图重建：全宽三栏资源总览（`IMPLEMENTED_VERIFIED`）

> 状态：clone 故事板模式按源站 2026-09-11 现版重建
> （`verify-liblib-batch334.py` 21 checks 全绿；旧验证器 11/13/104
> 迁移至新契约后全绿）。
>
> 证据：`evidence/source-storyboard-view.png`（源站故事板视图，
> 2026-09-11 会话截图）、`evidence/source-workbench-view.png`
> （工作流视图对照）、`runtime-audit.json`。

## 源站事实（`SOURCE_FACT`，2026-09-11）

- 工作流/故事板为顶栏图标对（aria-label `工作流`/`故事板`）切换的
  双视图；故事板视图是**全宽三栏资源总览**：音频（窄）| 图片（宽）
  | 视频（弹性和），三块圆角边框面板；
- 图片栏头部右侧为展开图标（↗）；栏体内子行含类型小标 +
  **对话**按钮；
- 图片卡片：缩略图 + 下方尺寸芯片（`1080 x 1446` 形式）；
- 视频栏头部：**全部 ∨** 过滤 + 展开图标；卡片：深色媒体区居中
  ▶ / 状态文案（`待确认后生成`），下方**模型芯片**（Wan 3.0 Prime）
  与输入引用缩略图（首帧图 + 音频）；
- batch 104 时代的「关键元素」侧栏、「返回工作台」按钮、
  「放大图片/视频」按钮在源站现版中**不存在**（视图切换由顶栏
  图标对承担）。

## Clone 变更

`StoryboardBoard.tsx` 重写：

- 三栏 `data-storyboard-column="audio|image|video"`，列序与源站
  一致，音频栏最窄、图片栏次之、视频栏弹性占满；
- 图片栏：类型子行 + `data-storyboard-dialog="image"`（对话），
  卡片 `data-storyboard-card` + `data-storyboard-dimension`
  （`width x height`）；
- 视频栏：`data-storyboard-filter="all"`（全部）、
  `data-storyboard-expand`（展开图标 ×2）、卡片
  `data-storyboard-video-status`（empty/failed/ready/pending →
  暂无预览/生成失败/播放圆钮/待确认后生成）+
  `data-storyboard-model` 模型芯片 + 引用缩略图；
- 音频栏：`data-storyboard-audio-duration` 时长标签；
  空态 `data-storyboard-empty`（暂无音频/暂无图片/暂无视频）；
- 移除关键元素侧栏、返回工作台、放大按钮（旧
  `data-storyboard-key-*`/`data-storyboard-return`/
  `data-storyboard-zoom` 契约废止）；
- 卡片点击保留 `selectNode` 联动（选中后切回工作流节点高亮）。

## 验证器迁移（源站现版证据导致旧契约失效）

- `verify-liblib-batch334.py`（新，21 checks）：列序/几何、控制
  面板、卡片状态与尺寸芯片、空态、双视图往返；
- batch 11/13/104：关键元素断言改为新三栏断言（文本列废止、
  返回按钮 → 顶栏工作流图标、空态增加 暂无音频）；均迁移后全绿；
- batch 14 的失败为**存量问题**（Agent 抽屉 data-agent-send，
  stash 前后基线同样失败，与本批无关），已单独记录待查。

## 验收

- `verify-liblib-batch334.py` 21 checks 全绿；
- 维护集 42 项全绿（batch 268 的 storyboard 为节点类型，无涉）；
- 迁移验证器 11/13/104 全绿；`npm run check` 0 errors；
  docs check 通过。

## 后续候选

- 视频卡「待确认后生成」确认/取消交互建模（BLOCKED_MANUAL）；
- 视频栏 全部 ∨ 过滤器的真实筛选行为采样；
- 源站恢复后补采 BLOCKED_SOURCE（Hailuo 分解、480P 批量、
  Style Video 费率）。
