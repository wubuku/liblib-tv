# Batch 150 — /project 画布卡新开标签 + 添加面板容器视觉（源站 2026-09-07）

## 概要

依据 Batch 149 复采的两项源站事实完成对齐：

1. **/project 画布卡点击在新标签页打开画布**。源站点击项目卡（封面为真实
   `<img>` object-cover）后新开 `/canvas?spaceId=…&projectId=…` 标签，列表页
   原地不动。clone `openCanvas` 由 `router.push` 改为 `window.open("/", "_blank")`；
   「开始创作」创建卡维持同页（源站新建流未采样，不作断言）。
2. **添加节点面板容器**对齐源站容器类：`rounded-2xl`（16px）+
   `backdrop-blur-[32px]` + hairline 边框（`border-white/[0.08]`）+
   半透明底（`bg-[#262626]/85`）。源站 39px 窄栏是背景窗口动画冻结中间态
   （见 Batch 149 勘误），目标态容器宽度 196px 与 clone 一致。

## CLONE_DECISION

- 新标签页是全新 JS 上下文（Zustand store 不跨页），popup 显示默认活动画布；
  源站新标签恢复同一画布依赖服务端会话，clone 无后端，行为差异记录在案。
- batch119 弹窗断言改为「画布切换器就绪」（`data-canvas-trigger`），
  不再断言具体画布名。

## 验收

- `verify-liblib-batch150.py`：9 checks 通过（新标签页契约 + 容器圆角/毛玻璃 + 0 diagnostics）。
- 相邻回归绿：100 / 115 / 119 / 125 / 148。
- `npm run check`：0 errors、8 warnings（既有基线）。
