# Batch 13：分镜模式数据绑定与故事板结构

> 日期：2026-08-25
> 范围：LibTV clone 的分镜模式主体，不改变工作台 React Flow 图。
> 目标：将分镜模式从固定示例改为当前画布驱动的“关键元素 + 故事板图片/视频 + Agent”三栏原型。

## 为什么做这一批

Batch 11 已经验证工作台/分镜切换和 Agent 生命周期，但当前 `StoryboardBoard` 仍然是固定数组：

- 新增、删除或切换画布后，分镜模式仍显示同一组示例卡片；
- 卡片不能反映当前画布的节点选择；
- 原站分镜截图中的左侧“关键元素”栏缺失；
- 原站中间故事板按“图片 / 视频”组织，clone 却把脚本、角色、分镜和视频混成四列。

这会让模式切换只改变画面，不保留画布上下文，是当前剩余高价值的交互缺口。

## 证据入口

- 原站登录态总体审计：[`../liblib-live-2026-08-25/README.md`](../liblib-live-2026-08-25/README.md)
- 一次性原站截图识图：[`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
- Batch 11 overlay 与模式生命周期：[`../liblib-canvas-batch11-2026-08-25/`](../liblib-canvas-batch11-2026-08-25/)
- 当前画布节点与媒体数据：[`../liblib-live-2026-08-25/full-canvas-audit.json`](../liblib-live-2026-08-25/full-canvas-audit.json)

## 本批边界

- 复刻分镜模式的空间组织和当前节点投影，不实现真实故事板编辑、拖拽排序或远端任务。
- 卡片点击只做本地节点选择；“回到工作台”是用于原型验证的显式命令。
- Agent 继续由 `uiStore.isAgentOpen` 管理，不把 FrameOS 状态混入 LibTV。
- 不重新识别原站工作台、图片编辑器或 Seedance 面板截图。

## 导航

- [`PLAN.md`](PLAN.md)：缺口、价值排序、实施和验收
- [`STORYBOARD_MODE.spec.md`](STORYBOARD_MODE.spec.md)：组件合同
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：原站截图一次性识图结果
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证和已知差异

